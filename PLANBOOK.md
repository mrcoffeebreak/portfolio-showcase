# portfolio-showcase — Master Planbook

## Purpose

Single reference for the operating state, decisions, and revision history of the
public pricing-scraper showcase. Companion to `SYSTEM_SNAPSHOT.md` (live state)
and `CHANGELOG.md` (dated change entries).

## Current snapshot

- **Last reconciled:** 2026-10-06 on the Dev Box (`main`). **Nothing built yet** —
  Phase A complete, no commits, no `origin` remote, CI not yet exercised.
- **Status:** Scaffold only. `git init` + house conventions. No application code,
  no tests, no `quick-start.sh`.
- **Phase A complete:** repo scaffolded, `dev-tools` hooks installed and pinned at
  **v0.2.2 (557b0fa)**, `probe_config.yaml` trimmed for a repo with no NUC,
  house doc set written, CI drafted.
- **Decisions locked:** seeded data (no live scraping); the seeded `.db` is **not
  committed**; dashboard = FastAPI + vendored HTMX on port **8090**; charts live in
  the notebook; mock/illustrative data fixed at `data_as_of: 2026-10-01`.

## Build plan

| Phase | Scope | Depends on | Status |
|---|---|---|---|
| **A** | Scaffold + house conventions | — | ✅ complete |
| **B** | Data layer: schema, seed JSON, idempotent scraper, tests | A | ⬜ not started |
| **C** | Dashboard + API: FastAPI, `_is_htmx()`, templates, tests | B | ⬜ not started |
| **D** | Jupyter walkthrough + notebook deps + CI notebook gate | B | ⬜ not started |
| **E** | Docs, `quick-start.sh`, publish, tag `v1.0.0` | C + D | ⬜ not started |

Full step-level plan and per-phase verification: `~/projects/portfolio-showcase-plan.md`.

## Decisions

1. **Standalone public repo**, MIT licensed, at `~/projects/portfolio-showcase/`.
2. **Seeded data, not live scraping.** Real vendor names with an explicit
   illustrative / not-affiliated disclaimer, fixed `data_as_of: 2026-10-01`, carried
   into the JSON root, README, case study, and dashboard footer.
3. **Dashboard = FastAPI + vendored HTMX** following `algo-trader`'s implementation
   (including the `_is_htmx()` shell-vs-fragment split), on port **8090**.
   React is docs-only and out of scope.
4. **Charts live in the notebook.** The dashboard ships no charting JS.
5. **One venv (`.venv`) at the repo root**, one runtime manifest
   (`requirements.txt`) plus `requirements-dev.txt`. Never global pip.
6. **Seeded `.db` is not committed** — `scripts/quick-start.sh` seeds it when
   absent, so a clone proves the pipeline runs and diffs stay readable.
   `sample_data.json` is the committed source of truth.
7. **Notebook tooling lives in `requirements-dev.txt`**, keeping the runtime
   manifest lean.
8. **CI is hermetic and inlined** — it never references
   `scripts/git-hooks/dev-tools/ci.sh`, which is gitignored and absent from a
   GitHub checkout.

## Non-goals

Live scraping of real vendor sites, any database server, authentication, Docker,
deployment infrastructure, and a React implementation.

## Revision history

- 2026-10-06: **Phase A — repo scaffolded and house conventions installed** — Created `~/projects/portfolio-showcase` (`git init -b main`), MIT `LICENSE`, `README.md` stub, `.gitignore` modelled on `algo-trader`/`ai-platform`. Installed `dev-tools` (pinned **v0.2.2**, `557b0fa`): `pre-commit`/`pre-push`/`post-checkout` symlinked under `scripts/git-hooks/`, `core.hooksPath` set. Trimmed `probe_config.yaml` for a NUC-less repo (empty `services`/`timers`, no `ssh` block) with the test command as the single gate shared by the hook and CI. Added `requirements.txt` + `requirements-dev.txt` and a draft `.github/workflows/ci.yml` so the Phase E6 push is meaningful. Wrote the house doc set (`AGENTS.md` ⇄ `.github/copilot-instructions.md`, `PLANBOOK.md`, `CHANGELOG.md`, `SYSTEM_SNAPSHOT.md`, `SESSION_RITUAL.md`), adapted to a no-SSH ritual. Drafted `01_PRICING_SCRAPER_CASE_STUDY.md`. Recorded the seeded-DB decision (not committed) and reserved port 8090. No tests yet — `probe_config.yaml` carries a temporary `[ ! -d tests ]` guard that Phase B removes.
