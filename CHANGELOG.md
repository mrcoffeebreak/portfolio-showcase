# Changelog

All notable changes to this repo are documented here. Newest first.

## 2026-10-06

### Added

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
- **Port 8090** reserved for the dashboard. 8000 and 8002 are in use by other local
  services; 8001 is reserved and unbound here.
- **Vendored HTMX**, never a CDN. Charts belong to the notebook, not the dashboard.

### Fixed

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

- No `origin` remote yet; publishing is Phase E.
