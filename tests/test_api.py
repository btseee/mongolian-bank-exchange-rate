import datetime

from app.models.currency import CurrencyRate


class TestRootEndpoint:
    def test_root_returns_api_info(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "supported_banks" in data
        assert len(data["supported_banks"]) == 15

    def test_root_contains_endpoints(self, client):
        response = client.get("/")
        data = response.json()
        assert "/rates" in data["endpoints"]
        assert "/rates/latest" in data["endpoints"]


class TestHealthEndpoint:
    def test_health_returns_healthy(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestRatesEndpoints:
    def test_get_all_rates_empty(self, client):
        response = client.get("/rates")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_all_rates_with_data(self, client, test_db, sample_rate_data):
        rate = CurrencyRate(
            bank_name="KhanBank",
            date=datetime.date.today(),
            rates=sample_rate_data,
        )
        test_db.add(rate)
        test_db.commit()

        response = client.get("/rates")
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["bank_name"] == "KhanBank"

    def test_get_latest_rates(self, client, test_db, sample_rate_data):
        rate1 = CurrencyRate(
            bank_name="KhanBank",
            date=datetime.date.today(),
            rates=sample_rate_data,
        )
        rate2 = CurrencyRate(
            bank_name="GolomtBank",
            date=datetime.date.today(),
            rates=sample_rate_data,
        )
        test_db.add_all([rate1, rate2])
        test_db.commit()

        response = client.get("/rates/latest")
        assert response.status_code == 200
        assert len(response.json()) == 2


class TestRatesByBankEndpoints:
    def test_get_rates_by_bank(self, client, test_db, sample_rate_data):
        rate = CurrencyRate(
            bank_name="KhanBank",
            date=datetime.date.today(),
            rates=sample_rate_data,
        )
        test_db.add(rate)
        test_db.commit()

        response = client.get("/rates/bank/KhanBank")
        assert response.status_code == 200
        assert response.json()[0]["bank_name"] == "KhanBank"

    def test_get_rates_by_bank_not_found(self, client):
        response = client.get("/rates/bank/NonExistent")
        assert response.status_code == 404


class TestRatesByDateEndpoints:
    def test_get_rates_by_date(self, client, test_db, sample_rate_data):
        today = datetime.date.today()
        rate = CurrencyRate(
            bank_name="KhanBank", date=today, rates=sample_rate_data
        )
        test_db.add(rate)
        test_db.commit()

        response = client.get(f"/rates/date/{today.isoformat()}")
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_get_rates_by_date_not_found(self, client):
        response = client.get("/rates/date/2020-01-01")
        assert response.status_code == 404

    def test_get_rates_by_date_invalid(self, client):
        response = client.get("/rates/date/invalid")
        assert response.status_code == 400


class TestRatesByBankAndDate:
    def test_get_rate(self, client, test_db, sample_rate_data):
        today = datetime.date.today()
        rate = CurrencyRate(
            bank_name="KhanBank", date=today, rates=sample_rate_data
        )
        test_db.add(rate)
        test_db.commit()

        response = client.get(f"/rates/bank/KhanBank/date/{today.isoformat()}")
        assert response.status_code == 200
        assert response.json()["bank_name"] == "KhanBank"

    def test_get_rate_not_found(self, client):
        response = client.get("/rates/bank/KhanBank/date/2020-01-01")
        assert response.status_code == 404
