"""Tests for the admin crawl/backfill endpoints (app/api/routers/admin.py).

Real crawling/backfill logic is mocked out here - these tests only cover
auth, request validation, status codes, and the job-lock contract. Live
network behavior is verified separately, outside the test suite.
"""

from unittest.mock import patch

import pytest

from app.config import config
from app.services import admin_jobs

ADMIN_KEY = "test-admin-secret"


@pytest.fixture(autouse=True)
def _reset_admin_lock():
    """admin_jobs holds module-level lock/state - reset around every test
    so a lock held (or released) by one test can't leak into the next."""
    if admin_jobs._lock.locked():
        admin_jobs._lock.release()
    admin_jobs._state.update(
        is_running=False,
        job_type=None,
        started_at=None,
        finished_at=None,
        last_result=None,
        last_error=None,
    )
    yield
    if admin_jobs._lock.locked():
        admin_jobs._lock.release()


class TestAdminAuth:
    def test_crawl_503_when_key_unset(self, client, monkeypatch):
        monkeypatch.setattr(config, "ADMIN_API_KEY", "")
        response = client.post("/api/admin/crawl")
        assert response.status_code == 503

    def test_status_503_when_key_unset(self, client, monkeypatch):
        monkeypatch.setattr(config, "ADMIN_API_KEY", "")
        response = client.get("/api/admin/status")
        assert response.status_code == 503

    def test_401_when_key_missing(self, client, monkeypatch):
        monkeypatch.setattr(config, "ADMIN_API_KEY", ADMIN_KEY)
        response = client.post("/api/admin/crawl")
        assert response.status_code == 401

    def test_401_when_key_wrong(self, client, monkeypatch):
        monkeypatch.setattr(config, "ADMIN_API_KEY", ADMIN_KEY)
        response = client.post(
            "/api/admin/crawl", headers={"X-Admin-Key": "wrong"}
        )
        assert response.status_code == 401


class TestAdminCrawl:
    def test_returns_202_and_runs_background_task(self, client, monkeypatch):
        monkeypatch.setattr(config, "ADMIN_API_KEY", ADMIN_KEY)
        with patch("app.services.admin_jobs.ScraperService") as mock_service:
            mock_service.return_value.run_all.return_value = {
                "succeeded": 15,
                "failed": 0,
                "failed_banks": [],
            }
            response = client.post(
                "/api/admin/crawl", headers={"X-Admin-Key": ADMIN_KEY}
            )

        assert response.status_code == 202
        assert response.json()["status"] == "started"
        assert admin_jobs.get_status()["last_result"]["succeeded"] == 15

    def test_returns_409_when_already_running(self, client, monkeypatch):
        monkeypatch.setattr(config, "ADMIN_API_KEY", ADMIN_KEY)
        assert admin_jobs.try_start("crawl")

        response = client.post(
            "/api/admin/crawl", headers={"X-Admin-Key": ADMIN_KEY}
        )
        assert response.status_code == 409


class TestAdminBackfill:
    def test_rejects_reversed_range(self, client, monkeypatch):
        monkeypatch.setattr(config, "ADMIN_API_KEY", ADMIN_KEY)
        response = client.post(
            "/api/admin/backfill",
            headers={"X-Admin-Key": ADMIN_KEY},
            json={"start": "2026-02-01", "end": "2026-01-31"},
        )
        assert response.status_code == 400

    def test_rejects_end_without_start(self, client, monkeypatch):
        monkeypatch.setattr(config, "ADMIN_API_KEY", ADMIN_KEY)
        response = client.post(
            "/api/admin/backfill",
            headers={"X-Admin-Key": ADMIN_KEY},
            json={"end": "2026-01-31"},
        )
        assert response.status_code == 400

    def test_returns_202_with_resolved_range(self, client, monkeypatch):
        monkeypatch.setattr(config, "ADMIN_API_KEY", ADMIN_KEY)
        with patch("app.services.admin_jobs.run_backfill_range"):
            response = client.post(
                "/api/admin/backfill",
                headers={"X-Admin-Key": ADMIN_KEY},
                json={"start": "2026-01-01", "end": "2026-01-02"},
            )

        assert response.status_code == 202
        body = response.json()
        assert body["start"] == "2026-01-01"
        assert body["end"] == "2026-01-02"

    def test_returns_409_when_already_running(self, client, monkeypatch):
        monkeypatch.setattr(config, "ADMIN_API_KEY", ADMIN_KEY)
        assert admin_jobs.try_start("crawl")

        response = client.post(
            "/api/admin/backfill",
            headers={"X-Admin-Key": ADMIN_KEY},
            json={},
        )
        assert response.status_code == 409


class TestAdminSingleBankCrawl:
    def test_unknown_bank_returns_422(self, client, monkeypatch):
        monkeypatch.setattr(config, "ADMIN_API_KEY", ADMIN_KEY)
        response = client.post(
            "/api/admin/crawl/NotABank", headers={"X-Admin-Key": ADMIN_KEY}
        )
        assert response.status_code == 422

    def test_crawl_failure_returns_502(self, client, monkeypatch):
        monkeypatch.setattr(config, "ADMIN_API_KEY", ADMIN_KEY)
        with patch("app.services.admin_jobs.ScraperService") as mock_service:
            mock_service.return_value.scrape_bank.return_value = None
            response = client.post(
                "/api/admin/crawl/KhanBank",
                headers={"X-Admin-Key": ADMIN_KEY},
            )

        assert response.status_code == 502

    def test_success_persists_and_returns_rates(self, client, monkeypatch):
        monkeypatch.setattr(config, "ADMIN_API_KEY", ADMIN_KEY)
        with (
            patch("app.services.admin_jobs.ScraperService") as mock_service,
            patch(
                "app.services.admin_jobs.repository.save_rates"
            ) as mock_save,
            patch("app.services.admin_jobs.SessionLocal"),
        ):
            mock_service.return_value.date = "2026-01-15"
            mock_service.return_value.scrape_bank.return_value = {
                "usd": {"cash": {"buy": 1, "sell": 2}}
            }
            response = client.post(
                "/api/admin/crawl/KhanBank",
                headers={"X-Admin-Key": ADMIN_KEY},
            )

        assert response.status_code == 200
        assert response.json()["bank_name"] == "KhanBank"
        mock_save.assert_called_once()

    def test_returns_409_when_already_running(self, client, monkeypatch):
        monkeypatch.setattr(config, "ADMIN_API_KEY", ADMIN_KEY)
        assert admin_jobs.try_start("crawl")

        response = client.post(
            "/api/admin/crawl/KhanBank", headers={"X-Admin-Key": ADMIN_KEY}
        )
        assert response.status_code == 409


class TestAdminStatus:
    def test_reports_idle_by_default(self, client, monkeypatch):
        monkeypatch.setattr(config, "ADMIN_API_KEY", ADMIN_KEY)
        response = client.get(
            "/api/admin/status", headers={"X-Admin-Key": ADMIN_KEY}
        )
        assert response.status_code == 200
        assert response.json()["is_running"] is False
