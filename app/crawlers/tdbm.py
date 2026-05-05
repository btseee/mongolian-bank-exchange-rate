"""TDBM bank crawler using Playwright for JavaScript rendering."""

from datetime import datetime, timedelta
from typing import Dict

from app.config import config
from app.crawlers.base import PlaywrightCrawler
from app.models.exchange_rate import CurrencyDetail


class TDBM(PlaywrightCrawler):
    BANK_NAME = "TDBM"

    def _crawl_page(self, page) -> Dict[str, CurrencyDetail]:
        page.goto(
            config.TDBM_URI,
            timeout=self.timeout,
            wait_until="domcontentloaded",
        )
        page.wait_for_selector("table.table-hover", timeout=self.timeout)

        target = datetime.strptime(self.date, "%Y-%m-%d")
        date_inputs = page.locator("input[type=date]").all()
        buttons = None
        if date_inputs:
            date_inputs[0].fill(target.strftime("%Y-%m-%d"))
            buttons = page.locator(
                "form button, form input[type=submit]"
            ).all()
            if buttons:
                buttons[0].click()
                page.wait_for_selector(
                    "table.table-hover",
                    state="visible",
                    timeout=self.timeout,
                )

        rates = self._parse_table(page)
        if not rates and date_inputs:
            yesterday = target - timedelta(days=1)
            date_inputs[0].fill(yesterday.strftime("%Y-%m-%d"))
            if buttons:
                buttons[0].click()
                page.wait_for_selector(
                    "table.table-hover",
                    state="visible",
                    timeout=self.timeout,
                )
            rates = self._parse_table(page)

        return rates

    def _parse_table(self, page) -> Dict[str, CurrencyDetail]:
        rates = {}
        for row in page.locator("table.table-hover tbody tr").all():
            cells = row.locator("td").all()
            if len(cells) >= 8:
                code = cells[1].inner_text().strip().lower()
                if code and len(code) == 3:
                    rates[code] = self.make_rate(
                        cash_buy=self.parse_float(cells[6].inner_text()),
                        cash_sell=self.parse_float(cells[7].inner_text()),
                        noncash_buy=self.parse_float(cells[4].inner_text()),
                        noncash_sell=self.parse_float(cells[5].inner_text()),
                    )
        return rates
