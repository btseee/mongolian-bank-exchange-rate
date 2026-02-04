import os
from typing import Dict, Optional

import urllib3
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from app.models.exchange_rate import CurrencyDetail, Rate


class CKBankCrawler:
    BANK_NAME = "Chinggis Khaan Bank"
    REQUEST_TIMEOUT = 60000

    def __init__(self, url: str, date: str):
        self.url = url
        self.date = date
        self.ssl_verify = os.getenv("SSL_VERIFY", "True").lower() in ("true", "1", "t")

    def crawl(self) -> Dict[str, CurrencyDetail]:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            page.goto(self.url, timeout=self.REQUEST_TIMEOUT, wait_until="networkidle")

            rates = self._extract_rates_from_page(page)
            browser.close()

            return rates

    def _extract_rates_from_page(self, page) -> Dict[str, CurrencyDetail]:
        rates = {}

        try:
            rows = page.locator("table tbody tr, .uk-table tbody tr").all()

            for row in rows:
                cells = row.locator("td").all()
                if len(cells) >= 6:
                    try:
                        first_cell_text = cells[0].text_content() or ""

                        import re

                        currency_match = re.search(r"\b([A-Z]{3})\b", first_cell_text)
                        if not currency_match:
                            continue

                        currency_code = currency_match.group(1).lower()

                        if currency_code in rates:
                            continue

                        cash_buy = self._parse_float(cells[2].text_content())
                        cash_sell = self._parse_float(cells[3].text_content())
                        noncash_buy = self._parse_float(cells[4].text_content())
                        noncash_sell = self._parse_float(cells[5].text_content())

                        rates[currency_code] = CurrencyDetail(
                            cash=Rate(buy=cash_buy, sell=cash_sell),
                            noncash=Rate(buy=noncash_buy, sell=noncash_sell),
                        )
                    except Exception:
                        continue
        except Exception:
            pass

        return rates

    def _parse_float(self, value) -> Optional[float]:
        try:
            if isinstance(value, (int, float)):
                return float(value) if value != 0 else None

            cleaned = str(value).strip().replace(",", "").replace(" ", "").replace("\xa0", "")
            if not cleaned or cleaned == "-" or cleaned == "0":
                return None
            return float(cleaned)
        except (ValueError, TypeError):
            return None
