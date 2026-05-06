from typing import Dict

from app.config import config
from app.crawlers.base import BaseCrawler
from app.models.exchange_rate import CurrencyDetail
from app.utils.logger import logger


class ArigBank(BaseCrawler):
    BANK_NAME = "ArigBank"

    def crawl(self) -> Dict[str, CurrencyDetail]:
        token = (config.ARIGBANK_BEARER_TOKEN or "").strip()
        if token:
            data = self._get_rates(token)
            if self._has_token_error(data):
                logger.warning(
                    "ArigBank: configured token expired, signing in"
                )
            else:
                return self._rates_from_payload(data)

        token = self._sign_in()
        if not token:
            return {}

        data = self._get_rates(token)
        return self._rates_from_payload(data)

    def _sign_in(self) -> str:
        resp = self.post(
            config.ARIGBANK_SIGNIN_URL,
            headers={"Content-Type": "application/json"},
            json={},
        )
        resp.raise_for_status()

        token = (resp.json().get("token") or "").strip()
        if not token:
            logger.warning("ArigBank: signIn did not return a token")
        return token

    def _get_rates(self, token: str) -> dict:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }
        resp = self.post(
            config.ARIGBANK_API_URL,
            headers=headers,
            json={"rateDate": self.date.replace("-", "")},
        )
        if resp.status_code == 401:
            try:
                return resp.json()
            except ValueError:
                return {"status": 401, "message": resp.text}

        resp.raise_for_status()
        return resp.json()

    def _rates_from_payload(self, data: dict) -> Dict[str, CurrencyDetail]:
        if not data.get("data") and data.get("message"):
            logger.warning(f"ArigBank API error: {data.get('message')}")
            return {}
        return self._parse(data.get("data", []))

    @staticmethod
    def _has_token_error(data: dict) -> bool:
        message = str(data.get("message") or "").lower()
        return data.get("status") == 401 or "expired" in message

    def _parse(self, data: list) -> Dict[str, CurrencyDetail]:
        rates = {}
        for item in data:
            code = item.get("curCode", "").strip().lower()
            if code:
                rates[code] = self.make_rate(
                    cash_buy=self.parse_float(item.get("belenBuyRate")),
                    cash_sell=self.parse_float(item.get("belenSellRate")),
                    noncash_buy=self.parse_float(item.get("belenBusBuyRate")),
                    noncash_sell=self.parse_float(
                        item.get("belenBusSellRate")
                    ),
                )
        return rates
