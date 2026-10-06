"""Tests for the seeded pricing data layer (``schema.py`` + ``scraper.py``).

The suite covers the four properties Phase B promises:

1. ``init_db`` creates exactly the four expected tables and is safe to re-run.
2. A seed run produces the expected row counts, and a second run over the same
   input changes nothing (idempotency — the core ingestion guarantee).
3. Foreign keys resolve: every ``pricing_history`` row joins to a real
   competitor and product, and the declared names map to the declared prices.
4. A run records exactly one ``pricing_snapshots`` row, keyed on the snapshot
   date, so "one row per run" survives a re-run on the same date. A run that
   declares a *later* ``data_as_of`` adds exactly one more row.
5. A later snapshot **closes** the prior price window: exactly one row per
   ``(competitor, product)`` keeps ``valid_to IS NULL``, and the earlier row's
   ``valid_to`` equals the new ``valid_from``.

All tests use a temporary database; the committed ``sample_data.json`` is the
seed source, so a change to that file is exercised here too.

Run: ``.venv/bin/python -m pytest tests/ -q``
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

import schema
import scraper

REPO_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_DATA = REPO_ROOT / "pricing-scraper" / "sample_data.json"

EXPECTED_COUNTS = {
    "competitors": 4,
    "products": 5,
    "pricing_history": 19,
    "pricing_snapshots": 1,
}


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    """A path to a database that does not exist yet."""
    return tmp_path / "market_data.db"


def table_counts(db_path: Path) -> dict[str, int]:
    """Return ``{table: row_count}`` for the four pipeline tables."""
    conn = sqlite3.connect(db_path)
    try:
        return {
            table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in EXPECTED_COUNTS
        }
    finally:
        conn.close()


def shifted_snapshot(directory: Path, snapshot_date: str) -> Path:
    """Write a seed file identical to ``SAMPLE_DATA`` but declaring a later date.

    Both the root ``data_as_of`` and every pricing row's ``date`` are advanced,
    which is what a genuine later scrape would produce: same vendors and SKUs,
    a new observation window.
    """
    payload = json.loads(SAMPLE_DATA.read_text(encoding="utf-8"))
    payload["data_as_of"] = snapshot_date
    for row in payload["pricing"]:
        row["date"] = snapshot_date

    path = directory / f"sample_data_{snapshot_date}.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


# ── schema.init_db ────────────────────────────────────────────────────────────


def test_init_db_creates_the_four_tables(db_path: Path) -> None:
    schema.init_db(db_path)

    conn = sqlite3.connect(db_path)
    try:
        names = {
            row[0]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
    finally:
        conn.close()

    assert set(EXPECTED_COUNTS) <= names


def test_init_db_creates_missing_parent_directory(tmp_path: Path) -> None:
    nested = tmp_path / "nested" / "data" / "market_data.db"
    schema.init_db(nested)
    assert nested.exists()


def test_init_db_is_idempotent(db_path: Path) -> None:
    schema.init_db(db_path)
    schema.init_db(db_path)  # must not raise on an existing database

    conn = sqlite3.connect(db_path)
    try:
        count = conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type = 'table'"
        ).fetchone()[0]
    finally:
        conn.close()

    assert count >= len(EXPECTED_COUNTS)


# ── scraper.seed_from_json ────────────────────────────────────────────────────


def test_clean_seed_produces_expected_counts(db_path: Path) -> None:
    summary = scraper.seed_from_json(db_path, SAMPLE_DATA)

    assert table_counts(db_path) == EXPECTED_COUNTS
    # The returned summary mirrors the on-disk counts.
    assert summary == EXPECTED_COUNTS


def test_seeding_twice_leaves_counts_unchanged(db_path: Path) -> None:
    scraper.seed_from_json(db_path, SAMPLE_DATA)
    first = table_counts(db_path)

    scraper.seed_from_json(db_path, SAMPLE_DATA)
    second = table_counts(db_path)

    assert first == second == EXPECTED_COUNTS


def test_reseed_refreshes_an_existing_price(db_path: Path) -> None:
    """A changed price updates in place rather than inserting a second row."""
    scraper.seed_from_json(db_path, SAMPLE_DATA)

    payload = json.loads(SAMPLE_DATA.read_text(encoding="utf-8"))
    for row in payload["pricing"]:
        if row["competitor"] == "Vultr" and row["product"] == "medium":
            row["price"] = 99.00

    edited = db_path.parent / "edited_sample_data.json"
    edited.write_text(json.dumps(payload), encoding="utf-8")
    scraper.seed_from_json(db_path, edited)

    assert table_counts(db_path) == EXPECTED_COUNTS  # no new pricing row

    conn = sqlite3.connect(db_path)
    try:
        price = conn.execute(
            """
            SELECT ph.price
            FROM pricing_history ph
            JOIN competitors c ON c.id = ph.competitor_id
            JOIN products p    ON p.id = ph.product_id
            WHERE c.name = 'Vultr' AND p.sku = 'medium'
            """
        ).fetchone()[0]
    finally:
        conn.close()

    assert price == 99.00


# ── foreign-key resolution ────────────────────────────────────────────────────


def test_every_price_resolves_to_a_competitor_and_product(db_path: Path) -> None:
    scraper.seed_from_json(db_path, SAMPLE_DATA)

    conn = sqlite3.connect(db_path)
    try:
        orphans = conn.execute(
            """
            SELECT COUNT(*)
            FROM pricing_history ph
            LEFT JOIN competitors c ON c.id = ph.competitor_id
            LEFT JOIN products    p ON p.id = ph.product_id
            WHERE c.id IS NULL OR p.id IS NULL
            """
        ).fetchone()[0]
    finally:
        conn.close()

    assert orphans == 0


def test_joined_lookup_returns_the_declared_price(db_path: Path) -> None:
    scraper.seed_from_json(db_path, SAMPLE_DATA)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT c.name AS competitor, p.sku AS sku, ph.price AS price
            FROM pricing_history ph
            JOIN competitors c ON c.id = ph.competitor_id
            JOIN products    p ON p.id = ph.product_id
            WHERE c.name = 'Vultr' AND p.sku = 'medium'
            """
        ).fetchall()
    finally:
        conn.close()

    assert len(rows) == 1
    assert rows[0]["competitor"] == "Vultr"
    assert rows[0]["price"] == 18.00


def test_unknown_competitor_reference_raises(db_path: Path) -> None:
    payload = json.loads(SAMPLE_DATA.read_text(encoding="utf-8"))
    payload["pricing"].append(
        {"competitor": "Nonexistent", "product": "nano", "price": 1.0, "date": "2026-10-01"}
    )
    bad = db_path.parent / "bad_competitor.json"
    bad.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="unknown competitor"):
        scraper.seed_from_json(db_path, bad)


def test_unknown_product_reference_raises(db_path: Path) -> None:
    payload = json.loads(SAMPLE_DATA.read_text(encoding="utf-8"))
    payload["pricing"].append(
        {"competitor": "Vultr", "product": "gigantic", "price": 1.0, "date": "2026-10-01"}
    )
    bad = db_path.parent / "bad_product.json"
    bad.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="unknown product"):
        scraper.seed_from_json(db_path, bad)


# ── validity window + snapshot bookkeeping ────────────────────────────────────


def test_prices_carry_valid_from_and_open_valid_to(db_path: Path) -> None:
    scraper.seed_from_json(db_path, SAMPLE_DATA)

    conn = sqlite3.connect(db_path)
    try:
        windows = conn.execute(
            "SELECT DISTINCT valid_from, valid_to FROM pricing_history"
        ).fetchall()
    finally:
        conn.close()

    assert windows == [("2026-10-01", None)]


def test_one_snapshot_row_per_run_survives_a_rerun(db_path: Path) -> None:
    scraper.seed_from_json(db_path, SAMPLE_DATA)
    scraper.seed_from_json(db_path, SAMPLE_DATA)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT snapshot_date, data_as_of, row_count FROM pricing_snapshots"
        ).fetchall()
    finally:
        conn.close()

    assert len(rows) == 1
    assert rows[0]["snapshot_date"] == "2026-10-01"
    assert rows[0]["data_as_of"] == "2026-10-01"
    assert rows[0]["row_count"] == EXPECTED_COUNTS["pricing_history"]


def test_later_snapshot_closes_the_prior_window(db_path: Path, tmp_path: Path) -> None:
    """A newer snapshot closes the older window — one open row per pair (B5).

    This is the invariant the plan's ruling #10 restores: after any number of
    snapshots ``valid_to IS NULL`` still identifies exactly one current price per
    ``(competitor, product)``, and the superseded row is closed at the new date.
    """
    later = shifted_snapshot(tmp_path, "2026-11-01")

    scraper.seed_from_json(db_path, SAMPLE_DATA)
    scraper.seed_from_json(db_path, later)

    conn = sqlite3.connect(db_path)
    try:
        # No (competitor, product) has anything other than exactly one open row.
        offenders = conn.execute(
            """
            SELECT competitor_id, product_id
            FROM pricing_history
            WHERE valid_to IS NULL
            GROUP BY competitor_id, product_id
            HAVING COUNT(*) <> 1
            """
        ).fetchall()
        open_rows = conn.execute(
            "SELECT COUNT(*) FROM pricing_history WHERE valid_to IS NULL"
        ).fetchone()[0]
        pair_count = conn.execute(
            "SELECT COUNT(*) FROM ("
            "    SELECT DISTINCT competitor_id, product_id FROM pricing_history"
            ")"
        ).fetchone()[0]
        # Every prior window is closed at the new valid_from, not left open.
        stale_prior = conn.execute(
            """
            SELECT COUNT(*) FROM pricing_history
            WHERE valid_from = '2026-10-01' AND valid_to IS NOT '2026-11-01'
            """
        ).fetchone()[0]
        new_open = conn.execute(
            """
            SELECT COUNT(*) FROM pricing_history
            WHERE valid_from = '2026-11-01' AND valid_to IS NULL
            """
        ).fetchone()[0]
    finally:
        conn.close()

    assert offenders == []
    assert open_rows == pair_count == EXPECTED_COUNTS["pricing_history"]  # 19
    assert stale_prior == 0
    assert new_open == EXPECTED_COUNTS["pricing_history"]


def test_later_snapshot_adds_exactly_one_snapshot_row(
    db_path: Path, tmp_path: Path
) -> None:
    """A run declaring a different ``data_as_of`` adds one snapshot row (B5).

    Closes the residual gap from ruling #9: the same-date re-run test cannot tell
    "keyed on snapshot_date" apart from "always exactly one row, ever". Asserting
    the pair of dates pins the semantics.
    """
    later = shifted_snapshot(tmp_path, "2026-11-01")

    scraper.seed_from_json(db_path, SAMPLE_DATA)
    scraper.seed_from_json(db_path, later)

    conn = sqlite3.connect(db_path)
    try:
        dates = [
            row[0]
            for row in conn.execute(
                "SELECT snapshot_date FROM pricing_snapshots ORDER BY snapshot_date"
            )
        ]
    finally:
        conn.close()

    assert dates == ["2026-10-01", "2026-11-01"]


# ── the seed file is the committed source of truth ────────────────────────────


def test_sample_data_root_carries_the_disclaimer() -> None:
    payload = json.loads(SAMPLE_DATA.read_text(encoding="utf-8"))

    assert payload["data_as_of"] == "2026-10-01"
    assert payload["illustrative"] is True
    assert isinstance(payload["disclaimer"], str)
    assert "illustrative" in payload["disclaimer"].lower()
    assert "not affiliated" in payload["disclaimer"].lower()
