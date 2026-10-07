# portfolio-showcase — Master Planbook

## Purpose

Single reference for the operating state, decisions, and revision history of the
public pricing-scraper showcase. Companion to `SYSTEM_SNAPSHOT.md` (live state)
and `CHANGELOG.md` (dated change entries).

## Current snapshot

- **Last reconciled:** 2026-10-07 (`main`). **All phases complete — A–E.** The
  public repository now exists at `github.com/mrcoffeebreak/portfolio-showcase`;
  `main` carries the full build history, CI is green on the published commit, and
  the release is tagged **`v1.0.0`** (E6).
- **Status:** The repo is now a complete, self-contained artifact. Data layer,
  dashboard, notebook, a one-command bootstrap (`scripts/quick-start.sh`) and the
  full doc set (README, `LOCAL_SETUP.md`, `TECH_STACK.md`, the finalized case study)
  are all in place, behind a green **36-test** suite plus the headless notebook gate.
- **Phase E complete (E1–E5):** `scripts/quick-start.sh` (venv → runtime deps → seed
  if absent → uvicorn on **8090**); `README.md` finalized, with new `LOCAL_SETUP.md`
  and `TECH_STACK.md`; the case study **finalized and verified claim-by-claim**
  against the code (vendor count 3→4, notebook framing off "trend", SQLite row
  count "hundreds"→"dozen", HTMX size 48→50 KB, upsert key → `(competitor, product,
  valid_from)`, and the §6 trend sentence made accurate); PLANBOOK + CHANGELOG
  entries. Publishing (E6) followed once the owner gave the explicit go-ahead: the
  public repo was created, `main` pushed, CI confirmed green and `v1.0.0` tagged.
- **Phase D complete:** `notebooks/pricing_walkthrough.ipynb` — 15 cells (8 code, 7
  markdown, zero failed). Repo-root discovery by walking up from the kernel's cwd
  (a notebook has no `__file__`) feeding the **same** `import_paths.py` bootstrap;
  SQLite opened directly and **self-seeded** from `sample_data.json` when absent, so
  a fresh clone and CI both run it with no prior step. Flow: current-price view
  (`valid_to IS NULL`) → SKU × vendor grid → per-SKU cheapest/priciest/spread →
  coverage + price index → three matplotlib figures (grouped bars, cheapest-vs-
  priciest, price-index heatmap). `requirements-dev.txt` gains the pinned `jupyter`
  + `matplotlib` + `pandas` closure; `requirements.txt` (runtime) is **untouched**
  (the split is exactly `pip freeze` minus the runtime manifest). The notebook gate
  is appended to `probe_config.yaml` → `tests.command`, so the pre-commit hook and
  CI enforce it from one source of truth.
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
| **D** | Jupyter walkthrough + notebook deps + CI notebook gate | B | ✅ complete |
| **E** | Docs, `quick-start.sh`, publish, tag `v1.0.0` | C + D | ✅ complete |

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

- 2026-10-06: **Phase E — docs and the one-command bootstrap landed (E1–E5); publish held for review** — added `scripts/quick-start.sh`: create `.venv` if absent, install `requirements.txt`, seed the database from `sample_data.json` **only when it is missing**, then `exec uvicorn --app-dir pricing-dashboard app:app` on **8090**. No arguments, safe to re-run, `bash -n` clean. Replaced the Phase A `README.md` stub with the real landing page (disclaimer, quick start, architecture diagram, component summary, layout table, docs index), and wrote `LOCAL_SETUP.md` (prerequisites → quick start → by-hand steps → ports → tests → notebook → env vars → troubleshooting) and `TECH_STACK.md` (every runtime and dev tool with its rationale, plus the deliberately-absent list). **Finalized `01_PRICING_SCRAPER_CASE_STUDY.md` against the code**: the draft banner becomes a verified note, and each claim was checked — vendor count 3 → **4** (§1, §4.1); the notebook's job reworded from "what is the trend" to positioning/spread/coverage (§2), since the notebook plots one snapshot rather than a time series; SQLite "a few hundred rows" → **a few dozen** (19 observations) and HTMX "~48 KB" → **~50 KB** (§3, measured); the FastAPI rationale reworded to drop a cross-repo claim a public reader cannot verify (§3); the upsert key `(competitor, product, date)` → **`(competitor, product, valid_from)`** (§4.3); and the §6 trend sentence rewritten so it says the schema *supports* a series (superseded windows are closed, not overwritten) while the notebook plots a single snapshot. `SYSTEM_SNAPSHOT.md` refreshed (quick start + docs in Key Paths, Phase E change log). A pre-publish hygiene sweep of every tracked file — for private repository names, hostnames, account names and absolute paths — found exactly one leak: the notebook's stored setup output printed the absolute repo root (`/home/<user>/…`). Fixed: the cell now prints the directory **name** only, and code and stored output agree. Verified: full gate green (36 tests + notebook, 0 error cells); `bash -n scripts/quick-start.sh` clean; `git grep -lIE '/home/|/Users/'` over tracked files returns nothing.

- 2026-10-06: **Phase D — Jupyter walkthrough landed** — added `notebooks/pricing_walkthrough.ipynb` (15 cells: 8 code, 7 markdown, zero failed). It locates the repo root by walking up from the kernel's working directory — a notebook has no `__file__`, so this is how it finds the repo without hard-coding a path — and then reuses the **one** `import_paths.py` bootstrap so `schema`/`scraper` import by name, exactly as the tests and app do. It opens `market_data.db` directly and **calls `seed_from_json()` when the database is absent**, so a fresh clone and CI run it with no prior step; the write is idempotent. The analysis: the `valid_to IS NULL` current-price view (19 rows) → a SKU × vendor pivot ordered small→large → a per-SKU reduction (cheapest/priciest vendor, absolute and relative spread) → the price index vs. cheapest plus a coverage count, which surfaces Hetzner's missing `nano` plan as a gap rather than a win. Three matplotlib figures, each inline and paired with its insight: a grouped bar by plan, a cheapest-vs-priciest bar, and a price-index heatmap. `requirements-dev.txt` gained the notebook closure (`jupyter`, `matplotlib`, `pandas` + transitive deps, pinned from the same `pip freeze`); `requirements.txt` is **unchanged** — the split is exactly the freeze minus the runtime manifest. The notebook gate (`jupyter nbconvert --to notebook --execute --stdout …`) was **appended to `probe_config.yaml` → `tests.command`** so the local pre-commit hook and CI share one gate and cannot drift; `.github/workflows/ci.yml`'s step/comment were updated to say so (still inlined and hermetic — the notebook seeds its own database). Also corrected the case study's "four charts" to "three charts" to match. Verified: full gate run (`.venv/bin/python -m pytest tests/ -q && jupyter nbconvert --execute …`) exits 0 — 36 tests green, notebook executes with **0** `output_type: error` cells; with `market_data.db` moved aside the notebook still exits 0 and **self-seeds 4/5/19/1**; a deliberately broken notebook makes the same gate exit **1** with `CellExecutionError` on stderr.

- 2026-10-06: **Phase C — dashboard + API landed** — added `pricing-dashboard/`: `app.py` (one FastAPI app with an `APIRouter` for `/`, `/comparison`, `/api/pricing`, `/api/pricing/{competitor}`; `StaticFiles` mounted at `/static` and the router included, mirroring the reference wiring), `helpers.py` (plain-dict data access, no ORM; reuses `schema.connect()`; "current price" is a simple `valid_to IS NULL` filter; the DB path is resolved per call from `PRICING_DB_PATH` so tests never touch the gitignored artifact), `templates/` (`base.html` shell with nav, vendored HTMX, `hx-target="#main"`, `hx-push-url="true"` and the load-bearing footer disclaimer; `dashboard.html` grid and `comparison_fragment.html` search as content-only fragments) and `static/` (the vendored `htmx.min.js` — never a CDN — plus a hand-written `style.css`). `_is_htmx()` gates **every** view route. The bootstrap's sketch corrections are applied: the search input carries `name="products"` and the route tolerates empty input, and a legitimate `0.0` price renders as `$0.00` via an explicit `is none` check rather than the missing-value dash. `tests/test_dashboard.py` adds **21** tests (13 → 36 total): parameterized fragment-versus-shell coverage for both view routes, JSON-versus-HTML separation, the empty-search cases and the zero-price regression; `tests/conftest.py` loads the hyphenated app by file path and provides a `client` fixture over a throwaway seeded DB. Dependency pins frozen from `.venv/bin/pip freeze` and split so `requirements.txt` stays runtime-only. Verified: 36 tests green — including with `pricing-scraper/data/market_data.db` deleted; scraper run twice → counts unchanged (4/5/19/1); the app bound on 8090 returns no `<html>` under `HX-Request: true` and the full shell without it, while `/api/pricing` returns JSON; 8090 owned by this app, 8000/8002 untouched.

- 2026-10-06: **Phase B remediation (B5–B6) — close the price window and unify the import bootstrap** — `pricing-scraper/scraper.py`: `seed_from_json` now closes the prior open price window at ingest (an earlier row's `valid_to` is set to the new `valid_from`; the comparison is strict so a same-date re-run stays idempotent), restoring the documented "`valid_to IS NULL` is the current price" invariant. `pricing-scraper` unchanged in layout. Added `import_paths.py` at the repo root — the single documented `__file__`-relative `sys.path` bootstrap for `pricing-scraper/` — and rewrote `tests/conftest.py` to use it (replacing the hand-rolled version) so the app and notebook will share one mechanism. Added a **local-only, gitignored** `.vscode/settings.json` with `python.analysis.extraPaths = ["pricing-scraper"]`. `tests/test_scraper.py` gained two tests (13 → **15**): the one-open-row-per-`(competitor, product)` invariant and closed prior window after a later-dated snapshot, and the different-`data_as_of` snapshot case that closes the residual test gap in note #9. Verified: 15 tests green; same-date re-run counts unchanged (4/5/19/1); a `2026-11-01` run after `2026-10-01` → 38 price rows, 2 snapshot rows, 19 open rows for 19 pairs, 0 prior rows still open.
- 2026-10-06: **Phase B — data layer landed** — `pricing-scraper/schema.py` (4 tables: `competitors`, `products`, `pricing_history` with a `valid_from`/`valid_to` window, `pricing_snapshots`) plus `init_db()` / `connect()`; `pricing-scraper/sample_data.json` as the committed seed source of truth (4 vendors × 5 SKUs, 19 illustrative prices, `data_as_of: "2026-10-01"`, root disclaimer); `pricing-scraper/scraper.py` with idempotent `seed_from_json()` (`INSERT OR IGNORE` dimensions, price upsert on `(competitor, product, valid_from)`, one transaction, one snapshot row per run). Added `tests/` — 13 tests covering clean create, run-twice idempotency, FK resolution, unknown-reference rejection and the one-snapshot-row guarantee. Narrowed `probe_config.yaml`'s test command to `.venv/bin/python -m pytest tests/ -q` and made CI provision a root `.venv` so the same command runs in both places. Verified: 13 tests green; scraper run twice → counts unchanged (4/5/19/1).
- 2026-10-06: **Docs — corrected port ownership and de-identified the public docs** — The Phase A wording implied 8000 *and* 8001 were both in use locally; the verified state is that **8000 and 8002** are in use and **8001** is unbound here (reserved elsewhere). `AGENTS.md` (⇄ `.github/copilot-instructions.md`), `SESSION_RITUAL.md` (port table + the `ss -ltnp | grep -E ':(8000|8001|8002|8090)'` check), `SYSTEM_SNAPSHOT.md`, `CHANGELOG.md` and `.gitignore` updated. This entry also removes references to private sibling repositories, internal hostnames and plan-internal labels from every published file, ahead of the repo going public.
- 2026-10-06: **Phase A — repo scaffolded and house conventions installed** — `git init -b main`, MIT `LICENSE`, `README.md` stub, `.gitignore`. Installed the local git hooks (pinned **v0.2.2**): `pre-commit`/`pre-push`/`post-checkout` under `scripts/git-hooks/`, `core.hooksPath` set. Trimmed `probe_config.yaml` for a single-machine app (empty `services`/`timers`, no `ssh` block) with the test command as the single gate shared by the hook and CI. Added `requirements.txt` + `requirements-dev.txt` and a draft `.github/workflows/ci.yml` so the publish step is meaningful. Wrote the house doc set (`AGENTS.md` ⇄ `.github/copilot-instructions.md`, `PLANBOOK.md`, `CHANGELOG.md`, `SYSTEM_SNAPSHOT.md`, `SESSION_RITUAL.md`), adapted to a no-SSH ritual. Drafted `01_PRICING_SCRAPER_CASE_STUDY.md`. Recorded the seeded-DB decision (not committed) and reserved port 8090. No tests yet — `probe_config.yaml` carries a temporary `[ ! -d tests ]` guard that Phase B removes.
