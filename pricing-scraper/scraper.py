"""Seed the SQLite pricing database from ``sample_data.json``.

``seed_from_json(db_path, data_file)`` is the single ingestion entry point and
is **idempotent**: running it any number of times over unchanged input leaves
every table's row count unchanged. That property is what makes a scheduled
re-run safe, and it is asserted directly by ``tests/test_scraper.py``.

How idempotency is achieved:

- Dimension rows (``competitors``, ``products``) use ``INSERT OR IGNORE`` against
  their natural key (``name`` / ``sku``). The first insert wins, so primary keys
  stay stable across runs and foreign keys keep resolving to the same rows.
- Price rows upsert on ``(competitor_id, product_id, valid_from)`` — the natural
  key for an observation. Re-seeding the same snapshot date updates the price in
  place rather than appending a duplicate.
- The run records exactly one ``pricing_snapshots`` row, keyed on
  ``snapshot_date`` (the declared ``data_as_of``), and upserts it too.

All writes happen in a single transaction, so a malformed input file leaves the
database exactly as it was.

Run ``./venv/bin/python -m pytest tests/`` for the invariants this module must
uphold, or invoke it directly to (re)build the local artifact:

    .venv/bin/python pricing-scraper/scraper.py
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

from schema import connect, init_db

DEFAULT_DB_PATH = Path(__file__).resolve().parent / "data" / "market_data.db"
DEFAULT_DATA_FILE = Path(__file__).resolve().parent / "sample_data.json"

TABLE_NAMES = ("competitors", "products", "pricing_history", "pricing_snapshots")


def _table_counts(conn: sqlite3.Connection) -> dict[str, int]:
    """Return ``{table: row_count}`` for the four pipeline tables."""
    return {
        table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in TABLE_NAMES
    }


def seed_from_json(db_path: str | Path, data_file: str | Path) -> dict[str, int]:
    """Load ``data_file`` into the SQLite database at ``db_path``.

    Creates the database and schema when absent. Returns a ``{table: count}``
    summary of the four tables after seeding (useful for logging and tests).

    Raises ``ValueError`` if a pricing row references a competitor or product
    that is not declared in the same file — a loud failure beats a silently
    dropped row or an orphaned foreign key.
    """
    db_path = Path(db_path)
    data_file = Path(data_file)

    with open(data_file, encoding="utf-8") as fh:
        payload = json.load(fh)

    data_as_of = payload["data_as_of"]
    default_currency = payload.get("currency", "USD")

    init_db(db_path)
    conn = connect(db_path)
    try:
        with conn:  # one transaction: all-or-nothing
            # --- Dimension tables: INSERT OR IGNORE keeps natural keys stable.
            for competitor in payload.get("competitors", []):
                conn.execute(
                    "INSERT OR IGNORE INTO competitors (name, website) VALUES (?, ?)",
                    (competitor["name"], competitor.get("website")),
                )

            for product in payload.get("products", []):
                conn.execute(
                    "INSERT OR IGNORE INTO products (sku, name, category) VALUES (?, ?, ?)",
                    (product["sku"], product["name"], product.get("category")),
                )

            # --- Resolve foreign keys by natural key, once.
            competitor_ids = {
                row["name"]: row["id"]
                for row in conn.execute("SELECT id, name FROM competitors")
            }
            product_ids = {
                row["sku"]: row["id"]
                for row in conn.execute("SELECT id, sku FROM products")
            }

            # --- Price observations: upsert on (competitor, product, valid_from).
            pricing_rows = payload.get("pricing", [])
            for row in pricing_rows:
                competitor_name = row["competitor"]
                product_sku = row["product"]

                if competitor_name not in competitor_ids:
                    raise ValueError(
                        f"pricing row references unknown competitor: {competitor_name!r}"
                    )
                if product_sku not in product_ids:
                    raise ValueError(
                        f"pricing row references unknown product SKU: {product_sku!r}"
                    )

                conn.execute(
                    """
                    INSERT INTO pricing_history
                        (competitor_id, product_id, price, currency, valid_from, valid_to)
                    VALUES (?, ?, ?, ?, ?, NULL)
                    ON CONFLICT (competitor_id, product_id, valid_from)
                    DO UPDATE SET price    = excluded.price,
                                  currency = excluded.currency
                    """,
                    (
                        competitor_ids[competitor_name],
                        product_ids[product_sku],
                        row["price"],
                        row.get("currency", default_currency),
                        row.get("date", data_as_of),
                    ),
                )

            # --- Exactly one snapshot row per run, keyed on the snapshot date.
            conn.execute(
                """
                INSERT INTO pricing_snapshots
                    (snapshot_date, data_as_of, source_file, row_count)
                VALUES (?, ?, ?, ?)
                ON CONFLICT (snapshot_date)
                DO UPDATE SET data_as_of  = excluded.data_as_of,
                              source_file = excluded.source_file,
                              row_count   = excluded.row_count
                """,
                (data_as_of, data_as_of, data_file.name, len(pricing_rows)),
            )

        return _table_counts(conn)
    finally:
        conn.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Seed the portfolio-showcase pricing database from JSON."
    )
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="SQLite database path")
    parser.add_argument("--data", default=str(DEFAULT_DATA_FILE), help="seed JSON path")
    args = parser.parse_args(argv)

    counts = seed_from_json(args.db, args.data)
    print(f"Seeded {args.db} from {Path(args.data).name}")
    for table in TABLE_NAMES:
        print(f"  {table:<18} {counts[table]}")
    return 0


if __name__ == "__main__":  # pragma: no cover - manual convenience
    raise SystemExit(main())
