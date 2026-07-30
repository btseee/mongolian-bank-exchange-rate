"""Admin endpoints: on-demand crawl/backfill for Render's HTTP-only free
tier, where no always-on worker process is available to run a scheduler.
All routes require the X-Admin-Key header (see app.api.dependencies)."""

from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.dependencies import BankName, require_admin_key
from app.services import admin_jobs
from scripts.backfill import parse_date_args

router = APIRouter(
    prefix="/api/admin",
    tags=["Админ"],
    dependencies=[Depends(require_admin_key)],
)

_DATE_PATTERN = r"^\d{4}-\d{2}-\d{2}$"


class BackfillRequest(BaseModel):
    start: Optional[str] = Field(None, pattern=_DATE_PATTERN)
    end: Optional[str] = Field(None, pattern=_DATE_PATTERN)


@router.post("/crawl", status_code=202, summary="Өнөөдрийн ханш татаж эхлэх")
def start_crawl(background_tasks: BackgroundTasks):
    """
    Өнөөдрийн өдрөөр бүх 15 банкны ханшийг татаж эхлүүлнэ (background дээр).

    Хариу нэн даруй `202 Accepted`-ээр буцна - гүйцэтгэл дуусаагүй байж
    болно. Явцыг шалгахын тулд `GET /api/admin/status` ашиглана уу.
    """
    if not admin_jobs.try_start("crawl"):
        raise HTTPException(409, "Өөр job аль хэдийн ажиллаж байна")
    background_tasks.add_task(admin_jobs.run_crawl_job)
    return {"status": "started", "job_type": "crawl"}


@router.post("/crawl/{bank_name}", summary="Ганц банкны ханш нэн даруй татах")
def start_single_bank_crawl(bank_name: BankName):
    """
    Ганц банкны өнөөдрийн ханшийг синхроноор (хүлээж) татаж, шууд хадгална.

    Нэг банкны ханшийг гараар шинэчлэх, эсвэл асуудлыг оношлоход ашиглана.
    """
    if not admin_jobs.try_start(f"crawl:{bank_name.value}"):
        raise HTTPException(409, "Өөр job аль хэдийн ажиллаж байна")

    rates = admin_jobs.run_single_bank_job(bank_name.value)
    if not rates:
        raise HTTPException(
            502, f"'{bank_name.value}' банкны ханш татахад алдаа гарлаа"
        )
    return {"bank_name": bank_name.value, "rates": rates}


@router.post("/backfill", status_code=202, summary="Түүхэн ханш татаж эхлэх")
def start_backfill(
    request: BackfillRequest, background_tasks: BackgroundTasks
):
    """
    Өгөгдсөн огнооны хооронд (эсвэл 2026-01-01-ээс өнөөдөр хүртэл,
    анхдагчаар) өдөр бүрийн ханшийг дараалан татаж эхлүүлнэ (background дээр).

    Банкны сайтуудыг бага багаар дуудахын тулд өдөр бүрийн хооронд
    `BACKFILL_DELAY_SECONDS` (анхдагч 2 сек) азнаа хүлээнэ.
    """
    if request.end is not None and request.start is None:
        raise HTTPException(
            400, "'end' огноог заахын тулд 'start' огноог зааx шаардлагатай"
        )
    args = [v for v in (request.start, request.end) if v is not None]
    try:
        start, end = parse_date_args(args)
    except ValueError as exc:
        raise HTTPException(400, str(exc))

    if not admin_jobs.try_start("backfill"):
        raise HTTPException(409, "Өөр job аль хэдийн ажиллаж байна")

    background_tasks.add_task(admin_jobs.run_backfill_job, start, end)
    return {
        "status": "started",
        "job_type": "backfill",
        "start": start.isoformat(),
        "end": end.isoformat(),
    }


@router.get("/status", summary="Job-ын явцыг шалгах")
def get_status():
    """Одоо ажиллаж буй (эсвэл сүүлд дууссан) crawl/backfill job-ын төлөв."""
    return admin_jobs.get_status()
