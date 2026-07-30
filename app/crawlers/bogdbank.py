"""BogdBank crawler using Playwright for JavaScript rendering."""

from typing import Dict

from app.config import config
from app.crawlers.base import PlaywrightCrawler
from app.models.exchange_rate import CurrencyDetail


class BogdBank(PlaywrightCrawler):
    BANK_NAME = "BogdBank"

    def _crawl_page(self, page) -> Dict[str, CurrencyDetail]:
        url = f"{config.BOGDBANK_URI}?date={self.date}"
        page.goto(url, timeout=self.timeout, wait_until="networkidle")
        page.wait_for_selector("table", timeout=self.timeout)
        page.wait_for_timeout(2000)

        rates = {}
        for row in page.locator("table tbody tr").all():
            cells = row.locator("td").all()
            if len(cells) >= 6:
                code = self._extract_code(cells[0])
                if code and len(code) == 3:
                    rates[code] = self.make_rate(
                        cash_buy=self.parse_float(cells[2].inner_text()),
                        cash_sell=self.parse_float(cells[3].inner_text()),
                        noncash_buy=self.parse_float(cells[4].inner_text()),
                        noncash_sell=self.parse_float(cells[5].inner_text()),
                    )
        return rates

    @staticmethod
    def _extract_code(cell) -> str:
        """The currency-code cell now renders as a flag <img> (e.g.
        .../USD.svg) instead of plain text. Try the text first in case the
        site reverts, then fall back to the image filename."""
        text = cell.inner_text().strip().replace("\xa0", "").replace(" ", "")
        if len(text) == 3:
            return text.lower()

        images = cell.locator("img").all()
        if not images:
            return ""
        src = images[0].get_attribute("src") or ""
        filename = src.rsplit("/", 1)[-1]
        return filename.rsplit(".", 1)[0].lower()
