"""Scraper service for crawling bank exchange rates."""

import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Tuple

from app.config import config
from app.crawlers import CRAWLER_MAP, HTTP_CRAWLERS, PLAYWRIGHT_CRAWLERS
from app.db import repository
from app.db.database import SessionLocal
from app.models.exchange_rate import CurrencyDetail, ExchangeRate
from app.utils.logger import logger


class ScraperService:
    def __init__(self, date: Optional[str] = None):
        self.date = date or datetime.date.today().isoformat()

    def run_all(self):
        logger.info(f"Starting crawl on {self.date}")

        results = []
        if config.ENABLE_PARALLEL:
            with ThreadPoolExecutor(max_workers=2) as executor:
                futures = [
                    executor.submit(
                        self._run_group, HTTP_CRAWLERS, config.MAX_WORKERS
                    ),
                    executor.submit(
                        self._run_group,
                        PLAYWRIGHT_CRAWLERS,
                        config.PLAYWRIGHT_MAX_WORKERS,
                    ),
                ]
                for f in as_completed(futures):
                    results.extend(f.result())
        else:
            for crawler_cls in HTTP_CRAWLERS + PLAYWRIGHT_CRAWLERS:
                results.append(self._execute(crawler_cls))

        self._save(results)

        success = len([r for r in results if r[1]])
        failed = len([r for r in results if r[2]])
        logger.info(f"Crawl completed: {success} succeeded, {failed} failed")

        return {
            "succeeded": success,
            "failed": failed,
            "failed_banks": [r[0] for r in results if r[2]],
        }

    def _run_group(
        self, crawler_classes: List, max_workers: int
    ) -> List[Tuple]:
        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self._execute, cls): cls
                for cls in crawler_classes
            }
            for f in as_completed(futures):
                results.append(f.result())
        return results

    def _execute(
        self, crawler_cls
    ) -> Tuple[str, Optional[Dict], Optional[Exception]]:
        bank_name = crawler_cls.BANK_NAME
        try:
            crawler = crawler_cls(self.date)
            rates = crawler.crawl()
            count = len(rates) if rates else 0
            if count == 0:
                logger.warning(
                    f"{bank_name}: crawled 0 currencies - possible "
                    "parsing break or upstream change"
                )
            else:
                logger.info(f"{bank_name}: crawled {count} currencies")
            return bank_name, rates, None
        except Exception as e:
            logger.error(f"{bank_name}: crawl failed - {e}")
            return bank_name, None, e

    def _save(self, results: List[Tuple]):
        db = SessionLocal()
        saved = 0
        try:
            for bank_name, rates, error in results:
                if error or not rates:
                    continue
                try:
                    data = ExchangeRate(
                        date=self.date, bank=bank_name, rates=rates
                    )
                    repository.save_rates(db, data)
                    saved += 1
                except Exception as e:
                    logger.error(f"{bank_name}: failed to save - {e}")
        finally:
            db.close()
            logger.info(f"Saved {saved} bank rates to database")

    def scrape_bank(
        self, bank_name: str
    ) -> Optional[Dict[str, CurrencyDetail]]:
        """Scrape a single bank by name."""
        crawler_cls = CRAWLER_MAP.get(bank_name.lower())
        if not crawler_cls:
            logger.warning(f"Unknown bank: {bank_name}")
            return None

        try:
            crawler = crawler_cls(self.date)
            rates = crawler.crawl()
            logger.info(
                f"{bank_name}: scraped {len(rates) if rates else 0} currencies"
            )
            return rates
        except Exception as e:
            logger.error(f"{bank_name}: scrape failed - {e}")
            return None
