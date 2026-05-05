import datetime
from unittest.mock import MagicMock, patch

from app.crawlers import (
    ArigBank,
    CapitronBank,
    GolomtBank,
    KhanBank,
    MongolBank,
    StateBank,
    XacBank,
)
from app.crawlers.base import BaseCrawler


class TestKhanBank:
    @patch("app.crawlers.khanbank.BaseCrawler.get")
    def test_crawl_success(self, mock_get, sample_khanbank_response):
        mock_resp = MagicMock()
        mock_resp.json.return_value = sample_khanbank_response
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        crawler = KhanBank(datetime.date.today().isoformat())
        rates = crawler.crawl()

        assert rates is not None
        assert "usd" in rates
        assert rates["usd"].cash.buy == 3420.5
        assert rates["usd"].cash.sell == 3450.0

    @patch("app.crawlers.khanbank.BaseCrawler.get")
    def test_crawl_empty(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = []
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        crawler = KhanBank(datetime.date.today().isoformat())
        rates = crawler.crawl()
        assert rates == {}


class TestGolomtBank:
    @patch("app.crawlers.golomt.BaseCrawler.get")
    def test_crawl_success(self, mock_get, sample_golomt_response):
        mock_resp = MagicMock()
        mock_resp.json.return_value = sample_golomt_response
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        crawler = GolomtBank(datetime.date.today().isoformat())
        rates = crawler.crawl()

        assert rates is not None
        assert "usd" in rates
        assert rates["usd"].cash.buy == 3420.5


class TestXacBank:
    @patch("app.crawlers.xacbank.BaseCrawler.get")
    def test_crawl_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "docs": [
                {
                    "code": "USD",
                    "buyCash": 3420.5,
                    "sellCash": 3450.0,
                    "buy": 3415.0,
                    "sell": 3455.0,
                }
            ]
        }
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        crawler = XacBank(datetime.date.today().isoformat())
        rates = crawler.crawl()

        assert rates is not None
        assert "usd" in rates
        assert rates["usd"].cash.buy == 3420.5


class TestArigBank:
    @patch("app.crawlers.arigbank.config")
    @patch("app.crawlers.arigbank.BaseCrawler.post")
    def test_crawl_success(self, mock_post, mock_config):
        mock_config.ARIGBANK_BEARER_TOKEN = "test-token"
        mock_config.ARIGBANK_API_URL = "https://api.example.com"
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "data": [
                {
                    "curCode": "USD",
                    "belenBuyRate": 3420.5,
                    "belenSellRate": 3450.0,
                    "belenBusBuyRate": 3415.0,
                    "belenBusSellRate": 3455.0,
                }
            ]
        }
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        crawler = ArigBank(datetime.date.today().isoformat())
        rates = crawler.crawl()

        assert rates is not None
        assert "usd" in rates
        assert rates["usd"].cash.buy == 3420.5


class TestStateBank:
    @patch("app.crawlers.statebank.BaseCrawler.get")
    def test_crawl_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "data": [
                {"CurrencyCode": "USD", "BuyRate": 3420.5, "SellRate": 3450.0}
            ]
        }
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        crawler = StateBank(datetime.date.today().isoformat())
        rates = crawler.crawl()

        assert rates is not None
        assert "usd" in rates
        assert rates["usd"].cash.buy == 3420.5


class TestMongolBank:
    @patch("app.crawlers.mongolbank.BaseCrawler.get")
    def test_crawl_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.text = """<?xml version="1.0"?>
        <Root>
            <Ccy>
                <CcyNm_EN>USD</CcyNm_EN>
                <Rate>3435.5</Rate>
            </Ccy>
        </Root>"""
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        crawler = MongolBank(datetime.date.today().isoformat())
        rates = crawler.crawl()

        assert rates is not None
        assert "usd" in rates
        assert rates["usd"].noncash.buy == 3435.5
        assert rates["usd"].noncash.sell == 3435.5


class TestCapitronBank:
    @patch("app.crawlers.capitronbank.BaseCrawler.get")
    def test_crawl_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = [
            {
                "currencyCode": "USD",
                "cashBuyRate": 3420.5,
                "cashSellRate": 3450.0,
                "transferBuyRate": 3415.0,
                "transferSellRate": 3455.0,
            }
        ]
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        crawler = CapitronBank(datetime.date.today().isoformat())
        rates = crawler.crawl()

        assert rates is not None
        assert "usd" in rates
        assert rates["usd"].cash.buy == 3420.5


class TestBaseCrawler:
    def test_parse_float_valid(self):
        assert BaseCrawler.parse_float(3420.5) == 3420.5
        assert BaseCrawler.parse_float("3420.5") == 3420.5
        assert BaseCrawler.parse_float("3,420.5") == 3420.5

    def test_parse_float_invalid(self):
        assert BaseCrawler.parse_float(None) is None
        assert BaseCrawler.parse_float("") is None
        assert BaseCrawler.parse_float("-") is None
        assert BaseCrawler.parse_float(0) is None

    def test_parse_float_whitespace(self):
        assert BaseCrawler.parse_float(" 3420.5 ") == 3420.5
        assert BaseCrawler.parse_float("3 420.5") == 3420.5

    def test_make_rate(self):
        rate = BaseCrawler.make_rate(
            cash_buy=3420.5,
            cash_sell=3450.0,
            noncash_buy=3415.0,
            noncash_sell=3455.0,
        )
        assert rate.cash.buy == 3420.5
        assert rate.cash.sell == 3450.0
        assert rate.noncash.buy == 3415.0
        assert rate.noncash.sell == 3455.0


class TestAllCrawlersImport:
    """Test that all crawlers can be imported and have correct attributes."""

    def test_http_crawlers_have_bank_name(self):
        from app.crawlers import HTTP_CRAWLERS

        for crawler_cls in HTTP_CRAWLERS:
            assert hasattr(crawler_cls, "BANK_NAME")
            assert crawler_cls.BANK_NAME != ""

    def test_playwright_crawlers_have_bank_name(self):
        from app.crawlers import PLAYWRIGHT_CRAWLERS

        for crawler_cls in PLAYWRIGHT_CRAWLERS:
            assert hasattr(crawler_cls, "BANK_NAME")
            assert crawler_cls.BANK_NAME != ""

    def test_all_crawlers_count(self):
        from app.crawlers import ALL_CRAWLERS

        assert len(ALL_CRAWLERS) == 15

    def test_crawler_map_keys(self):
        from app.crawlers import CRAWLER_MAP

        expected_banks = [
            "khanbank",
            "golomtbank",
            "xacbank",
            "arigbank",
            "statebank",
            "mongolbank",
            "capitronbank",
            "naimansharga",
            "sendmn",
            "tdbm",
            "bogdbank",
            "ckbank",
            "nibank",
            "transbank",
            "mbank",
        ]
        for bank in expected_banks:
            assert bank in CRAWLER_MAP


class TestPlaywrightCrawlersExist:
    """Test Playwright crawlers can be instantiated."""

    def test_tdbm_instantiation(self):
        from app.crawlers import TDBM

        crawler = TDBM(datetime.date.today().isoformat())
        assert crawler.BANK_NAME == "TDBM"

    def test_bogdbank_instantiation(self):
        from app.crawlers import BogdBank

        crawler = BogdBank(datetime.date.today().isoformat())
        assert crawler.BANK_NAME == "BogdBank"

    def test_ckbank_instantiation(self):
        from app.crawlers import CKBank

        crawler = CKBank(datetime.date.today().isoformat())
        assert crawler.BANK_NAME == "CKBank"

    def test_nibank_instantiation(self):
        from app.crawlers import NIBank

        crawler = NIBank(datetime.date.today().isoformat())
        assert crawler.BANK_NAME == "NIBank"

    def test_transbank_instantiation(self):
        from app.crawlers import TransBank

        crawler = TransBank(datetime.date.today().isoformat())
        assert crawler.BANK_NAME == "TransBank"

    def test_mbank_instantiation(self):
        from app.crawlers import MBank

        crawler = MBank(datetime.date.today().isoformat())
        assert crawler.BANK_NAME == "MBank"


class TestSendMN:
    @patch("app.crawlers.sendmn.BaseCrawler.get")
    def test_crawl_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "fields": {
                "data": {
                    "arrayValue": {
                        "values": [
                            {
                                "mapValue": {
                                    "fields": {
                                        "currency": {"stringValue": "USD"},
                                        "buy": {"stringValue": "3570"},
                                        "sell": {"stringValue": "3615"},
                                    }
                                }
                            },
                            {
                                "mapValue": {
                                    "fields": {
                                        "currency": {"stringValue": "EUR"},
                                        "buy": {"stringValue": "3900"},
                                        "sell": {"stringValue": "3950"},
                                    }
                                }
                            },
                        ]
                    }
                }
            }
        }
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        from app.crawlers.sendmn import SendMN

        crawler = SendMN(datetime.date.today().isoformat())
        rates = crawler.crawl()

        assert rates is not None
        assert "usd" in rates
        assert rates["usd"].cash.buy == 3570.0
        assert rates["usd"].cash.sell == 3615.0
        assert rates["usd"].noncash.buy == 3570.0
        assert rates["usd"].noncash.sell == 3615.0
        assert "eur" in rates

    @patch("app.crawlers.sendmn.BaseCrawler.get")
    def test_crawl_empty_values(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"fields": {}}
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        from app.crawlers.sendmn import SendMN

        crawler = SendMN(datetime.date.today().isoformat())
        rates = crawler.crawl()
        assert rates == {}

    @patch("app.crawlers.sendmn.BaseCrawler.get")
    def test_crawl_skips_invalid_code(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "fields": {
                "data": {
                    "arrayValue": {
                        "values": [
                            {
                                "mapValue": {
                                    "fields": {
                                        "currency": {"stringValue": "INVALID"},
                                        "buy": {"stringValue": "100"},
                                        "sell": {"stringValue": "110"},
                                    }
                                }
                            }
                        ]
                    }
                }
            }
        }
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        from app.crawlers.sendmn import SendMN

        crawler = SendMN(datetime.date.today().isoformat())
        rates = crawler.crawl()
        assert rates == {}


class TestNaimanSharga:
    @patch("app.crawlers.naimansharga.BaseCrawler.get")
    def test_crawl_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "fields": {
                "USD": {
                    "mapValue": {
                        "fields": {
                            "avah": {"doubleValue": 3582},
                            "zarah": {"doubleValue": 3587},
                        }
                    }
                },
                "EUR": {
                    "mapValue": {
                        "fields": {
                            "avah": {"doubleValue": 3900},
                            "zarah": {"doubleValue": 3960},
                        }
                    }
                },
                "createdAt": {"timestampValue": "2026-05-05T00:00:00Z"},
                "updatedAt": {"timestampValue": "2026-05-05T08:00:00Z"},
            }
        }
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        from app.crawlers.naimansharga import NaimanSharga

        crawler = NaimanSharga(datetime.date.today().isoformat())
        rates = crawler.crawl()

        assert rates is not None
        assert "usd" in rates
        assert rates["usd"].cash.buy == 3582.0
        assert rates["usd"].cash.sell == 3587.0
        assert rates["usd"].noncash.buy == 3582.0
        assert rates["usd"].noncash.sell == 3587.0
        assert "eur" in rates
        assert "createdat" not in rates
        assert "updatedat" not in rates

    @patch("app.crawlers.naimansharga.BaseCrawler.get")
    def test_crawl_fallback_to_yesterday(self, mock_get):
        today = datetime.date.today().isoformat()
        yesterday = (
            datetime.date.today() - datetime.timedelta(days=1)
        ).isoformat()

        not_found = MagicMock()
        not_found.status_code = 404

        found = MagicMock()
        found.status_code = 200
        found.json.return_value = {
            "fields": {
                "USD": {
                    "mapValue": {
                        "fields": {
                            "avah": {"doubleValue": 3580},
                            "zarah": {"doubleValue": 3585},
                        }
                    }
                },
            }
        }
        found.raise_for_status = MagicMock()

        mock_get.side_effect = [not_found, found]

        from app.crawlers.naimansharga import NaimanSharga

        crawler = NaimanSharga(today)
        rates = crawler.crawl()

        assert "usd" in rates
        assert mock_get.call_count == 2

    @patch("app.crawlers.naimansharga.BaseCrawler.get")
    def test_crawl_skips_non_3char_codes(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "fields": {
                "USDD": {
                    "mapValue": {
                        "fields": {
                            "avah": {"doubleValue": 3582},
                            "zarah": {"doubleValue": 3587},
                        }
                    }
                },
                "updatedAt": {"timestampValue": "2026-05-05T08:00:00Z"},
            }
        }
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        from app.crawlers.naimansharga import NaimanSharga

        crawler = NaimanSharga(datetime.date.today().isoformat())
        rates = crawler.crawl()
        assert rates == {}
