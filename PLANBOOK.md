# portfolio-showcase — Master Planbook

## Purpose

Single reference for the operating state, decisions, and revision history of the
public pricing-scraper showcase. Companion to `SYSTEM_SNAPSHOT.md` (live state)
and `CHANGELOG.md` (dated change entries).

## Current snapshot

- **Last reconciled:** 2026-10-06 (`main`). **Nothing built yet** —
  Phase A complete, no commits, no `origin` remote, CI not yet exercised.
- **Status:** Scaffold only. `git init` + house conventions. No application code,
  no tests, no `quick-start.sh`.
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
| **B** | Data layer: schema, seed JSON, idempotent scraper, tests | A | ⬜ not started |
| **C** | Dashboard + API: FastAPI, `_is_htmx()`, templates, tests | B | ⬜ not started |
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

## Non-goals

Live scraping of real vendor sites, any database server, authentication, Docker,
deployment infrastructure, and a React implementation.

## Revision history

- 2026-10-06: **Docs — corrected port ownership and de-identified the public docs** — The Phase A wording implied 8000 *and* 8001 were both in use locally; the verified state is that **8000 and 8002** are in use and **8001** is unbound here (reserved elsewhere). `AGENTS.md` (⇄ `.github/copilot-instructions.md`), `SESSION_RITUAL.md` (port table + the `ss -ltnp | grep -E ':(8000|8001|8002|8090)'` check), `SYSTEM_SNAPSHOT.md`, `CHANGELOG.md` and `.gitignore` updated. This entry also removes references to private sibling repositories, internal hostnames and plan-internal labels from every published file, ahead of the repo going public.
- 2026-10-06: **Phase A — repo scaffolded and house conventions installed** — `git init -b main`, MIT `LICENSE`, `README.md` stub, `.gitignore`. Installed the local git hooks (pinned **v0.2.2**): `pre-commit`/`pre-push`/`post-checkout` under `scripts/git-hooks/`, `core.hooksPath` set. Trimmed `probe_config.yaml` for a single-machine app (empty `services`/`timers`, no `ssh` block) with the test command as the single gate shared by the hook and CI. Added `requirements.txt` + `requirements-dev.txt` and a draft `.github/workflows/ci.yml` so the publish step is meaningful. Wrote the house doc set (`AGENTS.md` ⇄ `.github/copilot-instructions.md`, `PLANBOOK.md`, `CHANGELOG.md`, `SYSTEM_SNAPSHOT.md`, `SESSION_RITUAL.md`), adapted to a no-SSH ritual. Drafted `01_PRICING_SCRAPER_CASE_STUDY.md`. Recorded the seeded-DB decision (not committed) and reserved port 8090. No tests yet — `probe_config.yaml` carries a temporary `[ ! -d tests ]` guard that Phase B removes.
