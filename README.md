# portfolio-showcase

A seeded competitor-pricing pipeline that runs end to end: data collection → SQLite
→ a FastAPI + HTMX dashboard → a Jupyter analysis walkthrough.

It is a public proof-of-work — one small, complete, readable slice of data work:
ingestion that is safe to re-run, a storage shape that keeps history, a
server-rendered UI with no build step, and a notebook that turns the same data into
an answer.

> **All pricing data in this repository is illustrative and was not collected from
> live vendor sites.** Values are fixed at `data_as_of: 2026-10-01`. Vendor names
> are used to describe a realistic scenario only; this project is not affiliated
> with, endorsed by, or acting on behalf of any vendor mentioned.

## Quick start

```bash
./scripts/quick-start.sh
```

Then open <http://127.0.0.1:8090/>.

The script creates the virtualenv, installs the runtime dependencies, builds the
SQLite database from `sample_data.json` if it is missing, and serves the dashboard.
No arguments, no configuration, no external services. For prerequisites, the manual
steps and troubleshooting, see [`LOCAL_SETUP.md`](LOCAL_SETUP.md).

## What it does

```
sample_data.json ──► scraper.py ──► SQLite (4 tables) ──┬──► FastAPI + HTMX   :8090
 (source of truth)   (idempotent)      market_data.db    │     grid · search · JSON API
                                        (generated)       └──► Jupyter notebook
                                                              analysis + charts
```

- **Ingestion** — `pricing-scraper/scraper.py` loads a reviewed JSON file into four
  tables in a single transaction. `INSERT OR IGNORE` for the dimension tables and
  an upsert on `(competitor, product, valid_from)` for prices make the load
  **idempotent**: running it twice changes no row counts. Ingesting a newer
  snapshot *closes* the previous price window (`valid_to`) rather than overwriting
  it, so a superseded price stays queryable.
- **Dashboard** — `pricing-dashboard/` serves a comparison grid, a search view and
  a JSON API (`/api/pricing`). Every HTML view route implements the HTMX
  **shell-versus-fragment split** via `_is_htmx()`, so a navigation click swaps only
  the content region instead of nesting a whole document inside it. HTMX is
  **vendored** at `static/htmx.min.js` — no CDN and no build step.
- **Analysis** — `notebooks/pricing_walkthrough.ipynb` opens the same SQLite file
  directly and plots the positioning, the per-SKU spread and the coverage gaps.
  Charts live here; the dashboard ships no charting library at all.

## Layout

| Path | What it is |
|---|---|
| `pricing-scraper/` | `schema.py` (DDL), `scraper.py` (ingestion), `sample_data.json` (source of truth) |
| `pricing-dashboard/` | `app.py` (routes + `_is_htmx()`), `helpers.py` (plain-dict SQL), `templates/`, `static/` |
| `notebooks/` | `pricing_walkthrough.ipynb` — the analysis narrative |
| `scripts/` | `quick-start.sh` — the one-command bootstrap |
| `tests/` | Hermetic pytest suite for the schema, the scraper and the dashboard |
| `01_PRICING_SCRAPER_CASE_STUDY.md` | The design story: the problem, the decisions, the trade-offs |
| `LOCAL_SETUP.md` · `TECH_STACK.md` | How to run it · why these tools |

## Documentation

- **[`01_PRICING_SCRAPER_CASE_STUDY.md`](01_PRICING_SCRAPER_CASE_STUDY.md)** — the
  problem, the architecture, and the decisions behind them: seeded data instead of
  live scraping, an uncommitted database artifact, idempotent ingestion, and the
  shell-versus-fragment split.
- **[`LOCAL_SETUP.md`](LOCAL_SETUP.md)** — prerequisites, running it, tests, the notebook.
- **[`TECH_STACK.md`](TECH_STACK.md)** — each tool, why it is here, and what is
  deliberately absent.

## Tests

```bash
.venv/bin/python -m pytest tests/ -q
```

The suite is **hermetic**: it seeds a throwaway database from the committed
`sample_data.json`, so it passes with `market_data.db` deleted — which is exactly
what CI does. The single gate command in `probe_config.yaml` also executes the
notebook headlessly, so a broken walkthrough fails the build too.

## License

MIT — see [`LICENSE`](LICENSE).
