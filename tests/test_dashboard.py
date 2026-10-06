"""Tests for the Phase C FastAPI + HTMX dashboard (``pricing-dashboard/``).

The suite mirrors the fragment-versus-shell contract of the reference dashboard
pattern:

1. **Fragments versus shell.** Every view route returns content-only HTML when
   the request carries ``HX-Request: true`` (an HTMX swap) and the full
   ``base.html`` shell when it does not. A fragment that carried the shell would
   nest a whole document — and a second navigation — inside ``#main``.
2. **JSON versus HTML separation.** ``/api/*`` always returns JSON, even when it
   is (unusually) asked with the ``HX-Request`` header; the view routes always
   return HTML.
3. **The search route's edge cases.** The comparison input carries
   ``name="products"``, an empty search is valid and returns every product, and a
   term filters the grid.
4. **The sketch correction.** A legitimate ``0.0`` price renders as ``$0.00``,
   not as the missing-value dash (``price is none`` distinguishes them).

All fixtures seed a throwaway database from the committed ``sample_data.json``,
so this file passes on a fresh clone where the gitignored ``market_data.db`` does
not exist — the same hermetic property CI relies on.

Run: ``.venv/bin/python -m pytest tests/ -q``
"""

from __future__ import annotations

from bs4 import BeautifulSoup
from fastapi.testclient import TestClient
import pytest

#: Every HTML view route. Must stay in sync with the ``_is_htmx`` calls in
#: ``pricing-dashboard/app.py``.
VIEW_ROUTES = ["/", "/comparison"]

#: Seed shape (Phase B): 4 competitors x 5 products = 20 cells, 19 prices.
EXPECTED_PRODUCTS = 5
EXPECTED_PRICE_ROWS = 19
EXPECTED_CELLS = 20


# ── Helpers ───────────────────────────────────────────────────────────────────


def assert_html_response(resp, expected_status: int = 200) -> None:
    assert resp.status_code == expected_status, (
        f"Expected {expected_status}, got {resp.status_code}: {resp.text[:200]}"
    )
    content_type = resp.headers.get("content-type", "")
    assert content_type.startswith("text/html"), f"Expected text/html, got {content_type}"


def parse(resp) -> BeautifulSoup:
    return BeautifulSoup(resp.text, "html.parser")


# ── HTMX nav fragments (no duplicated shell) ──────────────────────────────────


class TestHtmxNavFragments:
    """Nav links ``hx-get`` a view route into ``#main``. Those requests must
    return content-only fragments — never the shell — or the nav is duplicated."""

    @pytest.mark.parametrize("path", VIEW_ROUTES)
    def test_htmx_request_returns_fragment_without_shell(self, client, path):
        resp = client.get(path, headers={"HX-Request": "true"})
        assert_html_response(resp)
        soup = parse(resp)
        # A fragment must NOT re-render the shell …
        assert not soup.select_one(".nav-bar"), f"Fragment for {path} contains .nav-bar"
        assert not soup.select_one("#main"), f"Fragment for {path} contains #main"
        assert not soup.select_one(".site-footer"), f"Fragment for {path} contains footer"
        assert "<html" not in resp.text.lower(), f"Fragment for {path} contains <html>"
        # … but it must contain actual content.
        assert len(soup.get_text(strip=True)) > 0, f"Fragment for {path} is empty"

    @pytest.mark.parametrize("path", VIEW_ROUTES)
    def test_direct_request_returns_full_page_with_shell(self, client, path):
        resp = client.get(path)
        assert_html_response(resp)
        soup = parse(resp)
        # Direct browser navigation returns the full shell.
        assert soup.select_one(".nav-bar"), f"Direct load of {path} missing .nav-bar"
        assert soup.select_one("#main"), f"Direct load of {path} missing #main"
        assert soup.select_one(".site-footer"), f"Direct load of {path} missing footer"
        assert resp.text.lower().lstrip().startswith("<!doctype html")

    def test_shell_carries_the_vendored_htmx_asset(self, client):
        """The shell loads HTMX from /static, never a CDN."""
        soup = parse(client.get("/"))
        srcs = [s.get("src", "") for s in soup.select("script")]
        assert any(s.startswith("/static/htmx") for s in srcs), srcs
        assert not any("cdn" in s.lower() for s in srcs), srcs

    def test_nav_links_carry_the_htmx_swap_attributes(self, client):
        soup = parse(client.get("/"))
        nav_links = soup.select(".nav-bar .nav-link")
        assert len(nav_links) >= 2, f"Expected at least 2 nav links, got {len(nav_links)}"
        for link in nav_links:
            assert link.get("hx-get"), f"nav link missing hx-get: {link}"
            assert link.get("hx-target") == "#main", f"bad hx-target: {link}"
            assert link.get("hx-push-url") == "true", f"bad hx-push-url: {link}"


# ── The footer disclaimer is load-bearing ─────────────────────────────────────


class TestDisclaimer:
    def test_footer_carries_the_illustrative_disclaimer(self, client):
        text = parse(client.get("/")).get_text(" ", strip=True).lower()
        assert "illustrative" in text
        assert "not affiliated" in text
        assert "2026-10-01" in text

    def test_json_root_carries_the_disclaimer(self, client):
        body = client.get("/api/pricing").json()
        assert body["data_as_of"] == "2026-10-01"
        assert body["illustrative"] is True
        assert "illustrative" in body["disclaimer"].lower()
        assert "not affiliated" in body["disclaimer"].lower()


# ── JSON versus HTML separation ───────────────────────────────────────────────


class TestApiPricing:
    def test_api_pricing_returns_json(self, client):
        resp = client.get("/api/pricing")
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("application/json")
        body = resp.json()
        assert body["count"] == EXPECTED_PRICE_ROWS
        assert len(body["pricing"]) == EXPECTED_PRICE_ROWS
        first = body["pricing"][0]
        assert set(first) >= {"competitor", "sku", "price", "currency", "valid_to"}

    def test_api_pricing_ignores_the_htmx_header(self, client):
        """A JSON route must stay JSON even with HX-Request set."""
        resp = client.get("/api/pricing", headers={"HX-Request": "true"})
        assert resp.headers["content-type"].startswith("application/json")
        assert not resp.text.lower().lstrip().startswith("<!doctype html")

    def test_api_pricing_by_competitor_filters(self, client):
        resp = client.get("/api/pricing/Vultr")
        assert resp.status_code == 200
        body = resp.json()
        assert body["count"] == EXPECTED_PRODUCTS
        assert {record["competitor"] for record in body["pricing"]} == {"Vultr"}

    def test_api_pricing_unknown_competitor_is_404(self, client):
        assert client.get("/api/pricing/NoSuchVendor").status_code == 404

    def test_view_route_still_returns_html(self, client):
        assert client.get("/").headers["content-type"].startswith("text/html")


# ── Comparison search ─────────────────────────────────────────────────────────


class TestComparisonSearch:
    def test_comparison_input_carries_name_products(self, client):
        """The sketch correction: without name="products" the query never binds."""
        soup = parse(client.get("/comparison"))
        field = soup.select_one("#products-input")
        assert field is not None, "search input #products-input is missing"
        assert field.get("name") == "products"

    def test_empty_search_returns_every_product(self, client):
        resp = client.get("/comparison", params={"products": ""}, headers={"HX-Request": "true"})
        assert_html_response(resp)
        rows = parse(resp).select("table.pricing-grid tbody tr")
        assert len(rows) == EXPECTED_PRODUCTS

    def test_missing_search_param_returns_every_product(self, client):
        resp = client.get("/comparison", headers={"HX-Request": "true"})
        assert_html_response(resp)
        rows = parse(resp).select("table.pricing-grid tbody tr")
        assert len(rows) == EXPECTED_PRODUCTS

    def test_whitespace_only_search_returns_every_product(self, client):
        resp = client.get("/comparison", params={"products": "   "}, headers={"HX-Request": "true"})
        assert_html_response(resp)
        rows = parse(resp).select("table.pricing-grid tbody tr")
        assert len(rows) == EXPECTED_PRODUCTS

    def test_term_filters_the_grid(self, client):
        resp = client.get("/comparison", params={"products": "medium"}, headers={"HX-Request": "true"})
        assert_html_response(resp)
        rows = parse(resp).select("table.pricing-grid tbody tr")
        assert len(rows) == 1
        assert "medium" in rows[0].get_text().lower()

    def test_search_with_no_match_renders_an_empty_state(self, client):
        resp = client.get(
            "/comparison", params={"products": "gigantic"}, headers={"HX-Request": "true"}
        )
        assert_html_response(resp)
        soup = parse(resp)
        assert not soup.select("table.pricing-grid tbody tr")
        assert soup.select_one(".empty-state")


# ── The grid, and the missing-versus-zero distinction ─────────────────────────


class TestPricingGrid:
    def test_grid_has_one_cell_per_product_and_competitor(self, client):
        resp = client.get("/", headers={"HX-Request": "true"})
        cells = parse(resp).select("table.pricing-grid td.price")
        assert len(cells) == EXPECTED_CELLS
        # Exactly one combination is absent from the seed (Hetzner has no 'nano').
        dashes = [c for c in cells if c.get_text(strip=True) == "\u2014"]
        assert len(dashes) == EXPECTED_CELLS - EXPECTED_PRICE_ROWS  # == 1

    def test_legitimate_zero_price_renders_as_dollars_not_dash(self, client_zero_price):
        """`row.prices[name] or '—'` would print a dash for a real 0.0 price."""
        resp = client_zero_price.get("/", headers={"HX-Request": "true"})
        assert_html_response(resp)
        soup = parse(resp)
        text = soup.get_text(" ", strip=True)

        assert "$0.00" in text, "a legitimate 0.0 price was not rendered as $0.00"
        # The zero price did not become an extra "missing" cell: still exactly one.
        cells = soup.select("table.pricing-grid td.price")
        dashes = [c for c in cells if c.get_text(strip=True) == "\u2014"]
        assert len(dashes) == EXPECTED_CELLS - EXPECTED_PRICE_ROWS
