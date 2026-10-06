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

### Changed

- **config:** `probe_config.yaml` trimmed for a single-machine app — no `ssh` block,
  empty `services`/`timers`, no inert `ports:`/`cron:` keys, and the test command set
  to the venv-first form used by both the hook and CI.
- **config:** `repo_owners.yaml` asserts the expected GitHub owner for this repo so
  the pre-push hook catches an account-crossing push (it is intended to be public).

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

- No tests yet — the suite lands in Phase B. `probe_config.yaml` carries a temporary
  `[ ! -d tests ]` guard (documented inline) that Phase B removes.
- No `origin` remote and no commits yet; publishing is Phase E.
