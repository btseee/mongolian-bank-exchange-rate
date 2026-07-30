"""Shared FastAPI dependencies: bank enum, date parsing, admin auth."""

import re
import secrets
from datetime import date
from enum import Enum

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

from app.config import config
from app.crawlers import ALL_CRAWLERS

BANKS = [crawler.BANK_NAME for crawler in ALL_CRAWLERS]
BankName = Enum("BankName", {bank: bank for bank in BANKS})

DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")

_INVALID_DATE_MESSAGE = "Огнооны формат буруу. YYYY-MM-DD ашиглана уу"


def parse_date(value: str) -> date:
    if not DATE_PATTERN.fullmatch(value):
        raise HTTPException(400, _INVALID_DATE_MESSAGE)
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise HTTPException(400, _INVALID_DATE_MESSAGE)


_admin_key_header = APIKeyHeader(name="X-Admin-Key", auto_error=False)


def require_admin_key(api_key: str = Security(_admin_key_header)) -> None:
    """Guard for /api/admin/*. An unset ADMIN_API_KEY disables the whole
    surface (503) rather than ever being treated as "no key required"."""
    if not config.ADMIN_API_KEY:
        raise HTTPException(
            503, "Admin endpoints are disabled (ADMIN_API_KEY not set)"
        )
    key_matches = api_key and secrets.compare_digest(
        api_key, config.ADMIN_API_KEY
    )
    if not key_matches:
        raise HTTPException(401, "Invalid or missing X-Admin-Key header")
