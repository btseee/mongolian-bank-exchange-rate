from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Column,
    Date,
    DateTime,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()

UNIQUE_BANK_DATE_CONSTRAINT = "uq_currency_rates_bank_name_date"


def utc_now():
    return datetime.now(timezone.utc)


class CurrencyRate(Base):
    __tablename__ = "currency_rates"
    __table_args__ = (
        UniqueConstraint(
            "bank_name", "date", name=UNIQUE_BANK_DATE_CONSTRAINT
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    bank_name = Column(String, index=True)
    date = Column(Date, index=True)
    rates = Column(JSON)
    timestamp = Column(DateTime, default=utc_now)
