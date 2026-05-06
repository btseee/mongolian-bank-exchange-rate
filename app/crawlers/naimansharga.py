from datetime import date, timedelta
from typing import Dict
from urllib.parse import urlsplit, urlunsplit

from app.config import config
from app.crawlers.base import BaseCrawler
from app.models.exchange_rate import CurrencyDetail
from app.utils.logger import logger

_SKIP_FIELDS = {"createdAt", "updatedAt"}


class NaimanSharga(BaseCrawler):
    BANK_NAME = "NaimanSharga"

    def crawl(self) -> Dict[str, CurrencyDetail]:
        url = self._document_url(self.date)
        resp = self.get(url)

        if resp.status_code == 404:
            yesterday = (
                date.fromisoformat(self.date) - timedelta(days=1)
            ).isoformat()
            logger.warning(
                f"NaimanSharga: no data for {self.date}, trying {yesterday}"
            )
            url = self._document_url(yesterday)
            resp = self.get(url)

        resp.raise_for_status()

        data = resp.json()
        fields = data.get("fields", {})
        if not fields:
            logger.warning("NaimanSharga: empty fields in response")
            return {}

        return self._parse(fields)

    @staticmethod
    def _document_url(target_date: str) -> str:
        parts = urlsplit(config.NSHARGA_FIRESTORE_BASE_URL)
        path = f"{parts.path.rstrip('/')}/{target_date}"
        return urlunsplit(
            (parts.scheme, parts.netloc, path, parts.query, parts.fragment)
        )

    def _parse(self, fields: dict) -> Dict[str, CurrencyDetail]:
        rates = {}
        for code, value in fields.items():
            if code in _SKIP_FIELDS:
                continue
            if len(code) != 3:
                continue
            currency_fields = value.get("mapValue", {}).get("fields", {})
            buy = self._parse_firestore_number(currency_fields.get("avah", {}))
            sell = self._parse_firestore_number(
                currency_fields.get("zarah", {})
            )
            rates[code.lower()] = self.make_rate(
                cash_buy=buy,
                cash_sell=sell,
                noncash_buy=buy,
                noncash_sell=sell,
            )
        return rates

    @staticmethod
    def _parse_firestore_number(field: dict):
        return BaseCrawler.parse_float(
            field.get("doubleValue")
            or field.get("integerValue")
            or field.get("stringValue")
        )
