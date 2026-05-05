from typing import Dict

from app.config import config
from app.crawlers.base import BaseCrawler
from app.models.exchange_rate import CurrencyDetail
from app.utils.logger import logger


class SendMN(BaseCrawler):
    BANK_NAME = "SendMN"

    def crawl(self) -> Dict[str, CurrencyDetail]:
        resp = self.get(config.SENDMN_FIRESTORE_URL)
        resp.raise_for_status()

        data = resp.json()
        values = (
            data.get("fields", {})
            .get("data", {})
            .get("arrayValue", {})
            .get("values", [])
        )
        if not values:
            logger.warning("SendMN: no rate data in response")
            return {}

        return self._parse(values)

    def _parse(self, values: list) -> Dict[str, CurrencyDetail]:
        rates = {}
        for item in values:
            fields = item.get("mapValue", {}).get("fields", {})
            code = fields.get("currency", {}).get("stringValue", "").strip().lower()
            if len(code) != 3:
                continue
            buy = self.parse_float(fields.get("buy", {}).get("stringValue"))
            sell = self.parse_float(fields.get("sell", {}).get("stringValue"))
            rates[code] = self.make_rate(
                cash_buy=buy,
                cash_sell=sell,
                noncash_buy=buy,
                noncash_sell=sell,
            )
        return rates
