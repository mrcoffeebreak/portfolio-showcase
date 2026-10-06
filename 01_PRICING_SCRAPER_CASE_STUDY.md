# Case Study: A Competitor Pricing Pipeline

> **Finalized in Phase E** against the shipped implementation: every claim below
> was checked against `pricing-scraper/`, `pricing-dashboard/` and `notebooks/`.
> Where this document and the code disagreed, the code won.

**All pricing data in this project is illustrative.** It was not collected from
live vendor sites. Values are fixed at `data_as_of: 2026-10-01` and vendor names
are used to describe a realistic scenario only; this project is not affiliated
with, endorsed by, or acting on behalf of any vendor mentioned.

---

## 1. Problem Statement

Competitive pricing is a moving target. A team that wants to know where it sits
against four named competitors, across a handful of comparable SKUs, is asking a
question that never stops needing an answer — and the manual version of that
answer (open three pricing pages, copy numbers into a spreadsheet, remember what
changed last month) decays the moment it is written down. It is slow, it is
error-prone, and because a human is transcribing prices by hand it is also
unrepeatable: two people doing the same exercise on the same day will produce two
different spreadsheets.

The interesting engineering problem is therefore not "scrape a price." It is:
**make the collection repeatable, make the storage honest, and make the result
readable** — so that a pricing question becomes a query instead of a project.

This project is a compact, self-contained implementation of that pipeline, built
as a public proof-of-work. It deliberately stops short of scraping live vendor
sites (see *Key Decisions*) so the architecture is the thing on display, not the
fragility of a scraper.

## 2. Architecture Overview

```
              ┌─────────────────────┐
              │ sample_data.json    │   committed seed source (source of truth)
              └──────────┬──────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │ scraper.py          │   seed_from_json() — idempotent
              │ (schema.py owns DDL)│   INSERT OR IGNORE + UPSERT
              └──────────┬──────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │ SQLite              │   market_data.db  (generated, NOT committed)
              │ 4 tables            │
              └──────────┬──────────┘
                         │
          ┌──────────────┴───────────────┐
          ▼                              ▼
┌─────────────────────┐        ┌─────────────────────┐
│ FastAPI             │        │ Jupyter notebook    │
│  /                  │        │  (analysis + charts)│
│  /api/pricing       │        │  reads SQLite       │
│  /api/pricing/{c}   │        │  directly           │
│  /comparison        │        └─────────────────────┘
└──────────┬──────────┘
           │  HTMX (vendored, no build step)
           ▼
┌─────────────────────┐
│ Dashboard  :8090    │
└─────────────────────┘
```

Two consumers sit on the same database. The dashboard answers *"what is the price
right now, and who is cheapest for this SKU?"* — the grid and the search view. The
notebook answers *"what is the shape of this market, and where are the gaps?"* —
positioning, spread and coverage. Keeping them separate is what lets the dashboard
stay small: it ships no charting library at all.

## 3. Stack & Tools

| Choice | Why this and not the alternative |
|---|---|
| **SQLite** | The entire dataset is a few dozen rows (19 price observations). A database server would be pure operational overhead for a repo whose value is being clonable and runnable in one command. |
| **FastAPI** | Typed query parameters (the search route binds `products: str`), automatic OpenAPI docs at `/docs`, and a template story that keeps the shell-versus-fragment split explicit. |
| **HTMX (vendored)** | Server-rendered HTML with fragment swaps gives real interactivity with no build step and no client-side state to keep in sync. Vendoring the ~50 KB file means the app works offline and the repo has no CDN dependency. |
| **Jinja2** | Already the FastAPI templating default; keeps the shell/fragment split explicit. |
| **pandas + matplotlib (notebook)** | Standard, inspectable, and good enough for the three charts the analysis actually needs. |

Deliberately absent: any ORM (the SQL is the point and it is short), any bundler,
any container.

## 4. Key Decisions

### 4.1 Seeded data instead of live scraping

The pipeline's *shape* is the deliverable, not its input. Scraping four real
vendor pricing pages would add anti-bot handling, rate limiting, brittle CSS
selectors and terms-of-service risk — all of which would need to be maintained for
the demo to keep working, and all of which would obscure the architecture.

So the input is a reviewed JSON file with realistic values, fixed at
`data_as_of: 2026-10-01`, and the disclaimer travels with the data into the JSON
root, the README, this case study, and the dashboard footer. The scraper's seam is
the file format: pointing `seed_from_json()` at a different producer is a
contained change.

### 4.2 The generated database is not committed

`sample_data.json` is the source of truth; `market_data.db` is an artifact.
Committing it would mean reviewing a binary diff on every data change, and it would
hide the one thing a reader most wants to verify — that the pipeline actually runs.
Instead `scripts/quick-start.sh` creates and seeds the database when it is missing,
so a fresh clone proves the ingestion path end to end.

### 4.3 Idempotent ingestion

The scraper is safe to run any number of times. Dimension rows (`competitors`,
`products`) are inserted with `INSERT OR IGNORE` against a natural key, and pricing
rows are upserted on `(competitor, product, valid_from)` — the natural key for an
observation. A second run over unchanged input changes no row counts — which is the property that makes a scheduled re-run
safe, and the property the test suite asserts directly.

### 4.4 The shell-versus-fragment split

Every view route returns *either* a full page or a bare fragment, depending on
whether the request carries the `HX-Request` header. Without this split, an HTMX
navigation click swaps a complete HTML document into the content region and the
nav renders twice. This is a real pitfall of server-rendered HTMX, not a
hypothetical one — it is the kind of bug that survives review because the page
looks right until a user clicks a nav link. This project handles it up front with
explicit `_is_htmx()` routing rather than rediscovering it in production.

## 5. How It Works

1. **Seed.** `scraper.seed_from_json(db_path, data_file)` loads `sample_data.json`,
   normalizes it into the four tables defined in `schema.py`, and commits in a
   single transaction. Re-running is a no-op.
2. **API.** The FastAPI app exposes `/api/pricing` (all prices, as JSON) and
   `/api/pricing/{competitor}` (filtered). These are the machine-readable views.
3. **Dashboard.** `/` renders the comparison grid — one row per product, one column
   per competitor — and `/comparison` re-renders just the results table as a
   fragment as you type, driven by HTMX. Port **8090**.
4. **Analysis.** `notebooks/pricing_walkthrough.ipynb` opens the SQLite file
   directly, walks the schema, runs the analytical queries, and plots the result.
   Charts live here, not in the dashboard.

## 6. Demo & Next Steps

Run instructions live in `LOCAL_SETUP.md` (`./scripts/quick-start.sh`), and the
analysis narrative lives in the notebook. Tooling rationale is in `TECH_STACK.md`.

The natural extensions are the ones the schema was designed to accept without
refactoring. **Add competitors or products** by adding rows to `sample_data.json`
— no code change is required. **Track history over time** by seeding a second
snapshot with a later `data_as_of`: ingestion closes the previous price window
rather than overwriting it, so a superseded price stays queryable and a trend
becomes a query over `pricing_history`. The notebook today plots a single
snapshot's positioning; a second snapshot is what would turn that into a series.
