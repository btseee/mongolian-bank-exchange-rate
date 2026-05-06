import datetime
import re
from collections import OrderedDict, deque
from contextlib import asynccontextmanager
from enum import Enum
from time import monotonic
from typing import List

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.__version__ import (
    __author__,
    __donation__,
    __license__,
    __url__,
    __version__,
)
from app.config import config
from app.crawlers import ALL_CRAWLERS
from app.db import repository
from app.db.database import get_db, init_db
from app.models.exchange_rate import CurrencyRateResponse

BANKS = [crawler.BANK_NAME for crawler in ALL_CRAWLERS]
BankName = Enum("BankName", {bank: bank for bank in BANKS})
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
RATE_LIMIT_EXCLUDED_PATHS = {"/health"}
_rate_limit_hits = OrderedDict()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Монголын Банкуудын Валютын Ханш API",
    version=__version__,
    description=(
        "Монголын банк, санхүүгийн байгууллагуудын валютын ханшийг "
        "нэг хэлбэртэй JSON бүтэцтэйгээр буцаадаг REST API. "
        "Swagger дээр банкны нэр, огноо, pagination параметрүүдийг сонгон "
        "турших боломжтой."
    ),
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
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=config.CORS_ALLOW_CREDENTIALS,
    allow_methods=["GET"],
    allow_headers=["*"],
)


def _client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if config.TRUST_PROXY_HEADERS and forwarded_for:
        return forwarded_for.split(",", maxsplit=1)[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def _rate_limit_bucket(client_key: str) -> deque:
    client_hits = _rate_limit_hits.get(client_key)
    if client_hits is not None:
        _rate_limit_hits.move_to_end(client_key)
        return client_hits

    while len(_rate_limit_hits) >= config.RATE_LIMIT_MAX_CLIENTS:
        _rate_limit_hits.popitem(last=False)

    client_hits = deque()
    _rate_limit_hits[client_key] = client_hits
    return client_hits


def _parse_date(value: str) -> datetime.date:
    if not DATE_PATTERN.fullmatch(value):
        raise HTTPException(
            400, "Огнооны формат буруу. YYYY-MM-DD ашиглана уу"
        )

    try:
        return datetime.date.fromisoformat(value)
    except ValueError:
        raise HTTPException(
            400, "Огнооны формат буруу. YYYY-MM-DD ашиглана уу"
        )


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    if (
        not config.RATE_LIMIT_ENABLED
        or request.url.path in RATE_LIMIT_EXCLUDED_PATHS
    ):
        return await call_next(request)

    now = monotonic()
    window_start = now - config.RATE_LIMIT_WINDOW_SECONDS
    client_hits = _rate_limit_bucket(_client_ip(request))

    while client_hits and client_hits[0] <= window_start:
        client_hits.popleft()

    if len(client_hits) >= config.RATE_LIMIT_REQUESTS:
        retry_after = max(
            1,
            int(config.RATE_LIMIT_WINDOW_SECONDS - (now - client_hits[0])),
        )
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"},
            headers={"Retry-After": str(retry_after)},
        )

    client_hits.append(now)
    response = await call_next(request)
    remaining = max(config.RATE_LIMIT_REQUESTS - len(client_hits), 0)
    response.headers["X-RateLimit-Limit"] = str(config.RATE_LIMIT_REQUESTS)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    return response


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
        100,
        ge=1,
        le=config.API_MAX_LIMIT,
        description=f"Буцаах өгөгдлийн тоо (1-{config.API_MAX_LIMIT})",
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
    bank_name: BankName,
    skip: int = Query(0, ge=0, description="Алгасах өгөгдлийн тоо"),
    limit: int = Query(
        100,
        ge=1,
        le=config.API_MAX_LIMIT,
        description=f"Буцаах өгөгдлийн тоо (1-{config.API_MAX_LIMIT})",
    ),
    db: Session = Depends(get_db),
):
    """
    Тодорхой банкны бүх ханшийг авах.

    **bank_name жишээ**: KhanBank, GolomtBank, TDBM, XacBank

    Банкны нэрийг яг зөв бичих шаардлагатай (case-sensitive).
    """
    rates = repository.get_rates_by_bank(
        db, bank_name.value, skip=skip, limit=limit
    )
    if not rates:
        raise HTTPException(404, f"'{bank_name.value}' банкны ханш олдсонгүй")
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
    limit: int = Query(
        100,
        ge=1,
        le=config.API_MAX_LIMIT,
        description=f"Буцаах бичлэгийн тоо (1-{config.API_MAX_LIMIT})",
    ),
    db: Session = Depends(get_db),
):
    """
    Тодорхой өдрийн бүх банкны ханшийг авах.

    **date формат**: YYYY-MM-DD (жишээ: 2026-02-06)
    """
    date_obj = _parse_date(date)

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
    bank_name: BankName,
    date: str,
    db: Session = Depends(get_db),
):
    """
    Тодорхой банкны тодорхой өдрийн ханшийг авах.

    - **bank_name**: Банкны нэр (жишээ: KhanBank)
    - **date**: Огноо YYYY-MM-DD форматаар

    Зөвхөн 1 өгөгдөл буцаана.
    """
    date_obj = _parse_date(date)

    rate = repository.get_rates_by_bank_and_date(db, bank_name.value, date_obj)
    if not rate:
        raise HTTPException(
            404, f"'{bank_name.value}' банкны '{date}' өдрийн ханш олдсонгүй"
        )
    return rate
