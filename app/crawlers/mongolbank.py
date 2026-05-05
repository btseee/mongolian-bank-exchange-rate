from typing import Dict

from lxml import etree

from app.config import config
from app.crawlers.base import BaseCrawler
from app.models.exchange_rate import CurrencyDetail


class MongolBank(BaseCrawler):
    BANK_NAME = "MongolBank"

    def crawl(self) -> Dict[str, CurrencyDetail]:
        url = (
            f"{config.MONGOLBANK_URI}"
            f"?startdate={self.date}&enddate={self.date}"
        )
        resp = self.get(url)
        resp.raise_for_status()
        return self._parse(resp.text)

    def _parse(self, xml_text: str) -> Dict[str, CurrencyDetail]:
        rates = {}
        # Disable entity resolution and network access to prevent XXE attacks
        parser = etree.XMLParser(resolve_entities=False, no_network=True)
        root = etree.fromstring(xml_text.encode("utf-8"), parser)
        for row in root.xpath("//Ccy"):
            code = row.find("CcyNm_EN").text.lower()
            rate = self.parse_float(row.find("Rate").text)
            # MongolBank provides official central bank rate
            rates[code] = self.make_rate(noncash_buy=rate, noncash_sell=rate)
        return rates
