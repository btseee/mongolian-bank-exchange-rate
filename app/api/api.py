import datetime
from contextlib import asynccontextmanager
from typing import List

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.__version__ import (
    __author__,
    __donation__,
    __license__,
    __url__,
    __version__,
)
from app.db import repository
from app.db.database import get_db, init_db
from app.models.exchange_rate import CurrencyRateResponse

BANKS = [
    "ArigBank",
    "BogdBank",
    "CapitronBank",
    "CKBank",
    "GolomtBank",
    "KhanBank",
    "MBank",
    "MongolBank",
    "NaimanSharga",
    "NIBank",
    "SendMN",
    "StateBank",
    "TDBM",
    "TransBank",
    "XacBank",
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Монголын Банкуудын Валютын Ханш API",
    version=__version__,
    contact={"name": __author__, "url": __url__},
    license_info={
        "name": __license__,
        "url": "https://opensource.org/licenses/MIT",
    },
    lifespan=lifespan,
    openapi_tags=[
        {
            "name": "Ерөнхий",
            "description": "API-н ерөнхий мэдээлэл",
        },
        {
            "name": "Ханш",
            "description": "Валютын ханшийн endpoints",
        },
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/", tags=["Ерөнхий"])
def root():
    """API-н ерөнхий мэдээлэл, дэмждэг банкууд, endpoints."""
    return {
        "name": "Монголын Банкуудын Валютын Ханш API",
        "version": __version__,
        "documentation": "/docs",
        "github": __url__,
        "donation": __donation__,
        "supported_banks": BANKS,
        "endpoints": {
            "/rates": "Бүх ханш (pagination-тай)",
            "/rates/latest": "Банк бүрийн хамгийн сүүлийн ханш",
            "/rates/bank/{bank_name}": "Тодорхой банкны ханш",
            "/rates/date/{date}": "Тодорхой өдрийн бүх банкны ханш",
            "/rates/bank/{bank_name}/date/{date}": "Банк + өдрөөр ханш",
            "/health": "API health check",
        },
        "example_currencies": ["usd", "eur", "cny", "rub", "jpy"],
    }


@app.get("/health", tags=["Ерөнхий"])
def health():
    """API health check - monitoring-д ашиглана."""
    return {"status": "healthy", "version": __version__}


@app.get(
    "/rates",
    response_model=List[CurrencyRateResponse],
    tags=["Ханш"],
    summary="Бүх ханш авах",
)
def get_all_rates(
    skip: int = Query(
        0, ge=0, description="Алгасах өгөгдлийн тоо (pagination)"
    ),
    limit: int = Query(
        100, ge=1, le=1000, description="Буцаах өгөгдлийн тоо (1-1000)"
    ),
    db: Session = Depends(get_db),
):
    """
    Бүх банкны бүх ханшийг авах (pagination-тай).

    - **skip**: Эхнээс хэдийг алгасах (default: 0)
    - **limit**: Хэдэн бичлэг буцаах (default: 100, max: 1000)
    """
    return repository.get_all_rates(db, skip=skip, limit=limit)


@app.get(
    "/rates/latest",
    response_model=List[CurrencyRateResponse],
    tags=["Ханш"],
    summary="Хамгийн сүүлийн ханш",
)
def get_latest_rates(db: Session = Depends(get_db)):
    """
    Банк бүрийн хамгийн сүүлд бүртгэгдсэн ханшийг буцаана.

    Энэ endpoint нь банк бүрээс зөвхөн 1 өгөгдөл буцаана (нийт 13).
    """
    return repository.get_latest_rates(db)


@app.get(
    "/rates/bank/{bank_name}",
    response_model=List[CurrencyRateResponse],
    tags=["Ханш"],
    summary="Банкаар ханш авах",
)
def get_rates_by_bank(
    bank_name: str,
    skip: int = Query(0, ge=0, description="Алгасах өгөгдлийн тоо"),
    limit: int = Query(100, ge=1, le=1000, description="Буцаах өгөгдлийн тоо"),
    db: Session = Depends(get_db),
):
    """
    Тодорхой банкны бүх ханшийг авах.

    **bank_name жишээ**: KhanBank, GolomtBank, TDBM, XacBank

    Банкны нэрийг яг зөв бичих шаардлагатай (case-sensitive).
    """
    rates = repository.get_rates_by_bank(db, bank_name, skip=skip, limit=limit)
    if not rates:
        raise HTTPException(404, f"'{bank_name}' банкны ханш олдсонгүй")
    return rates


@app.get(
    "/rates/date/{date}",
    response_model=List[CurrencyRateResponse],
    tags=["Ханш"],
    summary="Өдрөөр ханш авах",
)
def get_rates_by_date(
    date: str,
    skip: int = Query(0, ge=0, description="Алгасах бичлэгийн тоо"),
    limit: int = Query(100, ge=1, le=1000, description="Буцаах бичлэгийн тоо"),
    db: Session = Depends(get_db),
):
    """
    Тодорхой өдрийн бүх банкны ханшийг авах.

    **date формат**: YYYY-MM-DD (жишээ: 2026-02-06)
    """
    try:
        date_obj = datetime.date.fromisoformat(date)
    except ValueError:
        raise HTTPException(
            400, "Огнооны формат буруу. YYYY-MM-DD ашиглана уу"
        )

    rates = repository.get_rates_by_date(db, date_obj, skip=skip, limit=limit)
    if not rates:
        raise HTTPException(404, f"'{date}' өдрийн ханш олдсонгүй")
    return rates


@app.get(
    "/rates/bank/{bank_name}/date/{date}",
    response_model=CurrencyRateResponse,
    tags=["Ханш"],
    summary="Банк + өдрөөр ханш авах",
)
def get_rate_by_bank_and_date(
    bank_name: str,
    date: str,
    db: Session = Depends(get_db),
):
    """
    Тодорхой банкны тодорхой өдрийн ханшийг авах.

    - **bank_name**: Банкны нэр (жишээ: KhanBank)
    - **date**: Огноо YYYY-MM-DD форматаар

    Зөвхөн 1 өгөгдөл буцаана.
    """
    try:
        date_obj = datetime.date.fromisoformat(date)
    except ValueError:
        raise HTTPException(
            400, "Огнооны формат буруу. YYYY-MM-DD ашиглана уу"
        )

    rate = repository.get_rates_by_bank_and_date(db, bank_name, date_obj)
    if not rate:
        raise HTTPException(
            404, f"'{bank_name}' банкны '{date}' өдрийн ханш олдсонгүй"
        )
    return rate
