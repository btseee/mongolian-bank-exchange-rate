#!/usr/bin/env python3
"""Backfill historical exchange rate data.

Usage:
    python scripts/backfill.py                  # 2026-01-01 to today
    python scripts/backfill.py 2026-01-01       # From date to today
    python scripts/backfill.py 2026-01-01 2026-01-15  # Date range
"""

import sys
import time
from datetime import date, timedelta

from app.config import config
from app.db.database import init_db
from app.services.scraper import ScraperService
from app.utils.logger import logger
from app.utils.playwright_setup import ensure_playwright_browsers


def parse_date_args(args: list[str]) -> tuple[date, date]:
    start = date(2026, 1, 1)
    end = date.today()

    if len(args) >= 1:
        start = date.fromisoformat(args[0])
    if len(args) >= 2:
        end = date.fromisoformat(args[1])

    if start > end:
        raise ValueError("Start date must be <= end date")

    return start, end


def backfill(start: date, end: date) -> dict:
    total = (end - start).days + 1
    logger.info(f"Backfill: {start} to {end} ({total} days)")

    current = start
    count = 0
    succeeded = 0
    failed = 0
    failed_banks: set[str] = set()
    while current <= end:
        count += 1
        logger.info(f"[{count}/{total}] {current}")
        try:
            result = ScraperService(date=current.isoformat()).run_all()
            succeeded += result["succeeded"]
            failed += result["failed"]
            failed_banks.update(result["failed_banks"])
        except Exception as e:
            logger.error(f"Failed {current}: {e}")

        current += timedelta(days=1)
        if current <= end and config.BACKFILL_DELAY_SECONDS:
            time.sleep(config.BACKFILL_DELAY_SECONDS)

    logger.info(f"Backfill done: {count} days")
    return {
        "days_processed": count,
        "succeeded": succeeded,
        "failed": failed,
        "failed_banks": sorted(failed_banks),
    }


def main():
    try:
        start, end = parse_date_args(sys.argv[1:])
    except ValueError as exc:
        logger.error(str(exc))
        sys.exit(1)

    ensure_playwright_browsers()
    init_db()
    backfill(start, end)


if __name__ == "__main__":
    main()
