"""SQLite schema for the portfolio-showcase pricing pipeline.

This module owns the database DDL and the two helpers that every consumer
(the scraper, the dashboard and the notebook) should share:

- ``connect(path)`` opens a connection with ``sqlite3.Row`` rows and foreign
  keys enforced. ``PRAGMA foreign_keys`` is **per-connection**, so enabling it
  inside ``init_db`` alone would not protect later writers — every connection
  goes through here.
- ``init_db(path)`` creates the database (and its parent directory) and applies
  the schema. It is safe to call any number of times: every statement is
  ``CREATE ... IF NOT EXISTS``.

The database holds four tables. The two dimension tables key on a natural key,
so ingestion can use ``INSERT OR IGNORE`` and keep primary keys stable across
runs:

- ``competitors``      — one row per vendor (natural key: ``name``).
- ``products``         — one row per comparable SKU (natural key: ``sku``).
- ``pricing_history``  — price observations as a validity window
  (``valid_from`` / ``valid_to``); ``valid_to IS NULL`` marks the price that is
  current as of ``data_as_of``. The natural key for an upsert is
  ``(competitor_id, product_id, valid_from)``.
- ``pricing_snapshots`` — one row per snapshot date describing the seed run
  (source file, declared ``data_as_of`` and row count). Unique on
  ``snapshot_date`` so re-seeding the same day updates in place instead of
  appending a duplicate.

Run ``./venv/bin/python -m pytest tests/`` for the invariants this schema is
expected to uphold.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA_SQL = r"""
-- Foreign keys are enforced per-connection; schema.py -> connect() sets this
-- for every writer, and it is repeated here so a bare executescript() is safe.
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS competitors (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL UNIQUE,
    website    TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS products (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    sku        TEXT NOT NULL UNIQUE,
    name       TEXT NOT NULL,
    category   TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS pricing_history (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    competitor_id INTEGER NOT NULL,
    product_id    INTEGER NOT NULL,
    price         REAL NOT NULL,
    currency      TEXT NOT NULL DEFAULT 'USD',
    valid_from    TEXT NOT NULL,
    valid_to      TEXT,
    recorded_at   TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (competitor_id) REFERENCES competitors(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id)    REFERENCES products(id)    ON DELETE CASCADE,
    UNIQUE (competitor_id, product_id, valid_from)
);

CREATE TABLE IF NOT EXISTS pricing_snapshots (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_date TEXT NOT NULL UNIQUE,
    data_as_of    TEXT NOT NULL,
    source_file   TEXT,
    row_count     INTEGER NOT NULL DEFAULT 0,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_pricing_history_lookup
    ON pricing_history (competitor_id, product_id, valid_from);

CREATE INDEX IF NOT EXISTS idx_pricing_history_current
    ON pricing_history (valid_to);
"""


def connect(db_path: str | Path) -> sqlite3.Connection:
    """Open a connection with row access by name and foreign keys enforced."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: str | Path) -> Path:
    """Create (if needed) and initialize the SQLite database at ``db_path``.

    Creates the parent directory when missing, applies the schema, and returns
    the resolved path. Idempotent: safe to call on an existing database.
    """
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(path))
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(SCHEMA_SQL)
        conn.commit()
    finally:
        conn.close()

    return path


if __name__ == "__main__":  # pragma: no cover - manual convenience
    import sys

    default = Path(__file__).resolve().parent / "data" / "market_data.db"
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else default
    print(f"Initialized schema at {init_db(target)}")
