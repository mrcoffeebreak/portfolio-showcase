"""FastAPI + HTMX dashboard for the portfolio-showcase pricing pipeline.

One app, four routes:

- ``GET /``                     — the comparison grid (HTML, shell or fragment)
- ``GET /comparison``           — the search view (HTML, shell or fragment)
- ``GET /api/pricing``          — every current price, as JSON
- ``GET /api/pricing/{name}``   — one competitor's current prices, as JSON

The HTML routes implement the **shell-versus-fragment split** via
``_is_htmx(request)``: a request carrying ``HX-Request: true`` (an HTMX swap)
receives only the view content, while a direct browser navigation receives the
full ``base.html`` shell. Getting this wrong nests a whole HTML document inside
``#main`` and renders the navigation twice — the classic server-rendered-HTMX
pitfall — so the check is applied to every view route without exception.

Run it on port 8090::

    .venv/bin/python -m uvicorn --app-dir pricing-dashboard app:app --port 8090

The directory name contains a hyphen, so ``pricing-dashboard`` cannot be imported
as a package; ``--app-dir`` puts it on ``sys.path`` exactly as running the file
directly would. The prologue below does the same for the two things this module
needs at import time: the repo root (for the shared ``import_paths`` bootstrap)
and its own directory (for the sibling ``helpers`` module).
"""

from __future__ import annotations

import sys
from pathlib import Path

DASHBOARD_DIR = Path(__file__).resolve().parent
REPO_ROOT = DASHBOARD_DIR.parent

# Repo root → ``import_paths``; own directory → the sibling ``helpers`` module.
# Inserting this file's own directory mirrors what Python does automatically for
# a directly-executed script, so the module behaves the same however it is loaded.
for _path in (DASHBOARD_DIR, REPO_ROOT):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from import_paths import add_pricing_scraper_to_path  # noqa: E402

# The single documented bootstrap for the hyphenated ``pricing-scraper/`` package.
add_pricing_scraper_to_path()

from fastapi import APIRouter, FastAPI, HTTPException, Query, Request  # noqa: E402
from fastapi.responses import HTMLResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from fastapi.templating import Jinja2Templates  # noqa: E402

import helpers  # noqa: E402  (sibling module in this directory)

TEMPLATES_DIR = DASHBOARD_DIR / "templates"
STATIC_DIR = DASHBOARD_DIR / "static"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

#: The disclaimers are load-bearing (see AGENTS.md → Change Policy): the same
#: illustrative / not-affiliated claim and fixed ``data_as_of`` appear in the
#: JSON root, the README, the case study and the dashboard footer.
DATA_AS_OF = "2026-10-01"
DISCLAIMER = (
    "All pricing data on this page is illustrative and was not collected from "
    "live vendor sites. Values are fixed at data_as_of 2026-10-01. Vendor names "
    "are used to describe a realistic scenario only; this project is not "
    "affiliated with, endorsed by, or acting on behalf of any vendor mentioned."
)

app = FastAPI(
    title="portfolio-showcase pricing dashboard",
    version="0.1.0",
    description=(
        "Seeded competitor-pricing dashboard (illustrative data, "
        "data_as_of 2026-10-01)."
    ),
)

router = APIRouter()


# ── Helpers ───────────────────────────────────────────────────────────────────


def _is_htmx(request: Request) -> bool:
    """True for HTMX fragment swaps (the ``HX-Request`` header is present).

    View routes must return only the view content when this is true. Returning
    the full ``base.html`` shell to a swap nests the document (and the nav)
    inside ``#main``; see the module docstring.
    """
    return request.headers.get("HX-Request", "").lower() == "true"


def _base_context() -> dict:
    """Context shared by every HTML view (disclaimer + seed metadata)."""
    return {
        "data_as_of": DATA_AS_OF,
        "disclaimer": DISCLAIMER,
        "snapshot": helpers.get_snapshot(),
    }


def _pricing_payload(records: list[dict]) -> dict:
    """Wrap current-price records in the JSON envelope both API routes return."""
    return {
        "data_as_of": DATA_AS_OF,
        "illustrative": True,
        "disclaimer": DISCLAIMER,
        "count": len(records),
        "pricing": records,
    }


# ── HTML views (shell vs fragment) ────────────────────────────────────────────


@router.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Comparison grid — one row per product, one column per competitor."""
    context = _base_context()
    context["active_view"] = "dashboard"
    context.update(helpers.get_pricing_grid())
    if _is_htmx(request):
        return templates.TemplateResponse(request, "dashboard.html", context)
    return templates.TemplateResponse(request, "base.html", context)


@router.get("/comparison", response_class=HTMLResponse)
async def comparison(request: Request, products: str = Query("")):
    """Search view — re-renders the results table as the query changes.

    ``products`` is the search box value (the input carries ``name="products"``).
    An empty or whitespace-only value is valid and returns every product; the
    route must never reject an empty search.
    """
    context = _base_context()
    context["active_view"] = "comparison"
    context["query"] = products
    context.update(helpers.get_pricing_grid(products))
    if _is_htmx(request):
        return templates.TemplateResponse(request, "comparison_fragment.html", context)
    return templates.TemplateResponse(request, "base.html", context)


# ── JSON API ──────────────────────────────────────────────────────────────────


@router.get("/api/pricing")
async def api_pricing():
    """Every current price as JSON (``valid_to IS NULL`` per pair)."""
    return _pricing_payload(helpers.get_pricing_records())


@router.get("/api/pricing/{competitor}")
async def api_pricing_for_competitor(competitor: str):
    """One competitor's current prices as JSON; 404 for an unknown name."""
    records = helpers.get_pricing_records(competitor)
    if not records and not helpers.competitor_exists(competitor):
        raise HTTPException(status_code=404, detail=f"Unknown competitor: {competitor}")
    return _pricing_payload(records)


# ── Wiring (StaticFiles mount + router include) ───────────────────────────────

if STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.include_router(router)


if __name__ == "__main__":  # pragma: no cover - manual convenience
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8090)
