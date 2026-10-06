# portfolio-showcase — Agent Instructions

> Mirror pair: keep in sync with `AGENTS.md` (repo root).

## What this repo is

A **seeded** competitor-pricing pipeline used as a public proof-of-work:
scraped-style data → SQLite → FastAPI + HTMX dashboard → Jupyter walkthrough.

It is **not** connected to any vendor. All pricing is illustrative and fixed at
`data_as_of: 2026-10-01`. See *Change Policy* before touching any data or copy.

## Session Start Ritual

1. **Read `SYSTEM_SNAPSHOT.md`** and `SESSION_RITUAL.md` from this repo.
2. **Run the tests:** `.venv/bin/python -m pytest tests/ -q`.
3. **Report drift** against `SYSTEM_SNAPSHOT.md` (row counts, port, test count).
4. **Smoke-check the app** if the dashboard has been built:
   `./scripts/quick-start.sh`, then load `http://127.0.0.1:8090/`.

There is **no remote host**. Do not probe the NUC, do not SSH anywhere — this
repo runs entirely on the Dev Box.

## End-of-Session Ritual

1. **Update `SYSTEM_SNAPSHOT.md`** with what actually changed this session.
2. **Run tests** to confirm nothing broke.
3. **Commit and document** (`PLANBOOK.md` / `CHANGELOG.md`) before ending.

The `pre-commit` hook (installed via `dev-tools/install.sh`) does 2 and 3
partially for you: it refreshes the snapshot date and **blocks the commit if the
test command in `probe_config.yaml` fails**.

## Key Architecture

| Piece | Detail |
|---|---|
| Dashboard | FastAPI + **vendored** HTMX (`static/htmx.min.js`, never a CDN), port **8090** |
| View routes | Must implement the `_is_htmx()` shell-vs-fragment split — see *Change Policy* |
| Data | SQLite at `pricing-scraper/data/market_data.db`, **seeded, not committed** |
| Seed source | `pricing-scraper/sample_data.json` (this is the source of truth) |
| Analysis | `notebooks/pricing_walkthrough.ipynb` — charts live here, not in the dashboard |
| Ports taken | 8000 (ai-platform-api) and 8001 (algo-trader-api-v2). Use 8090. |

## Change Policy

- **The disclaimer is load-bearing.** If you change data, copy, templates or
  docs, keep the "illustrative, not affiliated, `data_as_of: 2026-10-01`" claim
  intact and consistent across README, case study, JSON root, and the dashboard
  footer.
- **Never add live scraping** of real vendor sites, real API keys, auth, a DB
  server, Docker, or deployment infrastructure. Those are explicit non-goals.
- **`_is_htmx()` is mandatory on every view route.** Returning a full shell to an
  HTMX swap duplicates the nav; this is the exact bug `algo-trader` fixed in
  `bf506a7`. Do not regress it.
- **Deps:** `.venv/bin/pip` only — never global pip. Then re-freeze
  `requirements.txt`. Notebook/charting deps go in `requirements-dev.txt`.
- **CI must stay hermetic and inlined.** Never reference
  `scripts/git-hooks/dev-tools/ci.sh` from CI — that path is gitignored and absent
  from a GitHub checkout (see the `algo-trader` CI incident).

## Cross-Repo Context

This repo is a standalone public artifact. The private homelab repos that share
its conventions live alongside it under `~/projects/`; see `~/projects/AGENTS.md`
for the index. The reference implementation for the dashboard patterns is
`algo-trader` (`scripts/dashboard_routes.py`, `templates/base.html`,
`tests/test_dashboard.py`).

## Working-Session Efficiency

- **One chat per concern.** Open a new chat when the task type changes.
- **Keep the working set small.** Prefer targeted section reads over re-reading
  whole documents.
- **Delegate heavy research** to a subagent and return only the summary.
- **Bound session length.** Resume from docs rather than letting a chat run on.
- **Commit discipline.** Document, commit, and push completed work before ending
  a session.
