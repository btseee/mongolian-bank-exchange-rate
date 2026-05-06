import datetime
from unittest.mock import MagicMock, patch

from app.services.scraper import ScraperService


class TestScraperService:
    def test_init_default_date(self):
        service = ScraperService()
        assert service.date == datetime.date.today().isoformat()

    def test_init_custom_date(self):
        service = ScraperService(date="2026-01-15")
        assert service.date == "2026-01-15"

    def test_execute_success(self):
        service = ScraperService()
        mock_crawler_cls = MagicMock()
        mock_crawler_cls.BANK_NAME = "TestBank"
        mock_crawler = MagicMock()
        mock_crawler.crawl.return_value = {"usd": {}}
        mock_crawler_cls.return_value = mock_crawler

        bank, rates, error = service._execute(mock_crawler_cls)

        assert bank == "TestBank"
        assert rates == {"usd": {}}
        assert error is None

    def test_execute_failure(self):
        service = ScraperService()
        mock_crawler_cls = MagicMock()
        mock_crawler_cls.BANK_NAME = "TestBank"
        mock_crawler = MagicMock()
        mock_crawler.crawl.side_effect = Exception("Error")
        mock_crawler_cls.return_value = mock_crawler

        bank, rates, error = service._execute(mock_crawler_cls)

        assert bank == "TestBank"
        assert rates is None
        assert error is not None

    @patch("app.services.scraper.config")
    def test_run_all_parallel_executes_groups_and_saves(self, mock_config):
        mock_config.ENABLE_PARALLEL = True
        mock_config.MAX_WORKERS = 4
        mock_config.PLAYWRIGHT_MAX_WORKERS = 2
        service = ScraperService(date="2026-01-15")
        http_results = [("HttpBank", {"usd": {}}, None)]
        browser_results = [("BrowserBank", None, Exception("failed"))]

        with (
            patch.object(
                service,
                "_run_group",
                side_effect=[http_results, browser_results],
            ) as mock_run_group,
            patch.object(service, "_save") as mock_save,
        ):
            service.run_all()

        assert mock_run_group.call_count == 2
        saved_results = mock_save.call_args.args[0]
        assert sorted(result[0] for result in saved_results) == [
            "BrowserBank",
            "HttpBank",
        ]

    @patch("app.services.scraper.repository.save_rates")
    @patch("app.services.scraper.SessionLocal")
    def test_save_persists_successful_results_only(
        self, mock_session_local, mock_save_rates
    ):
        db = MagicMock()
        mock_session_local.return_value = db
        service = ScraperService(date="2026-01-15")

        service._save(
            [
                ("GoodBank", {"usd": {}}, None),
                ("FailedBank", None, Exception("crawl failed")),
            ]
        )

        mock_save_rates.assert_called_once()
        assert mock_save_rates.call_args.args[1].bank == "GoodBank"
        db.close.assert_called_once()


class TestScrapeBankMethod:
    @patch("app.crawlers.khanbank.KhanBank.crawl")
    def test_scrape_known_bank(self, mock_crawl):
        mock_crawl.return_value = {"usd": {}}
        service = ScraperService()
        result = service.scrape_bank("khanbank")
        assert result is not None

    def test_scrape_unknown_bank(self):
        service = ScraperService()
        result = service.scrape_bank("unknown_bank")
        assert result is None
