import pytest

from app.config import _validate_cors_config


def test_validate_cors_config_rejects_credentials_with_wildcard():
    with pytest.raises(ValueError, match="CORS_ALLOW_CREDENTIALS"):
        _validate_cors_config(["*"], True)


def test_validate_cors_config_allows_explicit_origins_with_credentials():
    _validate_cors_config(["https://example.com"], True)
