"""Pytest configuration for the portfolio-showcase test suite.

The application code lives in ``pricing-scraper/`` — a directory whose name
contains a hyphen, so it cannot be imported as a package. Adding it to
``sys.path`` here lets tests (and, later, the notebook) ``import schema`` and
``import scraper`` by module name.

Keeping the path wiring in one place means the tests do not each carry a
``sys.path`` hack, and the production modules stay importable from a plain
script run (where the script's own directory is already on the path).
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
APP_DIR = REPO_ROOT / "pricing-scraper"

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))
