from datetime import date

import pytest

from scripts.backfill import parse_date_args
from scripts.cron import daily_time_from_cron


def test_daily_time_from_cron_returns_schedule_time():
    assert daily_time_from_cron("0 9 * * *") == "09:00"
    assert daily_time_from_cron("30 23 * * *") == "23:30"


@pytest.mark.parametrize(
    "cron_expression",
    [
        "0 9 * * 1",
        "0 9 1 * *",
        "0 9 * *",
        "60 9 * * *",
        "0 24 * * *",
    ],
)
def test_daily_time_from_cron_rejects_unsupported_values(cron_expression):
    with pytest.raises(ValueError):
        daily_time_from_cron(cron_expression)


def test_parse_date_args_returns_default_range():
    start, end = parse_date_args([])

    assert start == date(2026, 1, 1)
    assert end == date.today()


def test_parse_date_args_returns_requested_range():
    start, end = parse_date_args(["2026-01-01", "2026-01-31"])

    assert start == date(2026, 1, 1)
    assert end == date(2026, 1, 31)


def test_parse_date_args_rejects_reversed_range():
    with pytest.raises(ValueError):
        parse_date_args(["2026-02-01", "2026-01-31"])
