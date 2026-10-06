#!/usr/bin/env bash
# =============================================================================
# quick-start.sh — from a fresh clone to a running dashboard, in one command.
#
#   ./scripts/quick-start.sh
#
# In order, it will:
#   1. create a repository-root .venv if one is missing;
#   2. install requirements.txt into it — the runtime manifest only, which is
#      everything the dashboard needs to serve requests;
#   3. create and seed pricing-scraper/data/market_data.db if it is missing, by
#      running the idempotent scraper (so re-running this script is safe);
#   4. serve the dashboard on http://127.0.0.1:8090  (Ctrl-C to stop).
#
# The database is generated, never committed — see the case study, §4.2. That is
# deliberate: a fresh clone exercises the real ingestion path instead of trusting
# a committed binary.
#
# Port 8090 is this project's port. Do not move it to 8000 or 8002 (other local
# services) or to 8001 (reserved elsewhere).
#
# Override the interpreter with `PYTHON_BIN=python3.12 ./scripts/quick-start.sh`
# if the default `python3` is not the one you want (Python 3.10+).
# =============================================================================
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

HOST="127.0.0.1"
PORT="8090"
VENV="$REPO_ROOT/.venv"
PYTHON_BIN="${PYTHON_BIN:-python3}"
DB_PATH="$REPO_ROOT/pricing-scraper/data/market_data.db"

say() { printf '\n\033[1;36m==>\033[0m %s\n' "$1"; }

# 1. Virtualenv ---------------------------------------------------------------
if [ -x "$VENV/bin/python" ]; then
  say "Reusing the existing virtualenv at .venv"
else
  say "Creating a virtualenv at .venv with $PYTHON_BIN"
  "$PYTHON_BIN" -m venv "$VENV"
fi

# 2. Runtime dependencies -----------------------------------------------------
say "Installing runtime dependencies (requirements.txt)"
"$VENV/bin/python" -m pip install --quiet --upgrade pip
"$VENV/bin/pip" install --quiet -r "$REPO_ROOT/requirements.txt"

# 3. Database -----------------------------------------------------------------
if [ -f "$DB_PATH" ]; then
  say "Database already present at pricing-scraper/data/market_data.db — skipping the seed"
else
  say "Seeding the database from pricing-scraper/sample_data.json"
  "$VENV/bin/python" "$REPO_ROOT/pricing-scraper/scraper.py"
fi

# 4. Serve --------------------------------------------------------------------
say "Serving the dashboard on http://$HOST:$PORT  — press Ctrl-C to stop"
exec "$VENV/bin/python" -m uvicorn \
  --app-dir "$REPO_ROOT/pricing-dashboard" \
  app:app \
  --host "$HOST" \
  --port "$PORT"
