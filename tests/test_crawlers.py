import datetime
from unittest.mock import MagicMock, patch

import requests

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
        mock_config.ARIGBANK_SIGNIN_URL = "https://api.example.com/signIn"
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

    @patch("app.crawlers.arigbank.config")
    @patch("app.crawlers.arigbank.BaseCrawler.post")
    def test_crawl_signs_in_when_token_not_configured(
        self, mock_post, mock_config
    ):
        mock_config.ARIGBANK_BEARER_TOKEN = ""
        mock_config.ARIGBANK_API_URL = "https://api.example.com/getRate"
        mock_config.ARIGBANK_SIGNIN_URL = "https://api.example.com/signIn"

        sign_in_resp = MagicMock()
        sign_in_resp.json.return_value = {"token": "fresh-token"}
        sign_in_resp.raise_for_status = MagicMock()

        rate_resp = MagicMock()
        rate_resp.status_code = 200
        rate_resp.json.return_value = {
            "status": 200,
            "message": "Амжилттай",
            "data": [
                {
                    "curCode": "USD",
                    "belenBuyRate": 3568,
                    "belenSellRate": 3596,
                    "belenBusBuyRate": 3568,
                    "belenBusSellRate": 3578,
                }
            ],
        }
        rate_resp.raise_for_status = MagicMock()
        mock_post.side_effect = [sign_in_resp, rate_resp]

        crawler = ArigBank(datetime.date.today().isoformat())
        rates = crawler.crawl()

        assert rates["usd"].cash.buy == 3568.0
        assert (
            mock_post.call_args_list[0].args[0]
            == mock_config.ARIGBANK_SIGNIN_URL
        )
        assert mock_post.call_args_list[1].kwargs["headers"][
            "Authorization"
        ] == ("Bearer fresh-token")

    @patch("app.crawlers.arigbank.config")
    @patch("app.crawlers.arigbank.BaseCrawler.post")
    def test_crawl_refreshes_expired_configured_token(
        self, mock_post, mock_config
    ):
        mock_config.ARIGBANK_BEARER_TOKEN = "expired-token"
        mock_config.ARIGBANK_API_URL = "https://api.example.com/getRate"
        mock_config.ARIGBANK_SIGNIN_URL = "https://api.example.com/signIn"

        expired_resp = MagicMock()
        expired_resp.status_code = 200
        expired_resp.json.return_value = {
            "status": 401,
            "message": "Token expired!",
            "data": None,
        }
        expired_resp.raise_for_status = MagicMock()

        sign_in_resp = MagicMock()
        sign_in_resp.json.return_value = {"token": "fresh-token"}
        sign_in_resp.raise_for_status = MagicMock()

        rate_resp = MagicMock()
        rate_resp.status_code = 200
        rate_resp.json.return_value = {
            "status": 200,
            "data": [
                {
                    "curCode": "USD",
                    "belenBuyRate": 3568,
                    "belenSellRate": 3596,
                    "belenBusBuyRate": 3568,
                    "belenBusSellRate": 3578,
                }
            ],
        }
        rate_resp.raise_for_status = MagicMock()
        mock_post.side_effect = [expired_resp, sign_in_resp, rate_resp]

        crawler = ArigBank(datetime.date.today().isoformat())
        rates = crawler.crawl()

        assert rates["usd"].noncash.sell == 3578.0
        assert len(mock_post.call_args_list) == 3


class TestStateBank:
    @patch("app.crawlers.statebank.BaseCrawler.get")
    def test_crawl_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = [
            {
                "curCode": "USD",
                "cashBuy": 3420.5,
                "cashSale": 3450.0,
                "nonCashBuy": 3415.0,
                "nonCashSale": 3455.0,
            }
        ]
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        crawler = StateBank(datetime.date.today().isoformat())
        rates = crawler.crawl()

        assert rates is not None
        assert "usd" in rates
        assert rates["usd"].cash.buy == 3420.5
        assert rates["usd"].noncash.sell == 3455.0

    def test_parse_legacy_wrapped_response(self):
        crawler = StateBank(datetime.date.today().isoformat())

        rates = crawler._parse(
            [
                {
                    "CurrencyCode": "USD",
                    "BuyRate": 3420.5,
                    "SellRate": 3450.0,
                }
            ]
        )

        assert rates["usd"].cash.buy == 3420.5


class TestMongolBank:
    @patch("app.crawlers.mongolbank.BaseCrawler.post")
    def test_crawl_success(self, mock_post):
        today = datetime.date.today().isoformat()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "success": True,
            "data": [
                {
                    "RATE_DATE": today,
                    "USD": "3,575.94",
                    "EUR": "4,197.62",
                }
            ],
        }
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        crawler = MongolBank(today)
        rates = crawler.crawl()

        assert rates is not None
        assert "usd" in rates
        assert rates["usd"].noncash.buy == 3575.94
        assert rates["usd"].noncash.sell == 3575.94

    def test_parse_legacy_xml(self):
        crawler = MongolBank(datetime.date.today().isoformat())

        rates = crawler._parse("""<?xml version="1.0"?>
            <Root>
                <Ccy>
                    <CcyNm_EN>USD</CcyNm_EN>
                    <Rate>3435.5</Rate>
                </Ccy>
            </Root>""")

        assert rates["usd"].noncash.buy == 3435.5
        assert rates["usd"].noncash.sell == 3435.5

    def test_parse_recovers_from_unescaped_entity(self):
        crawler = MongolBank(datetime.date.today().isoformat())

        rates = crawler._parse("""<?xml version="1.0"?>
            <Root>
                <Ccy>
                    <CcyNm_EN>USD</CcyNm_EN>
                    <CcyNm_MN>Ам доллар & бусад</CcyNm_MN>
                    <Rate>3435.5</Rate>
                </Ccy>
            </Root>""")

        assert rates["usd"].noncash.buy == 3435.5


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

    def test_parse_current_lowercase_response(self):
        crawler = CapitronBank(datetime.date.today().isoformat())

        rates = crawler._parse(
            [
                {
                    "curcode": "USD",
                    "buyrate": "3569.0",
                    "salerate": "3595.0",
                }
            ]
        )

        assert rates["usd"].cash.buy == 3569.0
        assert rates["usd"].cash.sell == 3595.0
        assert rates["usd"].noncash.buy == 3569.0


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

    def test_mbank_is_grouped_as_http_crawler(self):
        from app.crawlers import HTTP_CRAWLERS, PLAYWRIGHT_CRAWLERS, MBank

        assert MBank in HTTP_CRAWLERS
        assert MBank not in PLAYWRIGHT_CRAWLERS


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


class TestNIBank:
    def test_crawl_page_parses_all_four_rate_fields(self):
        from app.crawlers import NIBank

        block_text = (
            "USD United States Dollar\n"
            "Бэлэн авах\n3400.00\n"
            "Бэлэн зарах\n3450.00\n"
            "Бэлэн бус авах\n3410.00\n"
            "Бэлэн бус зарах\n3440.00\n"
        )
        mock_block = MagicMock()
        mock_block.inner_text.return_value = block_text

        mock_page = MagicMock()
        mock_page.locator.return_value.all.return_value = [mock_block]

        crawler = NIBank(datetime.date.today().isoformat())
        rates = crawler._crawl_page(mock_page)

        assert rates["usd"].cash.buy == 3400.0
        assert rates["usd"].cash.sell == 3450.0
        assert rates["usd"].noncash.buy == 3410.0
        assert rates["usd"].noncash.sell == 3440.0


class TestTDBM:
    def test_parse_html_table(self):
        from app.crawlers import TDBM

        crawler = TDBM(datetime.date.today().isoformat())
        rates = crawler._parse_html_table("""
            <table class="table-hover">
                <tbody>
                    <tr><td>Currency</td><td>Mongol Bank</td></tr>
                    <tr><td>Buy</td><td>Sell</td></tr>
                    <tr>
                        <td></td><td>USD</td><td>United States Dollar</td>
                        <td>3576.12</td><td>3569.00</td><td>3577.00</td>
                        <td>3569.00</td><td>3594.00</td>
                    </tr>
                </tbody>
            </table>
            """)

        assert rates["usd"].cash.buy == 3569.0
        assert rates["usd"].cash.sell == 3594.0
        assert rates["usd"].noncash.buy == 3569.0
        assert rates["usd"].noncash.sell == 3577.0

    @patch("app.crawlers.base.PlaywrightCrawler.crawl")
    @patch("app.crawlers.base.BaseCrawler.get")
    def test_crawl_falls_back_to_playwright_on_static_request_error(
        self, mock_get, mock_playwright_crawl
    ):
        from app.crawlers import TDBM

        mock_get.side_effect = requests.RequestException("network failed")
        mock_playwright_crawl.return_value = {"usd": MagicMock()}

        crawler = TDBM(datetime.date.today().isoformat())

        assert crawler.crawl() == {
            "usd": mock_playwright_crawl.return_value["usd"]
        }
        mock_playwright_crawl.assert_called_once_with()


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

    @patch("app.crawlers.naimansharga.config")
    @patch("app.crawlers.naimansharga.BaseCrawler.get")
    def test_crawl_appends_date_before_firestore_query(
        self, mock_get, mock_config
    ):
        today = datetime.date.today().isoformat()
        mock_config.NSHARGA_FIRESTORE_BASE_URL = (
            "https://firestore.googleapis.com/v1/projects/app/databases/"
            "(default)/documents/currency_rates?key=abc123"
        )
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "fields": {
                "USD": {
                    "mapValue": {
                        "fields": {
                            "avah": {"integerValue": "3582"},
                            "zarah": {"stringValue": "3587"},
                        }
                    }
                }
            }
        }
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        from app.crawlers.naimansharga import NaimanSharga

        crawler = NaimanSharga(today)
        rates = crawler.crawl()

        expected_url = (
            "https://firestore.googleapis.com/v1/projects/app/databases/"
            f"(default)/documents/currency_rates/{today}?key=abc123"
        )
        assert mock_get.call_args.args[0] == expected_url
        assert rates["usd"].cash.buy == 3582.0
        assert rates["usd"].cash.sell == 3587.0

    @patch("app.crawlers.naimansharga.BaseCrawler.get")
    def test_crawl_fallback_to_yesterday(self, mock_get):
        today = datetime.date.today().isoformat()

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
