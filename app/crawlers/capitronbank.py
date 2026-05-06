from typing import Dict

from app.config import config
from app.crawlers.base import BaseCrawler
from app.models.exchange_rate import CurrencyDetail


class CapitronBank(BaseCrawler):
    BANK_NAME = "CapitronBank"

    def crawl(self) -> Dict[str, CurrencyDetail]:
        resp = self.get(config.CAPITRONBANK_API_URL)
        resp.raise_for_status()
        return self._parse(resp.json())

    def _parse(self, data: list) -> Dict[str, CurrencyDetail]:
        rates = {}
        for item in data:
            code = (
                item.get("currencyCode") or item.get("curcode") or ""
            ).lower()
            if code:
                buy_rate = item.get("cashBuyRate") or item.get("buyrate")
                sell_rate = item.get("cashSellRate") or item.get("salerate")
                rates[code] = self.make_rate(
                    cash_buy=self.parse_float(buy_rate),
                    cash_sell=self.parse_float(sell_rate),
                    noncash_buy=self.parse_float(
                        item.get("transferBuyRate") or buy_rate
                    ),
                    noncash_sell=self.parse_float(
                        item.get("transferSellRate") or sell_rate
                    ),
                )
        return rates
