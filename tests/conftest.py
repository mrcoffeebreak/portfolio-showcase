"""Pytest configuration for the portfolio-showcase test suite.

The application modules live in ``pricing-scraper/`` — a directory whose name
contains a hyphen, so it cannot be imported as a package. This file does **not**
hand-roll the ``sys.path`` fix; it reuses the repo's single documented bootstrap
(``import_paths.py`` at the repo root), which inserts ``pricing-scraper/``
relative to its own ``__file__``. The FastAPI app and the notebook call the same
function, so there is exactly one mechanism.

The short prologue below only makes ``import_paths`` itself importable: the repo
root is resolved from ``__file__`` (not the working directory), so the suite
behaves the same wherever pytest is invoked from.

It also provides the dashboard fixtures. ``pricing-dashboard/`` has the same
hyphen problem, so the app is loaded **by file path** (``importlib.util``) rather
than imported by name. Each client fixture seeds a throwaway database from the
committed ``sample_data.json`` and points the app at it through the
``PRICING_DB_PATH`` environment variable, so the dashboard tests are **hermetic**:
they pass on a fresh clone where ``pricing-scraper/data/market_data.db`` — a
gitignored artifact — does not exist.
"""

from __future__ import annotations

import importlib.util
import sqlite3
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from import_paths import add_pricing_scraper_to_path  # noqa: E402

add_pricing_scraper_to_path()

import scraper  # noqa: E402  (resolves via the bootstrap above)

SAMPLE_DATA = REPO_ROOT / "pricing-scraper" / "sample_data.json"
DASHBOARD_APP_PATH = REPO_ROOT / "pricing-dashboard" / "app.py"


def _load_dashboard_app() -> ModuleType:
    """Load ``pricing-dashboard/app.py`` by file path and return the module.

    The directory name contains a hyphen, so the app cannot be imported as
    ``pricing_dashboard.app``. Loading by path is the same trick uvicorn's
    ``--app-dir`` performs; the app's own prologue then puts its directory on
    ``sys.path`` so its sibling ``helpers`` module resolves.
    """
    spec = importlib.util.spec_from_file_location("pricing_dashboard_app", DASHBOARD_APP_PATH)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise RuntimeError(f"Could not load dashboard app from {DASHBOARD_APP_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def dashboard_app() -> ModuleType:
    """The FastAPI app module, loaded once for the whole session.

    Safe to share: the database path is resolved per request from the
    ``PRICING_DB_PATH`` environment variable, so each test's monkeypatched value
    is the one its requests see.
    """
    return _load_dashboard_app()


@pytest.fixture
def seeded_db(tmp_path: Path) -> Path:
    """Seed a fresh database from the committed ``sample_data.json``."""
    db_path = tmp_path / "market_data.db"
    scraper.seed_from_json(db_path, SAMPLE_DATA)
    return db_path


@pytest.fixture
def client(dashboard_app: ModuleType, seeded_db: Path, monkeypatch: pytest.MonkeyPatch):
    """A ``TestClient`` whose app reads from a throwaway seeded database."""
    from fastapi.testclient import TestClient

    monkeypatch.setenv("PRICING_DB_PATH", str(seeded_db))
    return TestClient(dashboard_app.app)


@pytest.fixture
def client_zero_price(
    dashboard_app: ModuleType, seeded_db: Path, monkeypatch: pytest.MonkeyPatch
):
    """Like ``client``, but one current price is set to a legitimate ``0.0``.

    Used to prove the template renders ``$0.00`` for a real zero price instead of
    the missing-value dash.
    """
    from fastapi.testclient import TestClient

    conn = sqlite3.connect(seeded_db)
    try:
        with conn:
            conn.execute(
                """
                UPDATE pricing_history
                   SET price = 0.0
                 WHERE valid_to IS NULL
                   AND competitor_id = (SELECT id FROM competitors WHERE name = 'Vultr')
                   AND product_id    = (SELECT id FROM products    WHERE sku  = 'medium')
                """
            )
    finally:
        conn.close()

    monkeypatch.setenv("PRICING_DB_PATH", str(seeded_db))
    return TestClient(dashboard_app.app)
