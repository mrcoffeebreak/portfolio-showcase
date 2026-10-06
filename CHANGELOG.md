# Changelog

All notable changes to this repo are documented here. Newest first.

## 2026-10-06

### Added

- **tooling:** `scripts/quick-start.sh` — the one-command bootstrap from a fresh
  clone to a running dashboard: create a root `.venv` if absent, install
  `requirements.txt`, seed `market_data.db` from `sample_data.json` **only when it
  is missing**, then `exec uvicorn --app-dir pricing-dashboard app:app` on **8090**.
  It takes no arguments and is safe to re-run.
- **docs:** `LOCAL_SETUP.md` — prerequisites, the quick start, the equivalent
  by-hand commands, the port table, running the tests, running the notebook, the
  environment variables and troubleshooting. `TECH_STACK.md` — every runtime and
  development tool with its rationale, plus what is deliberately absent (an ORM, a
  bundler, a database server, Docker, a dashboard charting library, live scraping).
- **notebook:** `notebooks/pricing_walkthrough.ipynb` — the analysis half of the
  pipeline and this repo's first notebook. It finds the repository root by walking
  up from the kernel's working directory (a notebook has no `__file__`), then
  reuses the single `import_paths.py` bootstrap so `schema` / `scraper` import by
  name exactly as the tests and app do. It opens `market_data.db` directly —
  seeding it from the committed `sample_data.json` when it is absent, so a fresh
  clone and CI both run it with no manual step — and walks from the
  `valid_to IS NULL` current-price view through a SKU × vendor grid and a per-SKU
  cheapest/priciest/spread reduction to a price index and a coverage check. Three
  inline matplotlib figures (grouped bars, cheapest-vs-priciest, price-index
  heatmap) each pair with an insight, and a closing section covers how the same
  pipeline would run in production. 8 code cells, 7 markdown cells, zero failed.
- **dashboard:** `pricing-dashboard/app.py` — one FastAPI app with an `APIRouter`
  exposing `/` (comparison grid), `/comparison` (search view),
  `/api/pricing` (all current prices as JSON) and `/api/pricing/{competitor}`
  (filtered JSON). `StaticFiles` is mounted at `/static` and the router is
  included, mirroring the established wiring. `_is_htmx(request)` gates **every**
  view route: `HX-Request: true` returns a content-only fragment, a direct load
  returns the full `base.html` shell — without the split an HTMX swap nests a
  whole document inside `#main` and duplicates the navigation. The hyphenated
  directory means the app is served with `--app-dir` (or loaded by file path in
  tests), and the module reuses the repo's single `import_paths.py` bootstrap.
  Port **8090**.
- **dashboard:** `pricing-dashboard/helpers.py` — plain-dict data access, no ORM.
  Reuses `schema.connect()` and reads "current price" as a simple
  `valid_to IS NULL` filter (Phase B's ruling #10 invariant). The database path
  is resolved **per call** from `PRICING_DB_PATH`, defaulting to the
  repo-relative `pricing-scraper/data/market_data.db`, so the test suite can point
  the app at a throwaway database without reloading modules. A missing database
  degrades to an empty state rather than an error.
- **dashboard:** `pricing-dashboard/templates/base.html` — the shell: nav links
  with `hx-get` / `hx-target="#main"` / `hx-push-url="true"`, the vendored HTMX
  script, and the **load-bearing footer disclaimer** (illustrative, not
  affiliated, `data_as_of: 2026-10-01`).
- **dashboard:** `pricing-dashboard/templates/dashboard.html` +
  `templates/comparison_fragment.html` — the comparison grid and the search view,
  rendered both inside the shell and standalone as HTMX fragments. The sketch
  corrections are applied: the search input carries `name="products"` (without it
  the route's query parameter never binds) and the route tolerates empty input;
  and a legitimate `0.0` price renders as `$0.00` through an explicit `is none`
  check, so the missing-value dash is reserved for a genuinely absent price.
- **dashboard:** `pricing-dashboard/static/htmx.min.js` — the vendored MIT asset
  (~48 KB), copied into the repo; **never** a CDN. `static/style.css` — a
  hand-written, dark, table-first stylesheet with no build step.
- **tests:** `tests/test_dashboard.py` — **21** hermetic dashboard tests (15 → 36
  in total): parameterized fragment-versus-shell coverage for both view routes
  (no shell markers under `HX-Request: true`; the full shell without it), the
  HTMX nav attributes and vendored-asset check, JSON-versus-HTML separation, the
  empty-search cases (`products=""`, missing and whitespace-only), and the
  zero-price-not-a-dash regression. `tests/conftest.py` loads the hyphenated
  `pricing-dashboard/app.py` by file path and adds a `client` fixture that seeds a
  throwaway database from the committed `sample_data.json` and points the app at
  it via `PRICING_DB_PATH` — so the suite passes with the gitignored
  `market_data.db` deleted, exactly as CI needs.
- **tooling:** `import_paths.py` — the single documented, `__file__`-relative
  `sys.path` bootstrap for the hyphenated `pricing-scraper/` directory. Resolved
  from the module's own `__file__` (never the working directory), it is shared by
  the test suite today and the dashboard/notebook later — no rename, no editable
  install, no per-module one-off.
- **tests:** two more tests in `tests/test_scraper.py` (13 → **15**) — the
  one-open-row-per-`(competitor, product)` invariant with a closed prior window
  after a later-dated snapshot, and the different-`data_as_of` case that pins the
  snapshot-row semantics.
- **repo:** Initial scaffold — `git init -b main`, MIT `LICENSE`, `README.md` stub
  (landing page is finalized in Phase E), `.gitignore`, and the `.github/` prompt
  mirror.
- **tooling:** local git hooks installed and pinned at **v0.2.2** —
  `scripts/git-hooks/{pre-commit,pre-push,post-checkout}`, `core.hooksPath` set,
  starter `secrets_config.yaml` and `repo_owners.yaml` seeded. The hooks are a
  local-only convenience: neither the hook bundle nor the symlinks are published.
- **ci:** `.github/workflows/ci.yml` drafted with **inlined, hermetic** steps: it
  installs both manifests, validates `probe_config.yaml`, and runs the test command
  from `probe_config.yaml` → `tests.command` (the same single source of truth the
  pre-commit hook uses). No step depends on a local helper script, which would be
  absent from a GitHub checkout.
- **deps:** `requirements.txt` (runtime) and `requirements-dev.txt` (test/analysis),
  to be frozen with `.venv/bin/pip freeze` once Phase C installs.
- **docs:** house doc set — `AGENTS.md` ⇄ `.github/copilot-instructions.md` (mirror
  pair), `PLANBOOK.md`, `CHANGELOG.md`, `SYSTEM_SNAPSHOT.md`, `SESSION_RITUAL.md` —
  adapted for a repo with **no remote host**: the ritual is read snapshot → run
  tests → check drift → smoke-check on port 8090 → update snapshot. No SSH.
- **docs:** draft `01_PRICING_SCRAPER_CASE_STUDY.md`.
- **data:** `pricing-scraper/schema.py` — SQLite schema + `init_db(path)`. Four
  tables: natural-keyed `competitors` and `products`; `pricing_history` with a
  `valid_from`/`valid_to` validity window (upsert key
  `(competitor_id, product_id, valid_from)`); and `pricing_snapshots`, unique on
  `snapshot_date`. Every statement is `CREATE ... IF NOT EXISTS`, and `connect()`
  enforces `PRAGMA foreign_keys` on every connection.
- **data:** `pricing-scraper/sample_data.json` — the committed seed source of truth:
  four real vendor names (DigitalOcean, Linode, Vultr, Hetzner) across five comparable
  SKUs (19 illustrative prices), with `data_as_of: "2026-10-01"`, `illustrative: true`
  and the not-affiliated `disclaimer` at the root.
- **data:** `pricing-scraper/scraper.py` — `seed_from_json(db_path, data_file)`:
  `INSERT OR IGNORE` for the dimensions, price upsert on
  `(competitor_id, product_id, valid_from)`, a single transaction, and exactly one
  snapshot row keyed on the snapshot date. Idempotent — a re-run over unchanged input
  leaves every row count unchanged.
- **tests:** `tests/test_scraper.py` — 13 tests: schema creation and re-init; clean
  seed counts; seeding twice leaves counts unchanged; a changed price updates in place;
  foreign-key resolution and an orphan check; unknown-reference rejection; open
  `valid_to`; one snapshot row per run; and the seed file's root disclaimer contract.
  `tests/conftest.py` puts the hyphenated `pricing-scraper/` directory on `sys.path`
  so the modules import by name.

### Changed

- **docs:** `README.md` finished — the landing page now carries the illustrative-
  data disclaimer, the quick start, the architecture diagram, a component summary,
  a layout table and the docs index.
- **docs:** `01_PRICING_SCRAPER_CASE_STUDY.md` **finalized against the shipped
  code**, replacing the Phase A draft banner with a verified-against-code note.
  Claims corrected: vendor count 3 → 4; the notebook's framing changed from "what
  is the trend" to positioning/spread/coverage (it plots one snapshot, not a time
  series); SQLite "a few hundred rows" → "a few dozen"; HTMX "~48 KB" → "~50 KB";
  the FastAPI rationale no longer leans on a cross-repository claim a public reader
  cannot verify; the upsert key is now stated as
  `(competitor, product, valid_from)`; and the §6 trend sentence now says the schema
  *supports* a series while the notebook plots a single snapshot.
- **ci:** the notebook is now part of the single shared gate. Phase D appended
  `jupyter nbconvert --to notebook --execute --stdout
  notebooks/pricing_walkthrough.ipynb > /dev/null` to `probe_config.yaml` →
  `tests.command`, so the pre-commit hook and CI execute the walkthrough from one
  source of truth — a broken notebook now blocks a commit as well as the build.
  The `ci.yml` step name and header comment were updated to match; no step points
  at a gitignored script and the notebook seeds its own database, so the job stays
  inlined and hermetic.
- **deps:** `requirements-dev.txt` gained the notebook toolchain — the pinned
  `jupyter`, `matplotlib` and `pandas` closure. They are dev-only: `requirements.txt`
  (runtime) is unchanged, and the split remains exactly `pip freeze` minus the
  runtime manifest.
- **deps:** `requirements.txt` and `requirements-dev.txt` are now **pinned** from a
  single `.venv/bin/pip freeze` and split so the runtime manifest stays lean.
  `requirements.txt` carries the pinned closure of `fastapi` + `uvicorn` + `jinja2`
  (HTMX is vendored, so it is deliberately absent); `requirements-dev.txt` carries
  `pytest`, `httpx`, `beautifulsoup4`, `PyYAML` and their transitive deps. CI
  installs both, so the versions frozen here are the versions that run.
- **data:** `seed_from_json` now **closes the prior price window at ingest**. Before
  a newer observation is written, the earlier open row's `valid_to` is set to the
  new `valid_from`, so exactly one row per `(competitor, product)` keeps
  `valid_to IS NULL` (the documented "current price" marker) and a superseded row
  carries a real closed window. The `valid_from <` comparison is strict, so a
  same-date re-run remains idempotent; all writes stay in the one transaction.
- **tests:** `tests/conftest.py` no longer hand-rolls `sys.path`; it delegates to
  the shared `import_paths.add_pricing_scraper_to_path()`, so there is exactly one
  bootstrap into `pricing-scraper/` and the suite imports `schema` / `scraper` by
  name from any working directory.
- **config (local, not published):** `.vscode/settings.json` (gitignored) sets
  `python.analysis.extraPaths = ["pricing-scraper"]` so the editor agrees with the
  runtime import bootstrap.
- **config:** `probe_config.yaml` trimmed for a single-machine app — no `ssh` block,
  empty `services`/`timers`, no inert `ports:`/`cron:` keys, and the test command set
  to the venv-first form used by both the hook and CI.
- **config:** `repo_owners.yaml` asserts the expected GitHub owner for this repo so
  the pre-push hook catches an account-crossing push (it is intended to be public).
- **config:** `probe_config.yaml` → `tests.command` is now the canonical
  `.venv/bin/python -m pytest tests/ -q`; the scaffold-era `[ ! -d tests ]` guard is
  removed now that the suite exists.
- **ci:** the workflow provisions a repository-root `.venv` and runs its validation and
  test steps with it, so the command in `probe_config.yaml` executes identically locally
  and in CI. (The job previously installed into the runner interpreter, which would have
  made the narrowed command exit 127 on the runner while passing locally.)

### Decisions

- **The seeded SQLite artifact is deliberately not committed.** `sample_data.json` is
  the committed source of truth and `scripts/quick-start.sh` will seed the database on
  demand, so a fresh clone exercises the real pipeline instead of trusting a binary.
- **Port 8090** is the dashboard's port, served by this app. 8000 and 8002 are in
  use by other local services; 8001 is reserved and unbound here.
- **Vendored HTMX**, never a CDN. Charts belong to the notebook, not the dashboard.

### Fixed

- **docs:** the case study claimed the notebook ships "four charts"; the walkthrough
  ships three. Corrected so the draft matches the implementation it describes.
- **data:** `valid_to` was never populated, so every observation stayed "open" and
  the documented `valid_to IS NULL` idiom returned one row per pair per snapshot.
  `seed_from_json` now closes the previous window when a newer snapshot is ingested,
  restoring the invariant.
- **tests:** the same-date re-run test could not distinguish "keyed on
  `snapshot_date`" from "always exactly one row, ever"; a run declaring a later
  `data_as_of` now asserts exactly one additional `pricing_snapshots` row.
- **repo:** Untracked the git-hook symlinks. They pointed into a gitignored
directory, so a fresh clone got three **dangling symlinks** — and because
`core.hooksPath` is local git config that is not cloned, they could never have run
there anyway. `scripts/git-hooks/` is now ignored wholesale, and the installer's
version stamp (which embeds another repository's commit hash) is ignored via the
local, unpublished `.git/info/exclude` rather than the published `.gitignore`.
- **docs:** Corrected port ownership, and removed private context. The earlier wording
  claimed 8000 *and* 8001 were both in use locally; the verified state is that **8000
  and 8002** are in use and **8001** is unbound here (reserved elsewhere).
  `SESSION_RITUAL.md` now carries a port table plus the check command
  `ss -ltnp | grep -E ':(8000|8001|8002|8090)'`.
- **docs:** Every published file was rewritten to stand alone — references to private
  sibling repositories, internal hostnames and plan-internal step labels were replaced
  with self-contained wording, since this repo is intended to be public. No behavioural
  change: the operative rules (vendored HTMX, `_is_htmx()` on every view route, port
  8090, `.venv`-only installs, inlined CI) are unchanged.

### Known gaps

- No `origin` remote yet — publishing (create the public repository, push `main`,
  confirm CI is green, tag `v1.0.0`) is the last remaining step and is held for an
  explicit go-ahead.
