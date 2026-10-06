# portfolio-showcase — Master Planbook

## Purpose

Single reference for the operating state, decisions, and revision history of the
public pricing-scraper showcase. Companion to `SYSTEM_SNAPSHOT.md` (live state)
and `CHANGELOG.md` (dated change entries).

## Current snapshot

- **Last reconciled:** 2026-10-06 (`main`). **Phases A + B + C complete**,
  committed; no `origin` remote yet, so CI is drafted but not yet exercised.
- **Status:** Data layer **and** dashboard complete. Schema, seed JSON, idempotent
  scraper (with a proper open/closed price window), the FastAPI + HTMX dashboard
  on port 8090 (shell/fragment split, JSON API) and a green **36-test** suite are
  in place. No notebook or `quick-start.sh` yet.
- **Phase C complete:** `pricing-dashboard/` — `app.py` (one FastAPI app;
  `/`, `/comparison`, `/api/pricing`, `/api/pricing/{competitor}`), `helpers.py`
  (plain dicts, no ORM; `PRICING_DB_PATH` resolved per call), `templates/`
  (`base.html` shell + `dashboard.html` / `comparison_fragment.html` fragments)
  and `static/` (vendored `htmx.min.js` + `style.css`). `_is_htmx()` gates every
  view route. `tests/test_dashboard.py` adds **21** hermetic tests (a throwaway
  DB seeded from the committed JSON, so the gitignored artifact is not needed).
  Runtime and test pins frozen from `pip freeze` and split across the two
  manifests.
- **Phase B remediation (B5–B6) complete:** `seed_from_json` now closes the earlier
  opening at ingest (ruling #10), so exactly one `valid_to IS NULL` row remains per
  `(competitor, product)`; and a single documented `import_paths.py` bootstrap puts
  `pricing-scraper/` on `sys.path` for tests (and, later, the app and notebook),
  replacing the hand-rolled `conftest.py` wiring (ruling #12).
- **Phase B complete:** `pricing-scraper/{schema.py,scraper.py,sample_data.json}` and
  `tests/`; a scraper re-run leaves row counts unchanged
  (4 competitors / 5 products / 19 prices / 1 snapshot). `probe_config.yaml`'s test
  command narrowed to the canonical `.venv/bin/python -m pytest tests/ -q`, with CI
  provisioning a root `.venv` so the same command runs in both places.
- **Phase A complete:** repo scaffolded, local git hooks installed and pinned at
  **v0.2.2**, `probe_config.yaml` trimmed for a single-machine app, house doc set
  written, CI drafted.
- **Decisions locked:** seeded data (no live scraping); the seeded `.db` is **not
  committed**; dashboard = FastAPI + vendored HTMX on port **8090**; charts live in
  the notebook; mock/illustrative data fixed at `data_as_of: 2026-10-01`.

## Build plan

| Phase | Scope | Depends on | Status |
|---|---|---|---|
| **A** | Scaffold + house conventions | — | ✅ complete |
| **B** | Data layer: schema, seed JSON, idempotent scraper, tests | A | ✅ complete |
| **C** | Dashboard + API: FastAPI, `_is_htmx()`, templates, tests | B | ✅ complete |
| **D** | Jupyter walkthrough + notebook deps + CI notebook gate | B | ⬜ not started |
| **E** | Docs, `quick-start.sh`, publish, tag `v1.0.0` | C + D | ⬜ not started |

Step-level build notes and per-phase verification are maintained by the repo
owner outside this repository.

## Decisions

1. **Standalone public repo**, MIT licensed.
2. **Seeded data, not live scraping.** Real vendor names with an explicit
   illustrative / not-affiliated disclaimer, fixed `data_as_of: 2026-10-01`, carried
   into the JSON root, README, case study, and dashboard footer.
3. **Dashboard = FastAPI + vendored HTMX**, including the `_is_htmx()`
   shell-versus-fragment split, on port **8090**. React is docs-only and out of
   scope.
4. **Charts live in the notebook.** The dashboard ships no charting JS.
5. **One venv (`.venv`) at the repo root**, one runtime manifest
   (`requirements.txt`) plus `requirements-dev.txt`. Never global pip.
6. **Seeded `.db` is not committed** — `scripts/quick-start.sh` seeds it when
   absent, so a clone proves the pipeline runs and diffs stay readable.
   `sample_data.json` is the committed source of truth.
7. **Notebook tooling lives in `requirements-dev.txt`**, keeping the runtime
   manifest lean.
8. **CI is hermetic and inlined** — it never depends on a script from a
   gitignored directory, which would be absent from a GitHub checkout.
9. **Local tooling is never published.** `scripts/git-hooks/` is ignored wholesale,
   and machine-local files that embed outside references (the installer's version
   stamp) are ignored through `.git/info/exclude` rather than the published
   `.gitignore`.

## Non-goals

Live scraping of real vendor sites, any database server, authentication, Docker,
deployment infrastructure, and a React implementation.

## Revision history

- 2026-10-06: **Phase C — dashboard + API landed** — added `pricing-dashboard/`: `app.py` (one FastAPI app with an `APIRouter` for `/`, `/comparison`, `/api/pricing`, `/api/pricing/{competitor}`; `StaticFiles` mounted at `/static` and the router included, mirroring the reference wiring), `helpers.py` (plain-dict data access, no ORM; reuses `schema.connect()`; "current price" is a simple `valid_to IS NULL` filter; the DB path is resolved per call from `PRICING_DB_PATH` so tests never touch the gitignored artifact), `templates/` (`base.html` shell with nav, vendored HTMX, `hx-target="#main"`, `hx-push-url="true"` and the load-bearing footer disclaimer; `dashboard.html` grid and `comparison_fragment.html` search as content-only fragments) and `static/` (the vendored `htmx.min.js` — never a CDN — plus a hand-written `style.css`). `_is_htmx()` gates **every** view route. The bootstrap's sketch corrections are applied: the search input carries `name="products"` and the route tolerates empty input, and a legitimate `0.0` price renders as `$0.00` via an explicit `is none` check rather than the missing-value dash. `tests/test_dashboard.py` adds **21** tests (13 → 36 total): parameterized fragment-versus-shell coverage for both view routes, JSON-versus-HTML separation, the empty-search cases and the zero-price regression; `tests/conftest.py` loads the hyphenated app by file path and provides a `client` fixture over a throwaway seeded DB. Dependency pins frozen from `.venv/bin/pip freeze` and split so `requirements.txt` stays runtime-only. Verified: 36 tests green — including with `pricing-scraper/data/market_data.db` deleted; scraper run twice → counts unchanged (4/5/19/1); the app bound on 8090 returns no `<html>` under `HX-Request: true` and the full shell without it, while `/api/pricing` returns JSON; 8090 owned by this app, 8000/8002 untouched.

- 2026-10-06: **Phase B remediation (B5–B6) — close the price window and unify the import bootstrap** — `pricing-scraper/scraper.py`: `seed_from_json` now closes the prior open price window at ingest (an earlier row's `valid_to` is set to the new `valid_from`; the comparison is strict so a same-date re-run stays idempotent), restoring the documented "`valid_to IS NULL` is the current price" invariant. `pricing-scraper` unchanged in layout. Added `import_paths.py` at the repo root — the single documented `__file__`-relative `sys.path` bootstrap for `pricing-scraper/` — and rewrote `tests/conftest.py` to use it (replacing the hand-rolled version) so the app and notebook will share one mechanism. Added a **local-only, gitignored** `.vscode/settings.json` with `python.analysis.extraPaths = ["pricing-scraper"]`. `tests/test_scraper.py` gained two tests (13 → **15**): the one-open-row-per-`(competitor, product)` invariant and closed prior window after a later-dated snapshot, and the different-`data_as_of` snapshot case that closes the residual test gap in note #9. Verified: 15 tests green; same-date re-run counts unchanged (4/5/19/1); a `2026-11-01` run after `2026-10-01` → 38 price rows, 2 snapshot rows, 19 open rows for 19 pairs, 0 prior rows still open.
- 2026-10-06: **Phase B — data layer landed** — `pricing-scraper/schema.py` (4 tables: `competitors`, `products`, `pricing_history` with a `valid_from`/`valid_to` window, `pricing_snapshots`) plus `init_db()` / `connect()`; `pricing-scraper/sample_data.json` as the committed seed source of truth (4 vendors × 5 SKUs, 19 illustrative prices, `data_as_of: "2026-10-01"`, root disclaimer); `pricing-scraper/scraper.py` with idempotent `seed_from_json()` (`INSERT OR IGNORE` dimensions, price upsert on `(competitor, product, valid_from)`, one transaction, one snapshot row per run). Added `tests/` — 13 tests covering clean create, run-twice idempotency, FK resolution, unknown-reference rejection and the one-snapshot-row guarantee. Narrowed `probe_config.yaml`'s test command to `.venv/bin/python -m pytest tests/ -q` and made CI provision a root `.venv` so the same command runs in both places. Verified: 13 tests green; scraper run twice → counts unchanged (4/5/19/1).
- 2026-10-06: **Docs — corrected port ownership and de-identified the public docs** — The Phase A wording implied 8000 *and* 8001 were both in use locally; the verified state is that **8000 and 8002** are in use and **8001** is unbound here (reserved elsewhere). `AGENTS.md` (⇄ `.github/copilot-instructions.md`), `SESSION_RITUAL.md` (port table + the `ss -ltnp | grep -E ':(8000|8001|8002|8090)'` check), `SYSTEM_SNAPSHOT.md`, `CHANGELOG.md` and `.gitignore` updated. This entry also removes references to private sibling repositories, internal hostnames and plan-internal labels from every published file, ahead of the repo going public.
- 2026-10-06: **Phase A — repo scaffolded and house conventions installed** — `git init -b main`, MIT `LICENSE`, `README.md` stub, `.gitignore`. Installed the local git hooks (pinned **v0.2.2**): `pre-commit`/`pre-push`/`post-checkout` under `scripts/git-hooks/`, `core.hooksPath` set. Trimmed `probe_config.yaml` for a single-machine app (empty `services`/`timers`, no `ssh` block) with the test command as the single gate shared by the hook and CI. Added `requirements.txt` + `requirements-dev.txt` and a draft `.github/workflows/ci.yml` so the publish step is meaningful. Wrote the house doc set (`AGENTS.md` ⇄ `.github/copilot-instructions.md`, `PLANBOOK.md`, `CHANGELOG.md`, `SYSTEM_SNAPSHOT.md`, `SESSION_RITUAL.md`), adapted to a no-SSH ritual. Drafted `01_PRICING_SCRAPER_CASE_STUDY.md`. Recorded the seeded-DB decision (not committed) and reserved port 8090. No tests yet — `probe_config.yaml` carries a temporary `[ ! -d tests ]` guard that Phase B removes.
