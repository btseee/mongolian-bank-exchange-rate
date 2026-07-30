"""FastAPI application: middleware, lifespan, and router assembly.

Endpoint handlers themselves live in app.api.routers.* - this module only
wires the app together. See app.api.dependencies for the shared BankName
enum, date parsing, and admin-key auth used across routers.
"""

import asyncio
from collections import OrderedDict, deque
from contextlib import asynccontextmanager
from time import monotonic

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.__version__ import __author__, __license__, __url__, __version__
from app.api.routers import admin, rates, system
from app.config import config
from app.db.database import init_db
from app.utils.logger import logger

RATE_LIMIT_EXCLUDED_PATHS = {"/", "/redoc", "/openapi.json", "/api/health"}
_rate_limit_hits = OrderedDict()


async def _self_ping_loop() -> None:
    """Keep a Render free-tier instance from idling to sleep by hitting its
    own health check on an interval. No-op unless SELF_PING_URL is set."""
    async with httpx.AsyncClient(timeout=10) as client:
        while True:
            await asyncio.sleep(config.SELF_PING_INTERVAL_SECONDS)
            try:
                await client.get(config.SELF_PING_URL)
            except httpx.HTTPError as exc:
                logger.warning(f"Self-ping failed: {exc}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    task = None
    if config.SELF_PING_URL:
        task = asyncio.create_task(_self_ping_loop())
    yield
    if task is not None:
        task.cancel()


app = FastAPI(
    title="Монголын Банкуудын Валютын Ханш API",
    version=__version__,
    docs_url="/",
    description=(
        "Монголын банк, санхүүгийн байгууллагуудын валютын ханшийг "
        "нэг хэлбэртэй JSON бүтэцтэйгээр буцаадаг REST API. "
        "Swagger дээр банкны нэр, огноо, pagination параметрүүдийг сонгон "
        "турших боломжтой."
    ),
    contact={"name": __author__, "url": __url__},
    license_info={
        "name": __license__,
        "url": "https://opensource.org/licenses/MIT",
    },
    lifespan=lifespan,
    openapi_tags=[
        {"name": "Ерөнхий", "description": "API-н ерөнхий мэдээлэл"},
        {"name": "Ханш", "description": "Валютын ханшийн endpoints"},
        {
            "name": "Админ",
            "description": (
                "Crawl/backfill job идэвхжүүлэх endpoints "
                "(X-Admin-Key шаардана)"
            ),
        },
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=config.CORS_ALLOW_CREDENTIALS,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def _client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if config.TRUST_PROXY_HEADERS and forwarded_for:
        return forwarded_for.split(",", maxsplit=1)[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def _rate_limit_bucket(client_key: str) -> deque:
    client_hits = _rate_limit_hits.get(client_key)
    if client_hits is not None:
        _rate_limit_hits.move_to_end(client_key)
        return client_hits

    while len(_rate_limit_hits) >= config.RATE_LIMIT_MAX_CLIENTS:
        _rate_limit_hits.popitem(last=False)

    client_hits = deque()
    _rate_limit_hits[client_key] = client_hits
    return client_hits


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    if (
        not config.RATE_LIMIT_ENABLED
        or request.url.path in RATE_LIMIT_EXCLUDED_PATHS
    ):
        return await call_next(request)

    now = monotonic()
    window_start = now - config.RATE_LIMIT_WINDOW_SECONDS
    client_hits = _rate_limit_bucket(_client_ip(request))

    while client_hits and client_hits[0] <= window_start:
        client_hits.popleft()

    if len(client_hits) >= config.RATE_LIMIT_REQUESTS:
        retry_after = max(
            1,
            int(config.RATE_LIMIT_WINDOW_SECONDS - (now - client_hits[0])),
        )
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"},
            headers={"Retry-After": str(retry_after)},
        )

    client_hits.append(now)
    response = await call_next(request)
    remaining = max(config.RATE_LIMIT_REQUESTS - len(client_hits), 0)
    response.headers["X-RateLimit-Limit"] = str(config.RATE_LIMIT_REQUESTS)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    return response


app.include_router(system.router)
app.include_router(rates.router)
app.include_router(admin.router)
