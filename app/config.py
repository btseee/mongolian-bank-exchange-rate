import os

from dotenv import load_dotenv

load_dotenv()


def _env(key: str, default: str = "") -> str:
    return os.getenv(key, default)


def _env_bool(key: str, default: bool = False) -> bool:
    return _env(key, str(default)).lower() in ("true", "1", "yes")


def _env_int(key: str, default: int = 0) -> int:
    return int(_env(key, str(default)))


def _database_url() -> str:
    url = _env("DATABASE_URL", "sqlite:///./exchange_rates.db")
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


class Config:
    # Database
    DATABASE_URL = _database_url()

    # Scheduler
    CRON_SCHEDULE = _env("CRON_SCHEDULE", "0 9 * * *")

    # HTTP settings
    SSL_VERIFY = _env_bool("SSL_VERIFY", False)
    REQUEST_TIMEOUT = _env_int("REQUEST_TIMEOUT", 30)
    PLAYWRIGHT_TIMEOUT = _env_int("PLAYWRIGHT_TIMEOUT", 60000)

    # Parallel execution
    ENABLE_PARALLEL = _env_bool("ENABLE_PARALLEL", True)
    MAX_WORKERS = _env_int("MAX_WORKERS", 8)
    PLAYWRIGHT_MAX_WORKERS = _env_int("PLAYWRIGHT_MAX_WORKERS", 3)

    # Bank API endpoints
    KHANBANK_URI = _env(
        "KHANBANK_URI", "https://www.khanbank.com/api/back/rates"
    )
    GOLOMT_URI = _env("GOLOMT_URI", "https://www.golomtbank.com/api/exchange")
    XACBANK_URI = _env("XACBANK_URI", "https://xacbank.mn/api/currencies")
    ARIGBANK_API_URL = _env(
        "ARIGBANK_API_URL", "https://www.arigbank.mn/exchange/getRate"
    )
    ARIGBANK_BEARER_TOKEN = _env("ARIGBANK_BEARER_TOKEN")
    STATEBANK_URI = _env(
        "STATEBANK_URI", "https://www.statebank.mn/back/api/fetchrate"
    )
    MONGOLBANK_URI = _env(
        "MONGOLBANK_URI",
        "https://www.mongolbank.mn/en/currency-rate-movement/data",
    )
    CAPITRONBANK_API_URL = _env(
        "CAPITRONBANK_API_URL",
        "https://www.capitronbank.mn/admin/en/wp-json/bank/rates/capitronbank",
    )

    # Playwright-based bank URLs
    TDBM_URI = _env("TDBM_URI", "https://www.tdbm.mn/en/exchange-rates")
    BOGDBANK_URI = _env("BOGDBANK_URI", "https://www.bogdbank.com/exchange")
    CKBANK_URI = _env("CKBANK_URI", "https://www.ckbank.mn/currency-rates")
    NIBANK_URI = _env("NIBANK_URI", "https://www.nibank.mn/en/rate")
    TRANSBANK_URI = _env("TRANSBANK_URI", "https://transbank.mn/en/exchange")
    MBANK_URI = _env("MBANK_URI", "https://m-bank.mn/")

    # Firebase Firestore-based APIs
    SENDMN_FIRESTORE_URL = _env(
        "SENDMN_FIRESTORE_URL",
        "https://firestore.googleapis.com/v1/projects/sendmn-remit/databases/(default)/documents/rate/exrate?key=AIzaSyCrYSDevTZ_WigjBGeOuoGj-ntLO5v9taY",
    )
    NSHARGA_FIRESTORE_BASE_URL = _env(
        "NSHARGA_FIRESTORE_BASE_URL",
        "https://firestore.googleapis.com/v1/projects/nsharga-2ec6a/databases/(default)/documents/currency_rates?key=AIzaSyBA-tL_dqi1MsO43OkwllUpV7k6rf0Iys4",
    )


config = Config()
