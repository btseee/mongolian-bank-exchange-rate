"""Daily scheduled job runner for bank exchange rate crawling."""

import time

import schedule

from app.config import config
from app.db.database import init_db
from app.services.scraper import ScraperService
from app.utils.logger import logger
from app.utils.playwright_setup import ensure_playwright_browsers


def daily_time_from_cron(cron_expression: str) -> str:
    parts = cron_expression.split()
    if len(parts) != 5 or parts[2:] != ["*", "*", "*"]:
        raise ValueError(
            "CRON_SCHEDULE must be a daily cron expression like '0 9 * * *'"
        )

    minute, hour = int(parts[0]), int(parts[1])
    if not 0 <= minute <= 59 or not 0 <= hour <= 23:
        raise ValueError("CRON_SCHEDULE hour/minute is out of range")

    return f"{hour:02d}:{minute:02d}"


def job():
    logger.info("Starting scheduled crawl")
    try:
        ScraperService().run_all()
        logger.info("Crawl completed")
    except Exception as e:
        logger.error(f"Crawl failed: {e}")


def main():
    ensure_playwright_browsers()
    init_db()

    run_at = daily_time_from_cron(config.CRON_SCHEDULE)
    schedule.every().day.at(run_at).do(job)
    logger.info(f"Scheduled daily crawl job at {run_at}")

    logger.info("Running initial crawl")
    job()

    logger.info("Starting scheduler")
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()
