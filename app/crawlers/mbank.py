import logging
import os
from typing import Dict, Optional

import urllib3
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from app.models.exchange_rate import CurrencyDetail, Rate

logger = logging.getLogger(__name__)


class MBankCrawler:
    BANK_NAME = "M-Bank"
    REQUEST_TIMEOUT = 60000

    def __init__(self, url: str, date: str):
        self.url = url
        self.date = date
        self.ssl_verify = os.getenv("SSL_VERIFY", "True").lower() in ("true", "1", "t")

    def crawl(self) -> Dict[str, CurrencyDetail]:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            try:
                page.goto(self.url, timeout=self.REQUEST_TIMEOUT, wait_until="networkidle")
                page.wait_for_timeout(3000)

                button = page.locator("xpath=/html/body/div/div/div[2]/button")
                if button.count() > 0:
                    button.click()
                    page.wait_for_timeout(5000)
                else:
                    alt_button = page.locator("text=Валютын ханш").first
                    if alt_button.count() > 0:
                        alt_button.click()
                        page.wait_for_timeout(5000)

            except Exception as e:
                logger.warning(f"MBank page load/click error: {e}")
                browser.close()
                return {}

            rates = self._extract_rates_from_page(page)
            browser.close()

            return rates

    def _extract_rates_from_page(self, page) -> Dict[str, CurrencyDetail]:
        rates = {}

        try:
            container = page.locator("xpath=/html/body/div/div/div[2]/div[4]/div[2]")

            if container.count() == 0:
                container = page.locator("div.relative.overflow-x-auto")

            if container.count() == 0:
                logger.warning("MBank: Exchange rate container not found")
                return rates

            rows = container.locator("div.flex.min-w-\\[760px\\].bg-white").all()

            for row in rows:
                try:
                    currency_el = row.locator("p.font-semibold").first
                    if currency_el.count() == 0:
                        continue

                    currency_code = (currency_el.text_content() or "").strip().lower()
                    if not currency_code or len(currency_code) != 3:
                        continue

                    if currency_code in rates:
                        continue

                    rate_elements = row.locator("p.font-regular").all()

                    if len(rate_elements) >= 4:
                        noncash_buy = self._parse_float(rate_elements[2].text_content())
                        noncash_sell = self._parse_float(rate_elements[3].text_content())

                        if noncash_buy and noncash_sell:
                            rates[currency_code] = CurrencyDetail(
                                cash=Rate(buy=noncash_buy, sell=noncash_sell),
                                noncash=Rate(buy=noncash_buy, sell=noncash_sell),
                            )

                except Exception as e:
                    logger.debug(f"MBank row parsing error: {e}")
                    continue

        except Exception as e:
            logger.warning(f"MBank extraction error: {e}")

        return rates

    def _parse_float(self, value) -> Optional[float]:
        try:
            if isinstance(value, (int, float)):
                return float(value) if value != 0 else None

            cleaned = str(value).strip().replace(" ", "").replace("\xa0", "")

            if not cleaned or cleaned == "-" or cleaned == "0":
                return None

            if "." in cleaned and "," in cleaned:
                cleaned = cleaned.replace(".", "").replace(",", ".")
            elif "." in cleaned and cleaned.count(".") == 1 and len(cleaned.split(".")[-1]) == 3:
                cleaned = cleaned.replace(".", "")
            elif "," in cleaned:
                cleaned = cleaned.replace(",", ".")

            return float(cleaned)
        except (ValueError, TypeError):
            return None
