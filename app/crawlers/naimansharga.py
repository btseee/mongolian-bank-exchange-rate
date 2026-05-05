from datetime import date, timedelta
from typing import Dict

from app.config import config
from app.crawlers.base import BaseCrawler
from app.models.exchange_rate import CurrencyDetail
from app.utils.logger import logger

_SKIP_FIELDS = {"createdAt", "updatedAt"}


class NaimanSharga(BaseCrawler):
    BANK_NAME = "NaimanSharga"

    def crawl(self) -> Dict[str, CurrencyDetail]:
        url = f"{config.NSHARGA_FIRESTORE_BASE_URL}/{self.date}"
        resp = self.get(url)

        if resp.status_code == 404:
            yesterday = (
                date.fromisoformat(self.date) - timedelta(days=1)
            ).isoformat()
            logger.warning(
                f"NaimanSharga: no data for {self.date}, trying {yesterday}"
            )
            url = f"{config.NSHARGA_FIRESTORE_BASE_URL}/{yesterday}"
            resp = self.get(url)

        resp.raise_for_status()

        data = resp.json()
        fields = data.get("fields", {})
        if not fields:
            logger.warning("NaimanSharga: empty fields in response")
            return {}

        return self._parse(fields)

    def _parse(self, fields: dict) -> Dict[str, CurrencyDetail]:
        rates = {}
        for code, value in fields.items():
            if code in _SKIP_FIELDS:
                continue
            if len(code) != 3:
                continue
            currency_fields = value.get("mapValue", {}).get("fields", {})
            buy = self.parse_float(
                currency_fields.get("avah", {}).get("doubleValue")
            )
            sell = self.parse_float(
                currency_fields.get("zarah", {}).get("doubleValue")
            )
            rates[code.lower()] = self.make_rate(
                cash_buy=buy,
                cash_sell=sell,
                noncash_buy=buy,
                noncash_sell=sell,
            )
        return rates
