# CLAUDE.md

Guidance for Claude Code (or any agent) working in this repo.

## What this is

FastAPI service that crawls exchange rates from 15 Mongolian banks, stores them, and serves
them over a REST API. Deployed as a Docker web service on Render's free tier.

## Architecture

- `app/crawlers/` — one class per bank, extends `BaseCrawler` (plain `requests`, session with
  retry/backoff) or `PlaywrightCrawler` (headless Chromium, for JS-rendered sites). Registered
  in `app/crawlers/__init__.py` under `HTTP_CRAWLERS`/`PLAYWRIGHT_CRAWLERS` — that grouping
  controls which worker pool and concurrency limit a crawler runs under, so misclassifying a
  crawler (e.g. a `requests`-based one under `PLAYWRIGHT_CRAWLERS`) silently throttles it.
- `app/services/scraper.py` — runs crawlers in parallel per group, persists results, returns a
  `{"succeeded", "failed", "failed_banks"}` summary. `app/services/admin_jobs.py` — in-process
  `threading.Lock` + state dict backing the admin endpoints; only correct for a single Uvicorn
  process (no `--workers` flag — check `Dockerfile`'s `CMD` before changing that).
- `app/api/` — `api.py` wires the FastAPI app (middleware, lifespan) only; handlers live in
  `app/api/routers/` (`system`, `rates`, `admin`). Shared enums/deps in `app/api/dependencies.py`.
  Swagger UI is mounted at `/` (`docs_url="/"`); every real endpoint is under `/api/`.
- `app/db/repository.py` — `save_rates()` is a dialect-dispatched atomic upsert
  (`postgresql.insert`/`sqlite.insert` + `on_conflict_do_update`) keyed on the
  `(bank_name, date)` unique constraint in `app/models/currency.py`. Don't revert this to
  check-then-act — it exists specifically to make concurrent crawls (scheduled + admin-triggered)
  race-safe.
- `scripts/backfill.py` / `scripts/cron.py` — CLI entry points, also reused directly by
  `app/services/admin_jobs.py` for the HTTP-triggered equivalents (Render's free tier has no
  worker/cron process type, only `web`).

## Local dev

```bash
python -m venv .venv && .venv\Scripts\activate      # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium

isort app tests scripts main.py --check-only && black app tests scripts main.py --check
ruff check app tests scripts main.py
pytest
```

## Conventions and gotchas

- **Line length is 79** (`pyproject.toml`), not black's default 88. Wrap accordingly.
- `[tool.black]`/`[tool.ruff]` `target-version` is pinned to **`py313`**, even though the
  Dockerfile/`.python-version`/CI actually run **Python 3.14**. This is deliberate: Black 26.5.1
  targeting `py314` rewrites `except (A, B):` into the new unparenthesized PEP 758 syntax, which
  is 3.14-only grammar sugar we don't want forced onto every except clause. Don't "fix" this by
  bumping target-version back to py314 without re-checking that bug is gone.
- No Alembic. Schema changes go through `app/db/database.py`'s idempotent
  `CREATE UNIQUE INDEX IF NOT EXISTS` self-heal on startup — single table, hobby scale, not
  worth a migration framework yet.
- No task queue/Redis. Admin job concurrency is a single in-process lock; don't add
  multi-worker/multi-replica support without redesigning that first.
- All dependencies are exact-pinned (`==`) in `requirements.txt`, not floor-pinned. Bump
  deliberately, and re-run the full local check sequence above after any bump — pytest 8→9 and
  similar majors have broken things silently before.
- Admin endpoints (`/api/admin/*`) require `X-Admin-Key` header, checked against
  `ADMIN_API_KEY` (empty means the feature is off, returns 503 — never "open").
- `render.yaml` deliberately omits `DATABASE_URL` — Render's free tier has no persistent disk,
  so the SQLite default is ephemeral there; a real deployment needs an external Postgres
  connection string set manually in the dashboard.

## Release process

- Every push to `main` publishes `ghcr.io/btseee/mongolian-bank-exchange-rate:v{version}` +
  `:latest` via the `publish` job in `ci.yml`, where `{version}` is read from
  `app/__version__.py` (not the git ref) — deliberate: the same two tags get overwritten in
  place on every push, so no `edge`/`sha-*` images pile up between releases. A new image tag
  only appears once `__version__.py` is actually bumped. This is separate from Render, which
  builds its own image straight from the Dockerfile on every push (`render.yaml`'s
  `autoDeploy: true`) — Render never pulls from ghcr.io.
- To cut a versioned release: update `CHANGELOG.md`, bump `app/__version__.py`, then push a
  `vX.Y.Z` tag matching the new version. CI publishes the new `vX.Y.Z` + `latest` images and
  creates a GitHub Release (title is just `${{ github.ref_name }}`, e.g. `v1.1.0` — keep it that
  plain, no descriptive suffix, to match every prior release).
- `generate_release_notes: true` produces an empty body when there were no PRs merged (this
  repo pushes straight to `main`) — write real notes from the CHANGELOG entry and
  `gh release edit vX.Y.Z --notes-file ...` afterward if that happens.

## Before committing

Run the full check sequence (isort, black, ruff, pytest) — CI enforces all four and will fail
the build otherwise. After touching `.github/workflows/*.yml`, check CodeQL's workflow-scanning
rules (`Settings > Code security > Code scanning`) — every job needs an explicit `permissions:`
block at the minimum scope it actually needs (`{}` if it doesn't touch the repo/token at all).
