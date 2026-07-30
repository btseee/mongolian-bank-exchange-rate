"""TransBank crawler using Playwright for JavaScript rendering."""

import json
from typing import Dict

from app.config import config
from app.crawlers.base import PlaywrightCrawler
from app.models.exchange_rate import CurrencyDetail


class TransBank(PlaywrightCrawler):
    BANK_NAME = "TransBank"

    def _crawl_page(self, page) -> Dict[str, CurrencyDetail]:
        url = f"{config.TRANSBANK_URI}?startdate={self.date}"
        # This site keeps background network activity going indefinitely
        # (analytics/polling), so "networkidle" reliably times out even
        # though the page itself renders in well under PLAYWRIGHT_TIMEOUT.
        page.goto(url, timeout=self.timeout, wait_until="domcontentloaded")
        page.wait_for_selector("table", timeout=self.timeout)

        script = page.locator("script#__NEXT_DATA__").first
        if script.count():
            data = json.loads(script.inner_text())
            return self._parse_next_data(data)
        return self._parse_table(page)

    def _parse_next_data(self, data: dict) -> Dict[str, CurrencyDetail]:
        rates = {}
        props = data.get("props", {})
        page_props = props.get("pageProps", {})
        rate_data = page_props.get("rateData", {})
        for currencies in rate_data.values():
            for code, v in currencies.items():
                if code == "NAME":
                    continue
                cash = v.get("2", {})
                noncash = v.get("3", {})
                rates[code.strip().lower()] = self.make_rate(
                    cash_buy=self.parse_float(cash.get("BUY_RATE")),
                    cash_sell=self.parse_float(cash.get("SELL_RATE")),
                    noncash_buy=self.parse_float(noncash.get("BUY_RATE")),
                    noncash_sell=self.parse_float(noncash.get("SELL_RATE")),
                )
        return rates

    def _parse_table(self, page) -> Dict[str, CurrencyDetail]:
        rates = {}
        for row in page.locator("table tbody tr").all():
            cells = row.locator("td").all()
            if len(cells) >= 7:
                code = cells[0].inner_text().strip().split()[0].lower()
                if code and len(code) == 3:
                    rates[code] = self.make_rate(
                        cash_buy=self.parse_float(cells[3].inner_text()),
                        cash_sell=self.parse_float(cells[4].inner_text()),
                        noncash_buy=self.parse_float(cells[5].inner_text()),
                        noncash_sell=self.parse_float(cells[6].inner_text()),
                    )
        return rates
