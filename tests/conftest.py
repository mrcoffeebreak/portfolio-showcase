"""Pytest configuration for the portfolio-showcase test suite.

The application modules live in ``pricing-scraper/`` — a directory whose name
contains a hyphen, so it cannot be imported as a package. This file does **not**
hand-roll the ``sys.path`` fix; it reuses the repo's single documented bootstrap
(``import_paths.py`` at the repo root), which inserts ``pricing-scraper/``
relative to its own ``__file__``. The FastAPI app and the notebook will call the
same function, so there is exactly one mechanism.

The short prologue below only makes ``import_paths`` itself importable: the repo
root is resolved from ``__file__`` (not the working directory), so the suite
behaves the same wherever pytest is invoked from.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from import_paths import add_pricing_scraper_to_path  # noqa: E402

add_pricing_scraper_to_path()
