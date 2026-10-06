"""Tests for the seeded pricing data layer (``schema.py`` + ``scraper.py``).

The suite covers the four properties Phase B promises:

1. ``init_db`` creates exactly the four expected tables and is safe to re-run.
2. A seed run produces the expected row counts, and a second run over the same
   input changes nothing (idempotency — the core ingestion guarantee).
3. Foreign keys resolve: every ``pricing_history`` row joins to a real
   competitor and product, and the declared names map to the declared prices.
4. A run records exactly one ``pricing_snapshots`` row, keyed on the snapshot
   date, so "one row per run" survives a re-run on the same date.

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


# ── the seed file is the committed source of truth ────────────────────────────


def test_sample_data_root_carries_the_disclaimer() -> None:
    payload = json.loads(SAMPLE_DATA.read_text(encoding="utf-8"))

    assert payload["data_as_of"] == "2026-10-01"
    assert payload["illustrative"] is True
    assert isinstance(payload["disclaimer"], str)
    assert "illustrative" in payload["disclaimer"].lower()
    assert "not affiliated" in payload["disclaimer"].lower()
