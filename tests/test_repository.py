"""Tests for the atomic upsert in app/db/repository.py.

The `test_db` fixture (tests/conftest.py) provides a fresh in-memory
SQLite session with the unique constraint on (bank_name, date) already
applied via Base.metadata.create_all.
"""

from datetime import date

from app.db import repository
from app.models.currency import CurrencyRate
from app.models.exchange_rate import ExchangeRate


def _rate(bank: str, day: str, value: float) -> ExchangeRate:
    return ExchangeRate(
        date=day,
        bank=bank,
        rates={"usd": {"cash": {"buy": value, "sell": value + 1}}},
    )


class TestSaveRatesUpsert:
    def test_creates_one_row(self, test_db):
        repository.save_rates(test_db, _rate("KhanBank", "2026-01-15", 100))

        rows = test_db.query(CurrencyRate).all()
        assert len(rows) == 1
        assert rows[0].bank_name == "KhanBank"

    def test_second_call_same_bank_and_date_updates_not_duplicates(
        self, test_db
    ):
        repository.save_rates(test_db, _rate("KhanBank", "2026-01-15", 100))
        repository.save_rates(test_db, _rate("KhanBank", "2026-01-15", 200))

        rows = test_db.query(CurrencyRate).all()
        assert len(rows) == 1
        assert rows[0].rates["usd"]["cash"]["buy"] == 200

    def test_different_banks_same_date_both_persist(self, test_db):
        repository.save_rates(test_db, _rate("KhanBank", "2026-01-15", 100))
        repository.save_rates(test_db, _rate("GolomtBank", "2026-01-15", 100))

        rows = test_db.query(CurrencyRate).all()
        assert len(rows) == 2
        assert {r.bank_name for r in rows} == {"KhanBank", "GolomtBank"}

    def test_returns_the_persisted_row(self, test_db):
        result = repository.save_rates(
            test_db, _rate("KhanBank", "2026-01-15", 100)
        )
        assert result.bank_name == "KhanBank"
        assert result.date == date(2026, 1, 15)
