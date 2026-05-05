from typing import Dict

import requests

from app.config import config
from app.crawlers.base import BaseCrawler
from app.models.exchange_rate import CurrencyDetail


class MBank(BaseCrawler):
    BANK_NAME = "MBank"
    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/144.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json",
        "Referer": "https://m-bank.mn/",
        "Origin": "https://m-bank.mn",
    }

    def crawl(self) -> Dict[str, CurrencyDetail]:
        session = requests.Session()
        session.verify = self.ssl_verify

        login_resp = session.post(
            f"{config.MBANK_URI}api/login",
            headers=self.HEADERS,
            timeout=self.timeout,
        )
        login_resp.raise_for_status()

        resp = session.get(
            f"{config.MBANK_URI}api",
            params={"name": "getCurrencyList"},
            headers=self.HEADERS,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return self._parse(resp.json())

    def _parse(self, data: dict) -> Dict[str, CurrencyDetail]:
        rates = {}
        if not data.get("success"):
            return rates
        for item in data.get("data", []):
            code = (item.get("fxd_crncy_code") or "").lower()
            if code:
                buy = self.parse_float(item.get("buy_rate"))
                sell = self.parse_float(item.get("sale_rate"))
                rates[code] = self.make_rate(buy, sell, buy, sell)
        return rates
