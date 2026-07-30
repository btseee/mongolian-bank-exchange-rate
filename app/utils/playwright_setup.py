import subprocess
import sys

from app.utils.logger import logger


def ensure_playwright_browsers():
    """Install Playwright browsers if not already installed."""
    try:
        subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as e:
        logger.warning(
            "playwright install chromium failed (may already be "
            f"installed or environment is restricted): {e}"
        )
