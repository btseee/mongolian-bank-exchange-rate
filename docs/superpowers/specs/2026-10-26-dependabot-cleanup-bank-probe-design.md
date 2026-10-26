# Dependabot fixes, cleanup, and bank probe - design

Date: 2026-10-26   Baseline commit: 73b1db8

## Goal

1. Clear the 6 open Dependabot alerts and remove unused packages and code.
2. Run all 15 bank crawlers once and report which return no exchange rates.
3. Fix the three small audit findings (F1, F3, F8) that make bank results and public API data wrong.

The audit (`.clean/ledger.md`, F1-F28) is the source for finding IDs. Everything not listed under "In scope" is out of scope.

## Decisions already made

- Cleanup is conservative: keep `scripts/cron.py`, `schedule`, and the docker-compose `cron` service (documented self-host path). Remove only what a static scan proves unused.
- The bank probe runs locally and is read-only: no DB writes, no admin key, no Render.
- Layering stays framework-first (no `.clean/architecture.md`).
- Local commits per part after the four checks pass (part D: one per fix). Nothing is pushed: a push to `main` publishes images and redeploys Render.

## In scope

### A. Dependabot alerts

| Package | From | To | Alerts |
| --- | --- | --- | --- |
| httpx2 | 2.9.1 | 2.16.0 | #8 #9 #10 #11 #12 (fixed in >= 2.12.0) |
| black | 26.5.1 | 26.10.1 | #13 (fixed in >= 26.10.1) |

- Keep `target-version = ["py313"]` in `pyproject.toml` (CLAUDE.md: black targeting py314 rewrites `except (A, B):`). After the bump, confirm black still leaves those clauses alone.
- If black 26.10.1 reformats files, that goes in its own commit, separate from the version bump.
- After the bump, run the full check sequence and check that `starlette.testclient` still prefers `httpx2` without a deprecation warning.

### B. Cleanup (conservative)

1. Split dependencies. `requirements.txt` keeps runtime packages only: fastapi, uvicorn[standard], pydantic, sqlalchemy, psycopg[binary], python-dotenv, schedule, requests, httpx, playwright, lxml. New `requirements-dev.txt` starts with `-r requirements.txt` and adds black, isort, ruff, pytest, pytest-cov, httpx2.
2. `Dockerfile`: the `base` stage installs `requirements.txt` only. The `test` stage also installs `requirements-dev.txt`. The production stage no longer ships dev tools. CI `lint-test` installs `requirements-dev.txt`.
3. Update install commands in CLAUDE.md, CONTRIBUTING.md and README.md.
4. `.dockerignore`: add `.venv/`, `.clean/`, `.serena/`, `.ruff_cache/` (F13).
5. HEALTHCHECK in `Dockerfile` and `docker-compose.yml`: call `raise_for_status()` so a 5xx fails the check (F14).
6. Remove `__title__`, `__description__`, `__author_email__` from `app/__version__.py` (no references anywhere; F24).
7. Dead-code scan: ruff F401/F841 and vulture were already run. Vulture's hits in `app` are false positives (route decorators, ORM columns, Pydantic config). No orphaned module exists, so nothing else is removed.

Risk: GitHub may not scan `requirements-dev.txt`, which would hide dev-dependency alerts. After a push, check the dependency graph. If the file is not detected, add `.github/dependabot.yml`. This is a note for later, not part of this change.

### C. Bank probe

- Throwaway script in the scratchpad, not in the repo.
- Loops `ALL_CRAWLERS` sequentially, so Chromium never overlaps another crawler. For each: `crawler(today).crawl()`, record seconds, currency count, exact error.
- A bank that fails is retried once, to separate transient from persistent failure.
- Flagged as bad: exception, 0 currencies, no `usd`, or any zero/negative buy or sell value.
- Output: a per-bank list (OK / EMPTY / ERROR with the reason, parser break vs network/IP block) reported in chat.
- The probe fixes nothing. Fixing a failing bank is a separate request.
- Local results can differ from Render (Singapore) if a bank blocks by IP; the report says so where relevant.

### D. Bug-fix lane (each: failing test first, then the fix)

- **B1 / F1** `app/db/repository.py`: order `get_all_rates` and `get_rates_by_bank` by `date desc, timestamp desc`. `get_latest_rates` picks each bank's row with the greatest `date` (the `(bank_name, date)` unique constraint makes that one row). Test: save a newer date, then an older date; `/latest` and the list must still return the newer one.
- **B2 / F3** `app/services/scraper.py`: `_execute` returns an error for a crawler that parses 0 currencies, so the summary counts it as failed, `_retry_failed` retries it, and `_save` skips it. Test: a crawler returning `{}` appears in `failed_banks`.
- **B3 / F8** `app/api/dependencies.py`: compare `api_key` and `ADMIN_API_KEY` as UTF-8 bytes in `secrets.compare_digest`. Test: a non-ASCII `X-Admin-Key` returns 401, not 500.

## Out of scope

F2 (backfill wrong-dated rows) and F9 (timeout units) wait for the probe result and a separate request. F4-F7, F10-F12, F15-F28 stay in the ledger as findings. Dependabot version-update config is not added.

## Verification

After each part: `isort app tests scripts main.py --check-only`, `black app tests scripts main.py --check`, `ruff check app tests scripts main.py`, `pytest`, compared with the baseline (101 passed, 81% coverage). After part B, build the Docker `test` and production targets, because Docker is installed locally.

## Order

1. Part C, the probe (read-only baseline; its result also informs F2 and F3).
2. Part A, then the reformat commit if black needs one.
3. Part B.
4. Part D: fixes B1, B2, B3, one commit each.
