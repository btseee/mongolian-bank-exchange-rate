from abc import ABC, abstractmethod
from typing import Dict, Optional

import requests
import urllib3
from playwright.sync_api import sync_playwright
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.config import config
from app.models.exchange_rate import CurrencyDetail, Rate

if not config.SSL_VERIFY:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def _build_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=2,
        backoff_factor=1,
        status_forcelist=(500, 502, 503, 504),
        allowed_methods=frozenset(["GET", "POST"]),
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


class BaseCrawler(ABC):
    """Base class for HTTP API crawlers."""

    BANK_NAME: str = ""
    DEFAULT_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/html;q=0.9, */*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,mn;q=0.8",
    }

    def __init__(self, date: str):
        self.date = date
        self.timeout = config.REQUEST_TIMEOUT
        self.ssl_verify = config.SSL_VERIFY
        self.session = _build_session()

    @abstractmethod
    def crawl(self) -> Dict[str, CurrencyDetail]:
        pass

    def get(self, url: str, **kwargs) -> requests.Response:
        kwargs.setdefault("timeout", self.timeout)
        kwargs.setdefault("verify", self.ssl_verify)
        headers = kwargs.get("headers", {})
        kwargs["headers"] = {**self.DEFAULT_HEADERS, **headers}
        return self.session.get(url, **kwargs)

    def post(self, url: str, **kwargs) -> requests.Response:
        kwargs.setdefault("timeout", self.timeout)
        kwargs.setdefault("verify", self.ssl_verify)
        headers = kwargs.get("headers", {})
        kwargs["headers"] = {**self.DEFAULT_HEADERS, **headers}
        return self.session.post(url, **kwargs)

    @staticmethod
    def parse_float(value) -> Optional[float]:
        if value is None:
            return None
        try:
            if isinstance(value, (int, float)):
                return float(value) if value != 0 else None
            cleaned = (
                str(value)
                .strip()
                .replace(",", "")
                .replace(" ", "")
                .replace("\xa0", "")
            )
            if not cleaned or cleaned == "-" or cleaned == "0":
                return None
            return float(cleaned)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def make_rate(
        cash_buy=None, cash_sell=None, noncash_buy=None, noncash_sell=None
    ) -> CurrencyDetail:
        return CurrencyDetail(
            cash=Rate(buy=cash_buy, sell=cash_sell),
            noncash=Rate(buy=noncash_buy, sell=noncash_sell),
        )


class PlaywrightCrawler(BaseCrawler):
    """Base class for Playwright-based crawlers."""

    def __init__(self, date: str):
        super().__init__(date)
        self.timeout = config.PLAYWRIGHT_TIMEOUT

    # Bank pages only need to render tables/JSON, so blocking images/fonts/
    # media cuts Chromium's memory footprint substantially - load-bearing on
    # Render's free 512MB tier, where this runs alongside the HTTP crawler
    # pool at the same time (see ScraperService.run_all).
    _BLOCKED_RESOURCE_TYPES = frozenset({"image", "media", "font"})

    def crawl(self) -> Dict[str, CurrencyDetail]:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--disable-dev-shm-usage", "--disable-gpu"],
            )
            context = browser.new_context(
                ignore_https_errors=not self.ssl_verify
            )
            context.set_default_timeout(self.timeout)
            context.route("**/*", self._block_heavy_resources)
            page = context.new_page()
            try:
                rates = self._crawl_page(page)
            finally:
                browser.close()
        return rates

    @classmethod
    def _block_heavy_resources(cls, route) -> None:
        if route.request.resource_type in cls._BLOCKED_RESOURCE_TYPES:
            route.abort()
        else:
            route.continue_()

    @abstractmethod
    def _crawl_page(self, page) -> Dict[str, CurrencyDetail]:
        pass
