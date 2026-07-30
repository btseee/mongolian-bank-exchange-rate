from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.config import config
from app.models.currency import UNIQUE_BANK_DATE_CONSTRAINT, Base
from app.utils.logger import logger

_is_sqlite = config.DATABASE_URL.startswith("sqlite")
_connect_args = {"check_same_thread": False} if _is_sqlite else {}
engine = create_engine(config.DATABASE_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)
    _ensure_unique_index()


def _ensure_unique_index():
    """Self-healing schema fix for deployments predating the unique
    constraint on (bank_name, date). No-ops if it already exists."""
    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS "
                    f"{UNIQUE_BANK_DATE_CONSTRAINT} "
                    "ON currency_rates (bank_name, date)"
                )
            )
    except IntegrityError:
        logger.error(
            "Cannot create unique index on currency_rates(bank_name, date) "
            "- duplicate rows already exist. Run this once, then restart:\n"
            "DELETE FROM currency_rates WHERE id NOT IN "
            "(SELECT MAX(id) FROM currency_rates GROUP BY bank_name, date);"
        )
        raise


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
