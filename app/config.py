import os

from dotenv import load_dotenv

load_dotenv()


def _env(key: str, default: str = "") -> str:
    return os.getenv(key, default)


def _env_bool(key: str, default: bool = False) -> bool:
    return _env(key, str(default)).lower() in ("true", "1", "yes")


def _env_int(key: str, default: int = 0) -> int:
    value = _env(key, str(default))
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{key} must be an integer") from exc


def _env_positive_int(key: str, default: int) -> int:
    value = _env_int(key, default)
    if value < 1:
        raise ValueError(f"{key} must be greater than or equal to 1")
    return value


def _env_non_negative_int(key: str, default: int) -> int:
    value = _env_int(key, default)
    if value < 0:
        raise ValueError(f"{key} must be greater than or equal to 0")
    return value


def _env_list(key: str, default: str = "") -> list[str]:
    return [
        item.strip() for item in _env(key, default).split(",") if item.strip()
    ]


def _validate_cors_config(origins: list[str], allow_credentials: bool) -> None:
    if allow_credentials and "*" in origins:
        raise ValueError(
            "CORS_ALLOW_CREDENTIALS cannot be true when "
            "CORS_ORIGINS includes *"
        )


def _database_url() -> str:
    default = "sqlite:///./exchange_rates.db"
    url = _env("DATABASE_URL", default) or default
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


class Config:
    # Database
    DATABASE_URL = _database_url()

    # Scheduler
    CRON_SCHEDULE = _env("CRON_SCHEDULE", "0 9 * * *")

    # HTTP settings
    SSL_VERIFY = _env_bool("SSL_VERIFY", True)
    REQUEST_TIMEOUT = _env_positive_int("REQUEST_TIMEOUT", 30)
    PLAYWRIGHT_TIMEOUT = _env_positive_int("PLAYWRIGHT_TIMEOUT", 60000)

    # Logging
    LOG_LEVEL = _env("LOG_LEVEL", "INFO")

    # Self-ping keepalive (empty means disabled). Set to the app's own public
    # URL (e.g. https://your-app.onrender.com) to stop Render's free tier
    # from sleeping the instance after ~15 minutes of no inbound traffic.
    SELF_PING_URL = _env("SELF_PING_URL")
    SELF_PING_INTERVAL_SECONDS = _env_positive_int(
        "SELF_PING_INTERVAL_SECONDS", 30
    )

    # Public API safeguards
    API_MAX_LIMIT = _env_positive_int("API_MAX_LIMIT", 100)
    CORS_ORIGINS = _env_list("CORS_ORIGINS", "*")
    CORS_ALLOW_CREDENTIALS = _env_bool("CORS_ALLOW_CREDENTIALS", False)
    _validate_cors_config(CORS_ORIGINS, CORS_ALLOW_CREDENTIALS)
    TRUST_PROXY_HEADERS = _env_bool("TRUST_PROXY_HEADERS", False)
    RATE_LIMIT_ENABLED = _env_bool("RATE_LIMIT_ENABLED", True)
    RATE_LIMIT_REQUESTS = _env_positive_int("RATE_LIMIT_REQUESTS", 60)
    RATE_LIMIT_WINDOW_SECONDS = _env_positive_int(
        "RATE_LIMIT_WINDOW_SECONDS", 60
    )
    RATE_LIMIT_MAX_CLIENTS = _env_positive_int("RATE_LIMIT_MAX_CLIENTS", 10000)

    # Admin endpoints (POST /api/admin/*) - empty means the feature is
    # disabled (503), never "open to anyone"
    ADMIN_API_KEY = _env("ADMIN_API_KEY")

    # Parallel execution
    ENABLE_PARALLEL = _env_bool("ENABLE_PARALLEL", True)
    MAX_WORKERS = _env_positive_int("MAX_WORKERS", 8)
    PLAYWRIGHT_MAX_WORKERS = _env_positive_int("PLAYWRIGHT_MAX_WORKERS", 3)
    BACKFILL_DELAY_SECONDS = _env_non_negative_int("BACKFILL_DELAY_SECONDS", 2)

    # Bank API endpoints
    KHANBANK_URI = _env(
        "KHANBANK_URI", "https://www.khanbank.com/api/back/rates"
    )
    GOLOMT_URI = _env("GOLOMT_URI", "https://www.golomtbank.com/api/exchange")
    XACBANK_URI = _env("XACBANK_URI", "https://xacbank.mn/api/currencies")
    ARIGBANK_API_URL = _env(
        "ARIGBANK_API_URL", "https://www.arigbank.mn/exchange/getRate"
    )
    ARIGBANK_SIGNIN_URL = _env(
        "ARIGBANK_SIGNIN_URL", "https://www.arigbank.mn/exchange/signIn"
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
