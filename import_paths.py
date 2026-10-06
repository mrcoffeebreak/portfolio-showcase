"""Single import bootstrap for the portfolio-showcase repo.

The application modules live in ``pricing-scraper/`` — a directory whose name
contains a hyphen, so it is not importable as a package and cannot appear on an
``import`` line. Every consumer that needs ``import schema`` / ``import scraper``
(the test suite now; the FastAPI app and the notebook later) therefore has to
put that directory on ``sys.path``.

Rather than repeat a hand-rolled ``sys.path`` hack in each file, this module is
the **one** place that does it. It resolves ``pricing-scraper/`` relative to its
own ``__file__`` — never to the current working directory — so it behaves the
same whether it is imported from ``tests/``, ``pricing-dashboard/`` or a
notebook. There is no rename of ``pricing-scraper/``, no editable install and no
per-module one-off.

Usage — the identical prologue in every consumer::

    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # repo root
    from import_paths import add_pricing_scraper_to_path  # noqa: E402

    add_pricing_scraper_to_path()

``tests/conftest.py`` does exactly this, so the suite imports ``schema`` and
``scraper`` by name regardless of the directory pytest is invoked from.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
PRICING_SCRAPER_DIR = REPO_ROOT / "pricing-scraper"


def add_pricing_scraper_to_path() -> Path:
    """Put ``pricing-scraper/`` on ``sys.path`` (once) and return the path.

    Idempotent: a second call does not add a duplicate entry.
    """
    entry = str(PRICING_SCRAPER_DIR)
    if entry not in sys.path:
        sys.path.insert(0, entry)
    return PRICING_SCRAPER_DIR
