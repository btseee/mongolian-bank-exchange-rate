"""Bank crawlers for Mongolian exchange rates."""

from app.crawlers.arigbank import ArigBank
from app.crawlers.bogdbank import BogdBank
from app.crawlers.capitronbank import CapitronBank
from app.crawlers.ckbank import CKBank
from app.crawlers.golomt import GolomtBank
from app.crawlers.khanbank import KhanBank
from app.crawlers.mbank import MBank
from app.crawlers.mongolbank import MongolBank
from app.crawlers.naimansharga import NaimanSharga
from app.crawlers.nibank import NIBank
from app.crawlers.sendmn import SendMN
from app.crawlers.statebank import StateBank
from app.crawlers.tdbm import TDBM
from app.crawlers.transbank import TransBank
from app.crawlers.xacbank import XacBank

HTTP_CRAWLERS = [
    KhanBank,
    GolomtBank,
    XacBank,
    ArigBank,
    StateBank,
    MongolBank,
    CapitronBank,
    NaimanSharga,
    SendMN,
]
PLAYWRIGHT_CRAWLERS = [TDBM, BogdBank, CKBank, NIBank, TransBank, MBank]
ALL_CRAWLERS = HTTP_CRAWLERS + PLAYWRIGHT_CRAWLERS

CRAWLER_MAP = {c.BANK_NAME.lower(): c for c in ALL_CRAWLERS}

__all__ = [
    "KhanBank",
    "GolomtBank",
    "XacBank",
    "ArigBank",
    "StateBank",
    "MongolBank",
    "CapitronBank",
    "NaimanSharga",
    "SendMN",
    "TDBM",
    "BogdBank",
    "CKBank",
    "NIBank",
    "TransBank",
    "MBank",
    "HTTP_CRAWLERS",
    "PLAYWRIGHT_CRAWLERS",
    "ALL_CRAWLERS",
    "CRAWLER_MAP",
]
