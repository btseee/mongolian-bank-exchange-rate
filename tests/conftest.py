import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.api import _rate_limit_hits, app
from app.db.database import get_db
from app.models.currency import Base


@pytest.fixture(scope="function")
def test_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override
    db = TestSession()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client(test_db):
    _rate_limit_hits.clear()
    with TestClient(app) as test_client:
        yield test_client
    _rate_limit_hits.clear()


@pytest.fixture
def sample_rate_data():
    return {
        "usd": {
            "cash": {"buy": 3420.5, "sell": 3450.0},
            "noncash": {"buy": 3415.0, "sell": 3455.0},
        },
        "eur": {
            "cash": {"buy": 3720.0, "sell": 3780.0},
            "noncash": {"buy": 3715.0, "sell": 3785.0},
        },
    }


@pytest.fixture
def sample_khanbank_response():
    return [
        {
            "currency": "USD",
            "cashBuyRate": 3420.5,
            "cashSellRate": 3450.0,
            "buyRate": 3415.0,
            "sellRate": 3455.0,
        },
        {
            "currency": "EUR",
            "cashBuyRate": 3720.0,
            "cashSellRate": 3780.0,
            "buyRate": 3715.0,
            "sellRate": 3785.0,
        },
    ]


@pytest.fixture
def sample_golomt_response():
    return {
        "result": {
            "USD": {
                "cash_buy": {"cvalue": 3420.5},
                "cash_sell": {"cvalue": 3450.0},
                "non_cash_buy": {"cvalue": 3415.0},
                "non_cash_sell": {"cvalue": 3455.0},
            },
        }
    }
