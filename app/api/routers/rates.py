"""Exchange-rate query endpoints."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies import BankName, parse_date
from app.config import config
from app.db import repository
from app.db.database import get_db
from app.models.exchange_rate import CurrencyRateResponse

router = APIRouter(prefix="/api/rates", tags=["Ханш"])


@router.get(
    "",
    response_model=List[CurrencyRateResponse],
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


@router.get(
    "/latest",
    response_model=List[CurrencyRateResponse],
    summary="Хамгийн сүүлийн ханш",
)
def get_latest_rates(db: Session = Depends(get_db)):
    """
    Банк бүрийн хамгийн сүүлд бүртгэгдсэн ханшийг буцаана.

    Энэ endpoint нь банк бүрээс зөвхөн 1 өгөгдөл буцаана (нийт 15).
    """
    return repository.get_latest_rates(db)


@router.get(
    "/bank/{bank_name}",
    response_model=List[CurrencyRateResponse],
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


@router.get(
    "/date/{date}",
    response_model=List[CurrencyRateResponse],
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
    date_obj = parse_date(date)

    rates = repository.get_rates_by_date(db, date_obj, skip=skip, limit=limit)
    if not rates:
        raise HTTPException(404, f"'{date}' өдрийн ханш олдсонгүй")
    return rates


@router.get(
    "/bank/{bank_name}/date/{date}",
    response_model=CurrencyRateResponse,
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
    date_obj = parse_date(date)

    rate = repository.get_rates_by_bank_and_date(db, bank_name.value, date_obj)
    if not rate:
        raise HTTPException(
            404, f"'{bank_name.value}' банкны '{date}' өдрийн ханш олдсонгүй"
        )
    return rate
