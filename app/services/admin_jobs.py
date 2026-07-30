"""In-process job lock and state for the HTTP-triggered admin endpoints.

Render's free tier has no background-worker/cron process type, so daily
crawls and backfills are triggered over HTTP by an external scheduler
instead of an always-on process. try_start()/finish() bracket every admin
job so a manually-triggered backfill can never overlap the scheduled daily
crawl (or another admin call) against the same bank sites and DB rows.
This lock is correct only as long as Uvicorn runs as a single process
(no --workers flag) - true for this deployment.
"""

import threading
from datetime import date, datetime, timezone
from typing import Optional

from app.db import repository
from app.db.database import SessionLocal
from app.models.exchange_rate import ExchangeRate
from app.services.scraper import ScraperService
from app.utils.logger import logger
from scripts.backfill import backfill as run_backfill_range

_lock = threading.Lock()
_state = {
    "is_running": False,
    "job_type": None,
    "started_at": None,
    "finished_at": None,
    "last_result": None,
    "last_error": None,
}


def get_status() -> dict:
    return dict(_state)


def try_start(job_type: str) -> bool:
    """Non-blocking lock acquire. The caller (a router) must call finish()
    exactly once afterwards, whether the job runs sync or in the background.
    """
    if not _lock.acquire(blocking=False):
        return False
    _state.update(
        is_running=True,
        job_type=job_type,
        started_at=datetime.now(timezone.utc).isoformat(),
        finished_at=None,
    )
    return True


def finish(result: Optional[dict] = None, error: Optional[str] = None) -> None:
    _state.update(
        is_running=False,
        finished_at=datetime.now(timezone.utc).isoformat(),
        last_result=result,
        last_error=error,
    )
    _lock.release()


def run_crawl_job() -> None:
    """Background task for POST /api/admin/crawl. Assumes the lock is
    already held by the router's try_start() call. Must be a plain `def`,
    not `async def` - FastAPI runs BackgroundTasks callables in a worker
    thread, keeping Uvicorn's event loop free while this blocks on I/O."""
    try:
        result = ScraperService().run_all()
        finish(result=result)
    except Exception as e:
        logger.error(f"Admin crawl job failed: {e}")
        finish(error=str(e))


def run_backfill_job(start: date, end: date) -> None:
    """Background task for POST /api/admin/backfill. Assumes the lock is
    already held by the router's try_start() call."""
    try:
        result = run_backfill_range(start, end)
        finish(result=result)
    except Exception as e:
        logger.error(f"Admin backfill job failed: {e}")
        finish(error=str(e))


def run_single_bank_job(bank_name: str) -> Optional[dict]:
    """Synchronous single-bank crawl for POST /api/admin/crawl/{bank_name}.
    Assumes the lock is already held by the router's try_start() call.

    ScraperService.scrape_bank() only fetches, it never persists - unlike
    run_all()'s own _save() step - so this explicitly saves on success.
    """
    try:
        service = ScraperService()
        rates = service.scrape_bank(bank_name)
        if rates:
            db = SessionLocal()
            try:
                data = ExchangeRate(
                    date=service.date, bank=bank_name, rates=rates
                )
                repository.save_rates(db, data)
            finally:
                db.close()
        finish(result={"bank_name": bank_name, "rates": rates})
        return rates
    except Exception as e:
        logger.error(f"Admin single-bank crawl failed for {bank_name}: {e}")
        finish(error=str(e))
        raise
