# Local setup

Everything in this repository runs on one machine. There is no server, no
container, no database service, and no network access required at runtime.

> **All pricing data is illustrative.** It was not collected from live vendor
> sites; values are fixed at `data_as_of: 2026-10-01`.

## Prerequisites

- **Python 3.10 or newer** (CI runs 3.12; this repo was developed on 3.12)
- `python3` on your `PATH`

That is the whole list. There is nothing to install globally and nothing to
configure.

## Quick start

```bash
./scripts/quick-start.sh
```

Then open <http://127.0.0.1:8090/>. Press `Ctrl-C` to stop.

The script, in order:

1. creates a repository-root `.venv` if one is missing;
2. installs `requirements.txt` into it — the runtime manifest only;
3. builds `pricing-scraper/data/market_data.db` from `sample_data.json` **if it is
   missing** (the scraper is idempotent, so re-running the script is safe);
4. serves the dashboard with uvicorn on `127.0.0.1:8090`.

## Doing it by hand

`quick-start.sh` is a convenience wrapper around four ordinary commands:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python pricing-scraper/scraper.py          # only if the database is absent
.venv/bin/python -m uvicorn --app-dir pricing-dashboard app:app --port 8090
```

> Note the `--app-dir pricing-dashboard` form. The directory name contains a hyphen,
> so `pricing-dashboard.app:app` is not importable; `--app-dir` puts it on
> `sys.path`, exactly as running the file directly would.

## Ports

The dashboard is fixed at **8090**.

| Port | Notes |
|---|---|
| **8090** | this project |
| 8000, 8002 | intentionally avoided — other local services |
| 8001 | intentionally avoided — reserved elsewhere |

## Tests

```bash
.venv/bin/python -m pytest tests/ -q
```

The suite never touches `pricing-scraper/data/market_data.db`. It creates a
throwaway database in a temporary directory, seeds it from the committed
`sample_data.json`, and points the app at it through `PRICING_DB_PATH` — so the
tests pass even with the real database deleted, which is exactly what CI relies on.

## The notebook

The walkthrough needs the development dependencies, which the quick-start script
deliberately does not install:

```bash
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/jupyter lab notebooks/pricing_walkthrough.ipynb
```

Run-all works from a clean kernel: the notebook locates the repository root itself
and seeds the database if it is missing. To execute it headlessly, exactly as the
build gate does:

```bash
.venv/bin/jupyter nbconvert --to notebook --execute --stdout \
  notebooks/pricing_walkthrough.ipynb > /dev/null
```

## Environment variables

| Variable | Effect |
|---|---|
| `PRICING_DB_PATH` | Overrides the SQLite path the dashboard reads. Defaults to `pricing-scraper/data/market_data.db`. The test suite uses this to stay hermetic. |
| `PYTHON_BIN` | The interpreter `quick-start.sh` uses to create `.venv` (default `python3`). |

## Troubleshooting

**`Address already in use` on 8090.** Something else is on the port — check with
`ss -ltnp | grep :8090`. Free it, or pick another port for a manual uvicorn run,
but keep the dashboard off 8000, 8001 and 8002, which belong to other services.

**The dashboard shows "No data yet".** The database is missing or empty:

```bash
.venv/bin/python pricing-scraper/scraper.py
```

**`ModuleNotFoundError: schema` / `scraper`.** The hyphenated `pricing-scraper/`
directory is not importable as a package. Use the repo's single bootstrap
(`import_paths.py`) instead of hand-rolling a `sys.path` change — see its docstring
for the three-line prologue.

**Charts do not render in the notebook.** Install the development dependencies
(`requirements-dev.txt`); `matplotlib` and `pandas` are deliberately not runtime
dependencies.
