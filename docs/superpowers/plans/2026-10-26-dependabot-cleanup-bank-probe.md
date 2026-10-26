# Dependabot Fixes, Cleanup, And Bank Probe Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Clear the 6 open Dependabot alerts, split dev dependencies out of the production image, report which of the 15 bank crawlers return no rates, and fix three audit findings (F1, F3, F8) test-first.

**Architecture:** Five small independent changes to an existing FastAPI service. No new modules except `requirements-dev.txt`. The bank probe is a throwaway script outside the repo that calls each crawler's `crawl()` directly and never touches a database.

**Tech Stack:** Python 3.14, FastAPI, SQLAlchemy 2.0, pytest, black/isort/ruff, Playwright, Docker.

Spec: `docs/superpowers/specs/2026-10-26-dependabot-cleanup-bank-probe-design.md`

## Global Constraints

- Working directory for every command: `D:/Personal documents/mongolian-bank-exchange-rate`. Python is `.venv/Scripts/python.exe` (Python 3.14.7). Shell is Git Bash.
- Line length is 79 (`pyproject.toml`). `target-version` stays `py313` for both black and ruff; do not change it.
- All dependencies are exact-pinned with `==`.
- The four checks, run after every part and before every commit:
  `.venv/Scripts/python.exe -m isort app tests scripts main.py --check-only`
  `.venv/Scripts/python.exe -m black app tests scripts main.py --check`
  `.venv/Scripts/python.exe -m ruff check app tests scripts main.py`
  `.venv/Scripts/python.exe -m pytest -q`
- Baseline before any change: 101 tests pass, 81% coverage, all lint clean.
- Commits are local only. **Never `git push`**: a push to `main` publishes Docker images and redeploys Render.
- Keep `scripts/cron.py`, `schedule`, and the docker-compose `cron` service.
- `.gitignore` has an uncommitted change from the audit tool (`.clean/` appended). Never `git add -A` or `git add .`; add files by exact path.
- Out of scope: F2, F9, and every other audit finding; adding `.github/dependabot.yml`; pushing.

## File Map

| File | Change |
| --- | --- |
| `<scratchpad>/probe_banks.py` | Create (outside repo) |
| `requirements.txt` | Bump pins, then drop dev packages |
| `requirements-dev.txt` | Create |
| `Dockerfile` | Test stage installs dev file; HEALTHCHECK checks status |
| `docker-compose.yml` | HEALTHCHECK checks status |
| `.github/workflows/ci.yml` | `lint-test` installs the dev file |
| `CLAUDE.md`, `CONTRIBUTING.md`, `README.md` | Install commands |
| `.dockerignore` | Exclude `.venv/`, `.ruff_cache/`, `.clean/`, `.serena/` |
| `app/__version__.py` | Remove 3 unused dunders |
| `app/db/repository.py`, `tests/test_repository.py` | F1 |
| `app/services/scraper.py`, `tests/test_scraper_service.py` | F3 |
| `app/api/dependencies.py`, `tests/test_admin_api.py` | F8 |

`<scratchpad>` = `C:/Users/BBadral/AppData/Local/Temp/claude/d--Personal-documents-mongolian-bank-exchange-rate/d8272d5b-3936-4ec8-aa82-5ac6d5b29fa0/scratchpad`

---

### Task 1: Bank probe (Part C, read-only, no commit)

**Files:**
- Create: `<scratchpad>/probe_banks.py`
- Output: `<scratchpad>/probe_results.json`

**Interfaces:**
- Consumes: `app.crawlers.ALL_CRAWLERS`, `app.crawlers.HTTP_CRAWLERS`, each class's `BANK_NAME` and `__call__(date_str).crawl() -> dict[str, CurrencyDetail]`, `app.utils.playwright_setup.ensure_playwright_browsers()`.
- Produces: a per-bank result list. Task 8 quotes it in the final report.

- [ ] **Step 1: Write the probe script**

Create `<scratchpad>/probe_banks.py` with exactly:

```python
"""Read-only probe of every bank crawler. Run from the repo root:

    PYTHONPATH=. .venv/Scripts/python.exe <this file>

Writes nothing to the repo or any database; results go to stdout and to
probe_results.json next to this script.
"""

import json
import os
import time
import traceback
from datetime import date
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app.crawlers import ALL_CRAWLERS, HTTP_CRAWLERS  # noqa: E402
from app.utils.playwright_setup import (  # noqa: E402
    ensure_playwright_browsers,
)

KINDS = ("cash", "noncash")
SIDES = ("buy", "sell")


def problems_in(rates):
    if not rates:
        return ["0 currencies"]
    found = []
    usd = rates.get("usd")
    if usd is None:
        found.append("no usd")
    elif not any(
        getattr(getattr(usd, kind), side) for kind in KINDS for side in SIDES
    ):
        found.append("usd has no rate values")
    for code, detail in rates.items():
        for kind in KINDS:
            for side in SIDES:
                value = getattr(getattr(detail, kind), side)
                if value is not None and value <= 0:
                    found.append(f"{code}.{kind}.{side}={value}")
    return found


def attempt(crawler_cls, day):
    started = time.monotonic()
    try:
        rates = crawler_cls(day).crawl()
    except Exception as exc:
        return {
            "error": f"{type(exc).__name__}: {exc}",
            "trace": traceback.format_exc().splitlines()[-6:],
            "problems": [],
            "currencies": 0,
            "seconds": round(time.monotonic() - started, 1),
        }
    return {
        "error": None,
        "trace": [],
        "problems": problems_in(rates),
        "currencies": len(rates or {}),
        "seconds": round(time.monotonic() - started, 1),
    }


def probe(crawler_cls, day):
    first = attempt(crawler_cls, day)
    final = first
    attempts = 1
    if first["error"] or first["problems"]:
        final = attempt(crawler_cls, day)
        attempts = 2
    if final["error"]:
        status = "ERROR"
    elif final["currencies"] == 0:
        status = "EMPTY"
    elif final["problems"]:
        status = "SUSPECT"
    else:
        status = "OK"
    return {
        "bank": crawler_cls.BANK_NAME,
        "group": "http" if crawler_cls in HTTP_CRAWLERS else "playwright",
        "status": status,
        "attempts": attempts,
        "first_error": first["error"],
        **final,
    }


def main():
    ensure_playwright_browsers()
    day = date.today().isoformat()
    results = []
    for crawler_cls in ALL_CRAWLERS:
        result = probe(crawler_cls, day)
        results.append(result)
        print(
            f"{result['bank']:<14} {result['group']:<10} "
            f"{result['status']:<8} {result['currencies']:>3} currencies "
            f"{result['seconds']:>6}s attempts={result['attempts']}"
        )
        if result["error"]:
            print(f"    error: {result['error']}")
        elif result["first_error"]:
            print(f"    first attempt failed, retry ok: {result['first_error']}")
        for problem in result["problems"]:
            print(f"    problem: {problem}")
    out = Path(__file__).with_name("probe_results.json")
    out.write_text(
        json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    bad = [r["bank"] for r in results if r["status"] != "OK"]
    print(f"\n{len(results) - len(bad)}/{len(results)} OK; not OK: {bad or 'none'}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the probe**

Run (in background; 5 Playwright banks can take up to a minute each, plus retries):

```bash
cd "D:/Personal documents/mongolian-bank-exchange-rate" && PYTHONPATH=. .venv/Scripts/python.exe "C:/Users/BBadral/AppData/Local/Temp/claude/d--Personal-documents-mongolian-bank-exchange-rate/d8272d5b-3936-4ec8-aa82-5ac6d5b29fa0/scratchpad/probe_banks.py"
```

Expected: 15 result lines (HTTP banks first, then TDBM, BogdBank, CKBank, NIBank, TransBank) and a final `N/15 OK; not OK: [...]` line. If every Playwright bank fails with a "Executable doesn't exist" error, run `.venv/Scripts/python.exe -m playwright install chromium` and re-run.

- [ ] **Step 3: Classify each non-OK bank**

For every bank whose status is not `OK`, read its `error`/`problems` in `<scratchpad>/probe_results.json` and label it:
- **network/IP block**: HTTP 403/429, connection reset, timeout, SSL error, or the page never loads.
- **parser break**: HTTP 200 or page loads, but 0 currencies, `KeyError`, `AttributeError`, `TypeError`, no `usd`, or a missing selector.
- **transient**: first attempt failed and the retry succeeded.

Keep the table for Task 8. Fix nothing. No commit (the script lives outside the repo).

- [ ] **Step 4: Confirm the repo is untouched**

Run: `git status --short`
Expected: only ` M .gitignore`.

---

### Task 2: Dependabot bumps (Part A)

**Files:**
- Modify: `requirements.txt` (lines `black==26.5.1`, `httpx2==2.9.1`)

**Interfaces:**
- Produces: `black==26.10.1` and `httpx2==2.16.0` pinned in `requirements.txt` (Task 3 moves both lines to `requirements-dev.txt`).

- [ ] **Step 1: Install the new versions in the venv**

Run:
```bash
.venv/Scripts/python.exe -m pip install httpx2==2.16.0 black==26.10.1 && .venv/Scripts/python.exe -m pip check
```
Expected: both install; `pip check` prints `No broken requirements found.` If pip reports a conflict, stop and report it; do not loosen any other pin.

- [ ] **Step 2: Update the pins**

In `requirements.txt` change `black==26.5.1` to `black==26.10.1` and `httpx2==2.9.1  # starlette.testclient prefers this over httpx, avoids a deprecation warning` to `httpx2==2.16.0  # starlette.testclient prefers this over httpx, avoids a deprecation warning`.

- [ ] **Step 3: Run the four checks**

Run the four checks from Global Constraints.
Expected: isort clean, ruff clean, pytest `101 passed`. Black may report files it would reformat; if it does, go to Step 4, otherwise skip to Step 5.

- [ ] **Step 4 (only if black failed): Reformat and inspect**

Run:
```bash
.venv/Scripts/python.exe -m black app tests scripts main.py && git diff --stat && git diff | grep -nE "^\+\s*except [A-Za-z_.]+, "
```
Expected: the grep prints nothing. A hit means black 26.10.1 rewrote an `except (A, B):` into the 3.14-only unparenthesized form. If that happens, undo with `git checkout -- app tests scripts main.py`, and report: do not change `target-version` yourself.

- [ ] **Step 5: Check the testclient and warnings**

Run:
```bash
.venv/Scripts/python.exe -c "import httpx2, black; print(httpx2.__version__, black.__version__)" && .venv/Scripts/python.exe -m pytest -q 2>&1 | tail -8
```
Expected: `2.16.0 26.10.1`, and the pytest tail shows `101 passed` with no `warnings summary` block.

- [ ] **Step 6: Commit the bump**

```bash
git add requirements.txt
git commit -m "security: bump httpx2 to 2.16.0 and black to 26.10.1 (Dependabot #8-#13)"
```

- [ ] **Step 7 (only if Step 4 ran): Commit the reformat separately**

```bash
git add app tests scripts main.py
git commit -m "style: reformat with black 26.10.1"
```

---

### Task 3: Split dev dependencies out of the production image (Part B, items 1-3)

**Files:**
- Modify: `requirements.txt`, `Dockerfile` (Test Stage), `.github/workflows/ci.yml` (lint-test install step), `CLAUDE.md`, `CONTRIBUTING.md`, `README.md`
- Create: `requirements-dev.txt`

**Interfaces:**
- Consumes: the pins from Task 2.
- Produces: `requirements.txt` = runtime only; `requirements-dev.txt` = `-r requirements.txt` + lint/test tools. Task 4's Docker verification depends on the Dockerfile `test` stage installing the dev file.

- [ ] **Step 1: Write `requirements-dev.txt`**

Create `requirements-dev.txt`:

```
-r requirements.txt

# Lint / format
black==26.10.1
isort==5.13.2
ruff==0.16.0

# Testing
pytest==9.1.1
pytest-cov==7.1.0
httpx2==2.16.0  # starlette.testclient prefers this over httpx, avoids a deprecation warning
```

- [ ] **Step 2: Reduce `requirements.txt` to runtime packages**

Overwrite `requirements.txt` with:

```
# Web Framework
fastapi==0.136.3
uvicorn[standard]==0.48.0
pydantic==2.13.4

# Database
sqlalchemy==2.0.51
psycopg[binary]==3.3.4

# Configuration
python-dotenv==1.2.2

# Scheduling
schedule==1.2.2

# HTTP
requests==2.34.2
httpx==0.28.1

# Web scraping
playwright==1.61.0
lxml==6.1.1
```

- [ ] **Step 3: Install the dev file in the venv and run the four checks**

Run: `.venv/Scripts/python.exe -m pip install -r requirements-dev.txt`
Expected: `Requirement already satisfied` for everything, no changes.
Then run the four checks. Expected: all clean, `101 passed`.

- [ ] **Step 4: Dockerfile test stage**

In `Dockerfile`, replace:

```
FROM base AS test
RUN pytest --cov=app --cov-report=term-missing -v
```

with:

```
FROM base AS test
RUN pip install --no-cache-dir -r requirements-dev.txt
RUN pytest --cov=app --cov-report=term-missing -v
```

(`requirements-dev.txt` is already inside the image because `COPY . .` runs in the `base` stage and `.dockerignore` does not exclude it.)

- [ ] **Step 5: CI install step**

In `.github/workflows/ci.yml`, in the `lint-test` job replace:

```
          python-version-file: ".python-version"
          cache: "pip"
```

with:

```
          python-version-file: ".python-version"
          cache: "pip"
          cache-dependency-path: |
            requirements.txt
            requirements-dev.txt
```

and replace `          pip install -r requirements.txt` with `          pip install -r requirements-dev.txt`. Leave the `docker-test`, `publish` and `release` jobs unchanged.

- [ ] **Step 6: Docs**

- `CLAUDE.md`: replace `pip install -r requirements.txt\npython -m playwright install chromium` (the Local dev block) with `pip install -r requirements-dev.txt   # runtime + black/isort/ruff/pytest\npython -m playwright install chromium`. Replace ``exact-pinned (`==`) in `requirements.txt`, not floor-pinned.`` with ``exact-pinned (`==`) in `requirements.txt` (runtime) and `requirements-dev.txt` (lint/test, includes the runtime file), not floor-pinned.``
- `CONTRIBUTING.md`: replace `python -m pip install -r requirements.txt\npython -m playwright install chromium` with `python -m pip install -r requirements-dev.txt\npython -m playwright install chromium`.
- `README.md`: in the "Хөгжүүлэгчийн Шалгалт" code block, put this line first, before the `isort ...` line: `python -m pip install -r requirements-dev.txt   # black, isort, ruff, pytest`. Leave the Quick Start `requirements.txt` line as is (runtime only).

- [ ] **Step 7: Verify nothing else still installs the old single file**

Run: `grep -rn "requirements" --include=*.md --include=*.yml --include=Dockerfile --include=*.txt . --exclude-dir=.venv --exclude-dir=.clean --exclude-dir=docs`
Expected: every `pip install` line uses `requirements-dev.txt` except `Dockerfile`'s base stage and README's Quick Start.

- [ ] **Step 8: Commit**

```bash
git add requirements.txt requirements-dev.txt Dockerfile .github/workflows/ci.yml CLAUDE.md CONTRIBUTING.md README.md
git commit -m "build: split dev dependencies into requirements-dev.txt"
```

---

### Task 4: Docker hygiene and unused code (Part B, items 4-6)

**Files:**
- Modify: `.dockerignore`, `Dockerfile` (HEALTHCHECK), `docker-compose.yml` (api healthcheck), `app/__version__.py`

**Interfaces:**
- Consumes: the Task 3 Dockerfile (`test` stage installs the dev file).
- Produces: a verified production image without dev tools and a healthcheck that fails on 4xx/5xx.

- [ ] **Step 1: `.dockerignore`**

Make these three edits:
1. Replace `# Virtual Environment\nvenv/\nENV/\nenv/` with `# Virtual Environment\n.venv/\nvenv/\nENV/\nenv/`.
2. Replace `# Testing\n.pytest_cache/` with `# Testing\n.pytest_cache/\n.ruff_cache/`.
3. Replace `# OS\n.DS_Store` with `# Local tooling state\n.clean/\n.serena/\n\n# OS\n.DS_Store`.

- [ ] **Step 2: HEALTHCHECK status check**

In `Dockerfile` replace the line

```
    CMD ["python", "-c", "import requests; requests.get('http://localhost:8000/api/health', timeout=5)"]
```

with

```
    CMD ["python", "-c", "import requests; requests.get('http://localhost:8000/api/health', timeout=5).raise_for_status()"]
```

In `docker-compose.yml` (the `api` service healthcheck) replace `"import requests; requests.get('http://localhost:8000/api/health', timeout=5)",` with `"import requests; requests.get('http://localhost:8000/api/health', timeout=5).raise_for_status()",`.

- [ ] **Step 3: Remove the three unused dunders**

First confirm they are unused: `grep -rn "__title__\|__description__\|__author_email__" --include=*.py . --exclude-dir=.venv`
Expected: only the three definitions in `app/__version__.py`. Then delete those three lines from `app/__version__.py`. The file must end up as:

```python
__version__ = "1.1.0"
__author__ = "Battseren Badral"
__url__ = "https://btseee.github.io"
__license__ = "MIT"
__donation__ = "https://buymeacoffee.com/btseee"
```

- [ ] **Step 4: Run the four checks**

Expected: all clean, `101 passed`.

- [ ] **Step 5: Build and inspect the Docker images**

Run (each build downloads Chromium and system packages; allow several minutes, run in background):

```bash
docker build --target test -t mber-test . && docker build --target production -t mber-prod .
```

Expected: the test build ends with the pytest summary `101 passed` and both builds succeed.

Then run:

```bash
docker run --rm mber-prod python -c "import fastapi, playwright, lxml, httpx, requests; print('runtime ok')"
docker run --rm mber-prod python -c "import black"
docker run --rm mber-prod python -c "import pytest"
```

Expected: `runtime ok`, then two `ModuleNotFoundError` lines (`No module named 'black'`, `No module named 'pytest'`).

- [ ] **Step 6: Verify the healthcheck command fails on a bad status**

Run:

```bash
docker run -d --name mber-hc mber-prod
sleep 12
docker exec mber-hc python -c "import requests; requests.get('http://localhost:8000/api/health', timeout=5).raise_for_status()"; echo "health exit=$?"
docker exec mber-hc python -c "import requests; requests.get('http://localhost:8000/api/does-not-exist', timeout=5).raise_for_status()"; echo "bad-path exit=$?"
docker rm -f mber-hc
```

Expected: `health exit=0` and `bad-path exit=1` (an `HTTPError ... 404` traceback is fine). Validate the compose file: `docker compose -f docker-compose.yml config > /dev/null && echo compose ok`. Expected: `compose ok`.

- [ ] **Step 7: Remove the images this task built**

```bash
docker image rm mber-test mber-prod
```

- [ ] **Step 8: Commit**

```bash
git add .dockerignore Dockerfile docker-compose.yml app/__version__.py
git commit -m "chore: exclude .venv from Docker context, fail healthcheck on bad status, drop unused version metadata"
```

---

### Task 5: Fix F1 - rank rates by date, not by write time (Part D)

**Files:**
- Modify: `app/db/repository.py` (`get_all_rates`, `get_rates_by_bank`, `get_latest_rates`)
- Test: `tests/test_repository.py`

**Interfaces:**
- Consumes: existing `repository.save_rates(db, ExchangeRate)`, the `test_db` fixture, and the `_rate(bank, day, value)` helper in `tests/test_repository.py`.
- Produces: unchanged function signatures; `get_latest_rates(db) -> List[CurrencyRate]` now returns each bank's row with the greatest `date`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_repository.py` (the file already imports `date` and `repository`):

```python


class TestDateOrdering:
    """Rows are ranked by rate date, not by when they were written - a
    backfill of an older date must not displace the newest rate."""

    def test_latest_ignores_write_order(self, test_db):
        repository.save_rates(test_db, _rate("KhanBank", "2026-10-26", 100))
        repository.save_rates(test_db, _rate("KhanBank", "2026-01-15", 200))

        latest = repository.get_latest_rates(test_db)

        assert [(r.bank_name, r.date) for r in latest] == [
            ("KhanBank", date(2026, 10, 26))
        ]

    def test_latest_is_per_bank(self, test_db):
        repository.save_rates(test_db, _rate("KhanBank", "2026-10-26", 100))
        repository.save_rates(test_db, _rate("GolomtBank", "2026-10-20", 100))
        repository.save_rates(test_db, _rate("GolomtBank", "2026-10-10", 100))

        latest = repository.get_latest_rates(test_db)

        assert {(r.bank_name, r.date) for r in latest} == {
            ("KhanBank", date(2026, 10, 26)),
            ("GolomtBank", date(2026, 10, 20)),
        }

    def test_bank_list_is_newest_date_first(self, test_db):
        repository.save_rates(test_db, _rate("KhanBank", "2026-10-26", 100))
        repository.save_rates(test_db, _rate("KhanBank", "2026-01-15", 100))

        rows = repository.get_rates_by_bank(test_db, "KhanBank")

        assert [r.date for r in rows] == [
            date(2026, 10, 26),
            date(2026, 1, 15),
        ]

    def test_all_rates_list_is_newest_date_first(self, test_db):
        repository.save_rates(test_db, _rate("KhanBank", "2026-10-26", 100))
        repository.save_rates(test_db, _rate("KhanBank", "2026-01-15", 100))

        rows = repository.get_all_rates(test_db)

        assert [r.date for r in rows] == [
            date(2026, 10, 26),
            date(2026, 1, 15),
        ]
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv/Scripts/python.exe -m pytest tests/test_repository.py::TestDateOrdering -v`
Expected: `test_latest_ignores_write_order`, `test_bank_list_is_newest_date_first` and `test_all_rates_list_is_newest_date_first` FAIL (the older date comes back first). `test_latest_is_per_bank` may pass or fail; that is fine.

- [ ] **Step 3: Implement**

In `app/db/repository.py`, replace the body of `get_all_rates`:

```python
def get_all_rates(
    db: Session, skip: int = 0, limit: int = 100
) -> List[CurrencyRate]:
    return (
        db.query(CurrencyRate)
        .order_by(CurrencyRate.date.desc(), CurrencyRate.timestamp.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
```

replace `get_rates_by_bank`:

```python
def get_rates_by_bank(
    db: Session, bank_name: str, skip: int = 0, limit: int = 100
) -> List[CurrencyRate]:
    return (
        db.query(CurrencyRate)
        .filter(CurrencyRate.bank_name == bank_name)
        .order_by(CurrencyRate.date.desc(), CurrencyRate.timestamp.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
```

and replace `get_latest_rates`:

```python
def get_latest_rates(db: Session) -> List[CurrencyRate]:
    subq = (
        db.query(
            CurrencyRate.bank_name,
            func.max(CurrencyRate.date).label("max_date"),
        )
        .group_by(CurrencyRate.bank_name)
        .subquery()
    )

    return (
        db.query(CurrencyRate)
        .join(
            subq,
            (CurrencyRate.bank_name == subq.c.bank_name)
            & (CurrencyRate.date == subq.c.max_date),
        )
        .all()
    )
```

Leave `get_rates_by_date` unchanged (every row has the same date there).

- [ ] **Step 4: Run the new tests and the whole suite**

Run: `.venv/Scripts/python.exe -m pytest tests/test_repository.py tests/test_api.py -v`
Expected: all PASS, including the existing `test_get_latest_rates`. Then run the four checks. Expected: `105 passed`.

- [ ] **Step 5: Commit**

```bash
git add app/db/repository.py tests/test_repository.py
git commit -m "fix: rank rates by date so /latest ignores backfill write order"
```

---

### Task 6: Fix F3 - a bank that parses to zero currencies is a failure (Part D)

**Files:**
- Modify: `app/services/scraper.py` (`ScraperService._execute`)
- Test: `tests/test_scraper_service.py`

**Interfaces:**
- Consumes: `ScraperService(date=...)`, `_execute(crawler_cls) -> Tuple[str, Optional[Dict], Optional[Exception]]`, `run_all() -> {"succeeded", "failed", "failed_banks"}`, `_retry_failed`.
- Produces: `_execute` returns `(bank_name, None, RuntimeError(...))` when a crawler returns an empty result, so `run_all` counts it under `failed`/`failed_banks`, `_retry_failed` retries it, and `_save` skips it. The error message contains `0 currencies`.

- [ ] **Step 1: Write the failing tests**

In `tests/test_scraper_service.py`, add this class right after the `from app.services.scraper import ScraperService` import line:

```python


class _EmptyCrawler:
    BANK_NAME = "EmptyBank"

    def __init__(self, date):
        self.date = date

    def crawl(self):
        return {}
```

Inside `class TestScraperService`, directly after `test_execute_failure`, add:

```python
    def test_execute_treats_zero_currencies_as_failure(self):
        service = ScraperService()

        bank, rates, error = service._execute(_EmptyCrawler)

        assert bank == "EmptyBank"
        assert rates is None
        assert isinstance(error, RuntimeError)
        assert "0 currencies" in str(error)

    @patch("app.services.scraper.config")
    def test_run_all_reports_empty_bank_as_failed(self, mock_config):
        mock_config.ENABLE_PARALLEL = False
        service = ScraperService(date="2026-01-15")

        with (
            patch("app.services.scraper.HTTP_CRAWLERS", [_EmptyCrawler]),
            patch("app.services.scraper.PLAYWRIGHT_CRAWLERS", []),
            patch.object(service, "_save") as mock_save,
        ):
            summary = service.run_all()

        assert summary == {
            "succeeded": 0,
            "failed": 1,
            "failed_banks": ["EmptyBank"],
        }
        mock_save.assert_called_once()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv/Scripts/python.exe -m pytest tests/test_scraper_service.py -k "zero_currencies or empty_bank" -v`
Expected: both FAIL (`rates is None` assertion fails because `_execute` returns `{}`; the summary shows `failed: 0`).

- [ ] **Step 3: Implement**

In `app/services/scraper.py`, replace the body of `_execute` from `try:` through the `return bank_name, rates, None` with:

```python
        try:
            crawler = crawler_cls(self.date)
            rates = crawler.crawl()
            if not rates:
                raise RuntimeError(
                    "crawled 0 currencies - possible parsing break or "
                    "upstream change"
                )
            logger.info(f"{bank_name}: crawled {len(rates)} currencies")
            return bank_name, rates, None
        except Exception as e:
            logger.error(f"{bank_name}: crawl failed - {e}")
            return bank_name, None, e
```

so the whole method reads:

```python
    def _execute(
        self, crawler_cls
    ) -> Tuple[str, Optional[Dict], Optional[Exception]]:
        bank_name = crawler_cls.BANK_NAME
        try:
            crawler = crawler_cls(self.date)
            rates = crawler.crawl()
            if not rates:
                raise RuntimeError(
                    "crawled 0 currencies - possible parsing break or "
                    "upstream change"
                )
            logger.info(f"{bank_name}: crawled {len(rates)} currencies")
            return bank_name, rates, None
        except Exception as e:
            logger.error(f"{bank_name}: crawl failed - {e}")
            return bank_name, None, e
```

(The old `count`/`warning` branch and its separate `except` are removed.)

- [ ] **Step 4: Run the new tests and the whole suite**

Run: `.venv/Scripts/python.exe -m pytest tests/test_scraper_service.py -v`
Expected: all PASS. Then run the four checks. Expected: `107 passed`.

- [ ] **Step 5: Commit**

```bash
git add app/services/scraper.py tests/test_scraper_service.py
git commit -m "fix: count a bank that parses to zero currencies as failed and retry it"
```

---

### Task 7: Fix F8 - non-ASCII admin key returns 401, not 500 (Part D)

**Files:**
- Modify: `app/api/dependencies.py` (`require_admin_key`)
- Test: `tests/test_admin_api.py` (`TestAdminAuth`)

**Interfaces:**
- Consumes: the `client` fixture and the module constant `ADMIN_KEY = "test-admin-secret"` in `tests/test_admin_api.py`.
- Produces: unchanged function signature; a non-ASCII header value now yields HTTP 401.

- [ ] **Step 1: Write the failing test**

In `tests/test_admin_api.py`, inside `class TestAdminAuth` directly after `test_401_when_key_wrong`, add:

```python
    def test_401_when_key_is_non_ascii(self, client, monkeypatch):
        monkeypatch.setattr(config, "ADMIN_API_KEY", ADMIN_KEY)
        response = client.post(
            "/api/admin/crawl",
            headers={"X-Admin-Key": "caf\u00e9".encode("latin-1")},
        )
        assert response.status_code == 401
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `.venv/Scripts/python.exe -m pytest tests/test_admin_api.py::TestAdminAuth::test_401_when_key_is_non_ascii -v`
Expected: FAIL with `TypeError: comparing strings with non-ASCII characters is not supported`.

- [ ] **Step 3: Implement**

In `app/api/dependencies.py` replace:

```python
    key_matches = api_key and secrets.compare_digest(
        api_key, config.ADMIN_API_KEY
    )
```

with:

```python
    key_matches = api_key and secrets.compare_digest(
        api_key.encode(), config.ADMIN_API_KEY.encode()
    )
```

- [ ] **Step 4: Run the new test and the whole suite**

Run: `.venv/Scripts/python.exe -m pytest tests/test_admin_api.py -v`
Expected: all PASS. Then run the four checks. Expected: `108 passed`.

- [ ] **Step 5: Commit**

```bash
git add app/api/dependencies.py tests/test_admin_api.py
git commit -m "fix: return 401 instead of 500 for a non-ASCII X-Admin-Key"
```

---

### Task 8: Final verification and report

**Files:**
- Modify: `.clean/ledger.md` (gitignored; tick the finished batches)

- [ ] **Step 1: Full check sequence on the final tree**

Run the four checks plus `.venv/Scripts/python.exe -m pytest --cov=app -q 2>&1 | tail -5`.
Expected: isort/black/ruff clean, `108 passed`, total coverage at or above the 81% baseline.

- [ ] **Step 2: Confirm the commit history and that nothing was pushed**

Run: `git log --oneline -9 && git status --short && git branch -vv | head -3`
Expected: the new commits (bump, optional reformat, build split, chore, three fixes) on top of `f57992d`; `git status` shows only ` M .gitignore`; the branch shows it is ahead of `origin/main`.

- [ ] **Step 3: Update the ledger**

In `.clean/ledger.md` tick `B1`, `B2`, `B3` and refactor batch `1` (safety), and note the date.

- [ ] **Step 4: Report to the user**

The final message must include: (a) the probe table from Task 1 with each non-OK bank classified; (b) which commits were created and that nothing is pushed; (c) the verification numbers; (d) the two follow-ups that need the user: pushing triggers Docker image publish and a Render redeploy, and after a push check whether GitHub's dependency graph detects `requirements-dev.txt` (add `.github/dependabot.yml` if it does not); (e) that F2 (backfill wrong-dated rows) can now be scoped using the probe result.

---

## Self-Review

**Spec coverage:** Part A -> Task 2. Part B items 1-3 -> Task 3, items 4-6 -> Task 4 (item 7, the dead-code scan, was already done during the audit and produced no removals). Part C -> Task 1. Part D B1 -> Task 5, B2 -> Task 6, B3 -> Task 7. Spec "Verification" -> the four checks in every task, the Docker builds in Task 4, the totals in Task 8. Spec "Order" is C, A, B, D = Tasks 1, 2, 3-4, 5-7. No gaps.

**Placeholder scan:** every step has the exact file content, edit text, command and expected output.

**Consistency:** test counts: baseline 101; Task 5 adds 4 (105); Task 6 adds 2 (107); Task 7 adds 1 (108). `_rate`, `ADMIN_KEY`, `_EmptyCrawler` and `EmptyBank` are used consistently. `black==26.10.1`, `httpx2==2.16.0` match across Tasks 2 and 3.
