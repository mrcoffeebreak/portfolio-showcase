# Changelog

All notable changes to this repo are documented here. Newest first.

## 2026-10-06

### Added

- **repo:** Initial scaffold — `git init -b main`, MIT `LICENSE`, `README.md` stub
  (landing page is finalized in Phase E), `.gitignore` modelled on the `algo-trader`
  and `ai-platform` repos, and the `.github/` prompt mirror.
- **tooling:** `dev-tools` hooks installed and pinned at **v0.2.2 (557b0fa)** —
  `scripts/git-hooks/{pre-commit,pre-push,post-checkout}` symlinked into
  `scripts/git-hooks/dev-tools/`, `core.hooksPath` set, starter `secrets_config.yaml`
  and `repo_owners.yaml` seeded.
- **ci:** `.github/workflows/ci.yml` drafted with **inlined, hermetic** steps: it
  installs both manifests, validates `probe_config.yaml`, and runs the test command
  from `probe_config.yaml` → `tests.command` (the same single source of truth the
  pre-commit hook uses). It never references the gitignored
  `scripts/git-hooks/dev-tools/ci.sh`.
- **deps:** `requirements.txt` (runtime) and `requirements-dev.txt` (test/analysis),
  to be frozen with `.venv/bin/pip freeze` once Phase C installs.
- **docs:** house doc set — `AGENTS.md` ⇄ `.github/copilot-instructions.md` (mirror
  pair), `PLANBOOK.md`, `CHANGELOG.md`, `SYSTEM_SNAPSHOT.md`, `SESSION_RITUAL.md` —
  adapted for a repo with **no remote host**: the ritual is read snapshot → run
  tests → check drift → smoke-check on port 8090 → update snapshot. No SSH.
- **docs:** draft `01_PRICING_SCRAPER_CASE_STUDY.md`.

### Changed

- **config:** `probe_config.yaml` trimmed for a NUC-less repo — no `ssh` block, empty
  `services`/`timers`, no inert `ports:`/`cron:` keys, and the test command set to the
  venv-first form used by both the hook and CI.
- **config:** `repo_owners.yaml` asserts `portfolio-showcase: mrcoffeebreak` so the
  pre-push hook catches an account-crossing push (the repo is intended to be public).

### Decisions

- **The seeded SQLite artifact is deliberately not committed.** `sample_data.json` is
  the committed source of truth and `scripts/quick-start.sh` will seed the database on
  demand, so a fresh clone exercises the real pipeline instead of trusting a binary.
- **Port 8090** reserved for the dashboard. Owned by others: 8000 (`ai-platform-api`)
  and 8002 (`ai-platform-api-linda`) on the Dev Box, plus 8001 which belongs to
  `algo-trader-api-v2` on the NUC (nothing binds it on the Dev Box).
- **Vendored HTMX**, never a CDN. Charts belong to the notebook, not the dashboard.

### Fixed

- **docs:** Corrected port ownership. The earlier wording claimed 8000 *and 8001* were
  bound on the Dev Box; the verified state is that the Dev Box binds **8000**
  (`ai-platform-api`) and **8002** (`ai-platform-api-linda`), while **8001** is reserved
  for `algo-trader-api-v2` on the **NUC** and is not bound here. `SESSION_RITUAL.md` now
  carries a port table plus the check command
  `ss -ltnp | grep -E ':(8000|8001|8002|8090)'`.

### Known gaps

- No tests yet — the suite lands in Phase B. `probe_config.yaml` carries a temporary
  `[ ! -d tests ]` guard (documented inline) that Phase B removes.
- No `origin` remote and no commits yet; publishing is Phase E.
