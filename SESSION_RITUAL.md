# Session Ritual — portfolio-showcase

There is **no remote host** for this repo: no SSH, no systemd, no probing.
Everything runs on the local machine.

## 1. Read the Snapshot

```bash
cat SYSTEM_SNAPSHOT.md
```

## 2. Run the Tests

```bash
cd "$(git rev-parse --show-toplevel)"
.venv/bin/python -m pytest tests/ -q
```

## 3. Check for Drift

Compare what you just ran against `SYSTEM_SNAPSHOT.md` and flag any difference:

- test count / pass-fail
- seeded row counts (competitors, products, pricing rows)
- the dashboard port (must be **8090** — see the port table below)
- whether `pricing-scraper/data/market_data.db` exists and its size

If the suite fails, stop and fix before starting new work.

## 4. Smoke-Check the App

If the dashboard has been built (Phase C onward):

```bash
./scripts/quick-start.sh          # venv → deps → seed DB if absent → uvicorn :8090
curl -s http://127.0.0.1:8090/ | head
curl -s -H 'HX-Request: true' http://127.0.0.1:8090/ | head   # must NOT contain <html>
```

The second command is the fragment check — a fragment must never carry the shell.

## 5. End of Session

1. Run the tests one last time.
2. Update `SYSTEM_SNAPSHOT.md` with what changed.
3. Add a `PLANBOOK.md` revision-history line and a `CHANGELOG.md` entry.
4. Commit.

> **What the pre-commit hook does for you:** refreshes the `**Date:**` line in
> `SYSTEM_SNAPSHOT.md` (and DB size, once the DB exists), then **runs the command
> from `probe_config.yaml` → `tests.command` and blocks the commit if it fails**.
> That is the enforcement layer, so a stale snapshot or a broken test cannot
> reach the repo.

## Ports

| Port | Bound here? | Notes |
|---|---|---|
| 8000 | ✅ yes | another local service |
| 8001 | ✖ no | reserved for a service that runs on a different host |
| 8002 | ✅ yes | another local service |
| **8090** | free | **this repo** — verify it is free before starting |

Check before binding anything:

```bash
ss -ltnp | grep -E ':(8000|8001|8002|8090)'
```

Only 8090 should belong to this repo.

> Do **not** bind anything else on 8090, and do not "borrow" 8001 just because it
> is free here — that port is reserved elsewhere.
