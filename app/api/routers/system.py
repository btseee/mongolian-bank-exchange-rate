"""General/system endpoints: health check and API info."""

from fastapi import APIRouter

from app.__version__ import __donation__, __url__, __version__
from app.api.dependencies import BANKS

router = APIRouter(prefix="/api", tags=["Ерөнхий"])


@router.get("/health", summary="Health check")
def health():
    """API health check - monitoring-д ашиглана."""
    return {"status": "healthy", "version": __version__}


@router.get("/info", summary="API-н ерөнхий мэдээлэл")
def info():
    """API-н ерөнхий мэдээлэл, дэмждэг банкууд, endpoints."""
    return {
        "name": "Монголын Банкуудын Валютын Ханш API",
        "version": __version__,
        "documentation": "/",
        "github": __url__,
        "donation": __donation__,
        "supported_banks": BANKS,
        "endpoints": {
            "/api/rates": "Бүх ханш (pagination-тай)",
            "/api/rates/latest": "Банк бүрийн хамгийн сүүлийн ханш",
            "/api/rates/bank/{bank_name}": "Тодорхой банкны ханш",
            "/api/rates/date/{date}": "Тодорхой өдрийн бүх банкны ханш",
            "/api/rates/bank/{bank_name}/date/{date}": "Банк + өдрөөр ханш",
            "/api/health": "API health check",
            "/api/admin/crawl": (
                "Өнөөдрийн ханш татаж эхлэх (admin key шаардана)"
            ),
            "/api/admin/backfill": (
                "Түүхэн ханш татаж эхлэх (admin key шаардана)"
            ),
        },
        "example_currencies": ["usd", "eur", "cny", "rub", "jpy"],
    }
