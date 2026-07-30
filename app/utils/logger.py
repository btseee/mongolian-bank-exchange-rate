import logging
import sys

from app.config import config

_level = getattr(logging, config.LOG_LEVEL.upper(), logging.INFO)

logging.basicConfig(
    level=_level,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger("app")
