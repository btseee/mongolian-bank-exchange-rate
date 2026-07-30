"""NIBank crawler using Playwright for JavaScript rendering."""

import re
from typing import Dict

from app.config import config
from app.crawlers.base import PlaywrightCrawler
from app.models.exchange_rate import CurrencyDetail


class NIBank(PlaywrightCrawler):
    BANK_NAME = "NIBank"

    def _crawl_page(self, page) -> Dict[str, CurrencyDetail]:
        page.goto(
            config.NIBANK_URI,
            timeout=self.timeout,
            wait_until="networkidle",
        )
        page.wait_for_selector(".exchange-block", timeout=self.timeout)

        rates = {}
        for block in page.locator(".exchange-block").all():
            text = block.inner_text()
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            if len(lines) < 6:
                continue

            match = re.match(r"^([A-Z]{3})", lines[0])
            if not match:
                continue

            code = match.group(1).lower()
            cash_buy = cash_sell = noncash_buy = noncash_sell = None

            for i, line in enumerate(lines):
                if i + 1 < len(lines):
                    if "Бэлэн авах" in line:
                        cash_buy = self.parse_float(lines[i + 1])
                    elif "Бэлэн зарах" in line:
                        cash_sell = self.parse_float(lines[i + 1])
                    elif "Бэлэн бус авах" in line:
                        noncash_buy = self.parse_float(lines[i + 1])
                    elif "Бэлэн бус зарах" in line:
                        noncash_sell = self.parse_float(lines[i + 1])

            rates[code] = self.make_rate(
                cash_buy, cash_sell, noncash_buy, noncash_sell
            )
        return rates
