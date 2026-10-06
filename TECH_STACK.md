# Tech stack

Every choice here is deliberate, and the reasoning matters more than the list. The
full narrative — including what was rejected and why — is in
[`01_PRICING_SCRAPER_CASE_STUDY.md`](01_PRICING_SCRAPER_CASE_STUDY.md).

## Runtime

| Tool | Role | Why |
|---|---|---|
| **Python 3.10+** | everything | One language for ingestion, the API and the analysis keeps the repo small and the seams obvious. |
| **SQLite** (`sqlite3`, stdlib) | storage | The dataset is a few dozen rows. A database server would be pure operational overhead for a repo whose value is being clonable and runnable in one command — and a single file is the honest default for a small dataset that has to survive a restart. |
| **FastAPI** | HTTP layer | Typed query parameters (the search route binds `products: str`), automatic OpenAPI documentation at `/docs`, and JSON responses that fit the API without a serialization layer. |
| **Uvicorn** | ASGI server | The standard way to serve an ASGI app: one process, one port, no configuration. |
| **Jinja2** | templates | FastAPI's templating default. It keeps the shell-versus-fragment split explicit and readable in the markup. |
| **HTMX** (vendored) | interactivity | Fragment swaps give real interactivity with no build step and no client-side state to keep in sync. The ~50 KB file is **vendored** at `pricing-dashboard/static/htmx.min.js` — never a CDN — so the app works offline and the repo has no external dependency. |

## Development

| Tool | Role | Why |
|---|---|---|
| **pytest** | test suite | Fast, plain-function tests. The suite is hermetic: it seeds a throwaway database from the committed JSON, so it never depends on the generated artifact. |
| **httpx** | TestClient transport | FastAPI's `TestClient` is built on it. |
| **beautifulsoup4** | HTML assertions | Lets the dashboard tests assert *structure* — that a fragment carries no shell markers — instead of string-matching raw HTML. |
| **PyYAML** | config read | CI and the pre-commit hook both read `probe_config.yaml`. |
| **Jupyter + ipykernel** | the walkthrough | The analysis narrative is a notebook because that is where exploration, prose and charts belong together. |
| **pandas** | analysis | The pivot and per-SKU reductions in the notebook are one line each instead of hand-rolled loops. |
| **matplotlib** | charts | Three static figures, rendered inline. No interactive charting framework. |

Both manifests are pinned from the same `pip freeze`, split so the runtime
manifest (`requirements.txt`) stays lean and the notebook/test toolchain lives in
`requirements-dev.txt`.

## Deliberately absent

- **An ORM.** The SQL is short enough that the query *is* the documentation; an ORM
  would add a layer to read past without removing any decisions.
- **A build step or bundler.** HTMX is vendored and the CSS is hand-written.
- **A database server.** See SQLite above.
- **Docker and deployment infrastructure.** The repo is meant to be cloned and run
  in one command on a laptop; that is the point, not a shortcut.
- **A charting library in the dashboard.** Charts belong to the notebook, which is
  what keeps the dashboard small and its payload static.
- **Live scraping.** The pipeline's shape is the deliverable; anti-bot handling and
  terms-of-service risk would obscure it. See the case study, §4.1.
