"""Data access for the pricing dashboard.

Every function here returns **plain ``dict`` / ``list`` structures** — there is no
ORM, no model layer and no serialization glue. The dashboard's SQL is short
enough that the query *is* the documentation, and the JSON API and the HTML
views read from the same helpers, so a change to the query can never make the
two views disagree about what the data is.

This module deliberately imports ``schema`` from ``pricing-scraper/`` (placed on
``sys.path`` by the repo's single import bootstrap, ``import_paths.py``) and
reuses ``schema.connect()`` so ``PRAGMA foreign_keys`` and the ``sqlite3.Row``
row factory are consistent with the rest of the pipeline.

The database path is resolved **at call time** from the ``PRICING_DB_PATH``
environment variable, falling back to the repo-relative
``pricing-scraper/data/market_data.db``. Resolving lazily (rather than freezing a
module-level constant at import) is what lets the test suite point the app at a
throwaway database without reloading modules — see ``tests/conftest.py``.

A missing database is not an error: the helpers return empty structures and the
templates render an empty state, so the app starts cleanly before the seed step
has run.
"""

from __future__ import annotations

import os
import re
import sqlite3
from pathlib import Path

import schema  # from pricing-scraper/, placed on sys.path by import_paths

#: Environment variable that overrides the database location (used by tests and
#: by ``scripts/quick-start.sh`` when it wants an explicit artifact).
DB_PATH_ENV_VAR = "PRICING_DB_PATH"

#: Default artifact, resolved relative to this file — never to the cwd.
DEFAULT_DB_PATH = (
    Path(__file__).resolve().parent.parent
    / "pricing-scraper"
    / "data"
    / "market_data.db"
)

#: Columns selected for a current-price record. ``valid_to IS NULL`` marks the
#: current price (Phase B ruling #10), so "current" is a simple filter.
_SELECT_CURRENT = """
SELECT c.name       AS competitor,
       c.website    AS website,
       p.sku        AS sku,
       p.name       AS product_name,
       p.category   AS category,
       ph.price     AS price,
       ph.currency  AS currency,
       ph.valid_from AS valid_from,
       ph.valid_to  AS valid_to
  FROM pricing_history ph
  JOIN competitors c ON c.id = ph.competitor_id
  JOIN products    p ON p.id = ph.product_id
 {where}
 ORDER BY p.id, c.name
"""

_TERM_SPLIT = re.compile(r"[,\s]+")


def get_db_path() -> Path:
    """Return the database path, honouring ``PRICING_DB_PATH`` at call time."""
    override = os.environ.get(DB_PATH_ENV_VAR)
    return Path(override) if override else DEFAULT_DB_PATH


def _connect() -> sqlite3.Connection | None:
    """Open a connection, or return ``None`` when the database is absent."""
    path = get_db_path()
    if not path.exists():
        return None
    return schema.connect(path)


def _fetch_all(sql: str, params: tuple = ()) -> list[dict]:
    """Run ``sql`` and return plain dicts, or ``[]`` when there is no database."""
    conn = _connect()
    if conn is None:
        return []
    try:
        return [dict(row) for row in conn.execute(sql, params).fetchall()]
    finally:
        conn.close()


# ── Dimensions ────────────────────────────────────────────────────────────────


def get_competitors() -> list[dict]:
    """Return every competitor as ``{id, name, website}``, ordered by name."""
    return _fetch_all("SELECT id, name, website FROM competitors ORDER BY name")


def get_products() -> list[dict]:
    """Return every comparable SKU as ``{id, sku, name, category}``."""
    return _fetch_all(
        "SELECT id, sku, name, category FROM products ORDER BY id"
    )


def competitor_exists(name: str) -> bool:
    """True when a competitor with this exact name exists."""
    rows = _fetch_all("SELECT 1 AS found FROM competitors WHERE name = ?", (name,))
    return bool(rows)


# ── Current prices ────────────────────────────────────────────────────────────


def get_pricing_records(competitor: str | None = None) -> list[dict]:
    """Return current price records, optionally filtered to one competitor.

    "Current" means ``valid_to IS NULL`` — Phase B closes the prior window at
    ingest, so exactly one such row exists per ``(competitor, product)``.
    """
    where = "WHERE ph.valid_to IS NULL"
    params: tuple = ()
    if competitor is not None:
        where += " AND c.name = ?"
        params = (competitor,)
    return _fetch_all(_SELECT_CURRENT.format(where=where), params)


def get_snapshot() -> dict | None:
    """Return the most recent snapshot row, or ``None`` before the first seed."""
    rows = _fetch_all(
        """
        SELECT snapshot_date, data_as_of, source_file, row_count, created_at
          FROM pricing_snapshots
         ORDER BY snapshot_date DESC
         LIMIT 1
        """
    )
    return rows[0] if rows else None


# ── The comparison grid ───────────────────────────────────────────────────────


def _search_terms(query: str | None) -> list[str]:
    """Split a raw search box value into lower-cased terms (empty → no filter)."""
    if not query:
        return []
    return [term for term in _TERM_SPLIT.split(query.strip().lower()) if term]


def _product_matches(product: dict, terms: list[str]) -> bool:
    """True when *every* term appears in the SKU, name or category."""
    haystack = " ".join(
        str(product.get(field) or "") for field in ("sku", "name", "category")
    ).lower()
    return all(term in haystack for term in terms)


def get_pricing_grid(query: str | None = None) -> dict:
    """Build the comparison grid: one row per product, one column per vendor.

    Returns ``{"competitors": [...], "rows": [{"product": {...}, "prices": {...}}]}``
    where ``prices`` maps competitor name to the current price, or ``None`` when
    that vendor does not offer the SKU. ``None`` (not ``0.0``) is the missing
    marker, so the template can distinguish "no price" from a legitimate ``$0.00``
    with an explicit ``is none`` check.

    ``query`` filters the rows through :func:`_search_terms`; an empty or
    whitespace-only query returns every product.
    """
    competitors = get_competitors()
    products = get_products()

    # (sku, competitor) -> price, from the current-price records.
    price_by_pair = {
        (record["sku"], record["competitor"]): record["price"]
        for record in get_pricing_records()
    }

    terms = _search_terms(query)
    rows = []
    for product in products:
        if terms and not _product_matches(product, terms):
            continue
        rows.append(
            {
                "product": product,
                "prices": {
                    competitor["name"]: price_by_pair.get(
                        (product["sku"], competitor["name"])
                    )
                    for competitor in competitors
                },
            }
        )

    return {"competitors": competitors, "rows": rows}
