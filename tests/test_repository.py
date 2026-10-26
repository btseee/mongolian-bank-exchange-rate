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


class TestDateOrdering:
    """Rows are ranked by rate date, not by when they were written - a
    backfill of an older date must not displace the newest rate."""

    def test_latest_ignores_write_order(self, test_db):
        repository.save_rates(test_db, _rate("KhanBank", "2026-10-26", 100))
        repository.save_rates(test_db, _rate("KhanBank", "2026-01-15", 200))

        latest = repository.get_latest_rates(test_db)

        assert [(r.bank_name, r.date) for r in latest] == [
            ("KhanBank", date(2026, 10, 26))
        ]

    def test_latest_is_per_bank(self, test_db):
        repository.save_rates(test_db, _rate("KhanBank", "2026-10-26", 100))
        repository.save_rates(test_db, _rate("GolomtBank", "2026-10-20", 100))
        repository.save_rates(test_db, _rate("GolomtBank", "2026-10-10", 100))

        latest = repository.get_latest_rates(test_db)

        assert {(r.bank_name, r.date) for r in latest} == {
            ("KhanBank", date(2026, 10, 26)),
            ("GolomtBank", date(2026, 10, 20)),
        }

    def test_bank_list_is_newest_date_first(self, test_db):
        repository.save_rates(test_db, _rate("KhanBank", "2026-10-26", 100))
        repository.save_rates(test_db, _rate("KhanBank", "2026-01-15", 100))

        rows = repository.get_rates_by_bank(test_db, "KhanBank")

        assert [r.date for r in rows] == [
            date(2026, 10, 26),
            date(2026, 1, 15),
        ]

    def test_all_rates_list_is_newest_date_first(self, test_db):
        repository.save_rates(test_db, _rate("KhanBank", "2026-10-26", 100))
        repository.save_rates(test_db, _rate("KhanBank", "2026-01-15", 100))

        rows = repository.get_all_rates(test_db)

        assert [r.date for r in rows] == [
            date(2026, 10, 26),
            date(2026, 1, 15),
        ]
