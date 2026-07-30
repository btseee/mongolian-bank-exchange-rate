# Монголын Банкуудын Валютын Ханш API

Монголын 15 банк, санхүүгийн байгууллагын валютын ханшийг цуглуулж, хадгалаад FastAPI REST API-аар түгээдэг open source төсөл.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.14+](https://img.shields.io/badge/python-3.14+-blue.svg)](https://www.python.org/downloads/)

## Хурдан Эхлэх

**Local:**

```bash
git clone https://github.com/btseee/mongolian-bank-exchange-rate.git
cd mongolian-bank-exchange-rate
python -m venv .venv && .venv\Scripts\activate   # Linux/macOS: source .venv/bin/activate
python -m pip install -r requirements.txt
python -m playwright install chromium

python main.py                                   # анхны өгөгдөл татах
python -m uvicorn app.api.api:app --reload
```

**Docker** (`.env` заавал биш - default тохиргоогоор API, cron worker, PostgreSQL хамт асна):

```bash
docker compose up --build
```

Хоёуланд нь: Swagger docs болон API [http://localhost:8000](http://localhost:8000) дээр (docs нь root дээр).

## Төслийн Бүтэц

| Зам | Үүрэг |
| --- | --- |
| `app/api/` | FastAPI app, middleware, router-ууд (`system`, `rates`, `admin`), auth/date dependencies |
| `app/crawlers/` | Банк бүрийн HTTP/Playwright crawler |
| `app/services/` | Crawler-уудыг зэрэгцээ ажиллуулах, admin job lock/төлөв |
| `app/db/`, `app/models/` | SQLAlchemy session, repository upsert, DB/API model-ууд |
| `scripts/cron.py`, `scripts/backfill.py` | Always-on scheduler worker, огноо нөхөж татах script |
| `render.yaml` | Render.com Docker web service Blueprint |

## API Endpoint-ууд

Swagger UI **`/`** дээр. Бодит endpoint бүгд **`/api/`** prefix-тэй.

| Endpoint | Тайлбар |
| --- | --- |
| `GET /api/info` | API мэдээлэл, дэмждэг банкууд |
| `GET /api/health` | Health check |
| `GET /api/rates?skip=0&limit=100` | Бүх ханш, pagination-тэй |
| `GET /api/rates/latest` | Банк бүрийн хамгийн сүүлийн ханш |
| `GET /api/rates/bank/{bank_name}` | Сонгосон банкны ханш |
| `GET /api/rates/date/{date}` | Сонгосон өдрийн бүх ханш |
| `GET /api/rates/bank/{bank_name}/date/{date}` | Банк ба өдрөөр нэг бичлэг |
| `POST /api/admin/crawl` | Бүх банкнаас нэн даруй татаж эхлүүлэх (background, `X-Admin-Key`) |
| `POST /api/admin/crawl/{bank_name}` | Ганц банкыг синхроноор татах (`X-Admin-Key`) |
| `POST /api/admin/backfill` | Огнооны интервалаар татаж эхлүүлэх (background, `X-Admin-Key`) |
| `GET /api/admin/status` | Job-ын явц/сүүлийн үр дүн (`X-Admin-Key`) |

```bash
curl "http://localhost:8000/api/rates/bank/KhanBank?limit=10"

curl -X POST "http://localhost:8000/api/admin/crawl" -H "X-Admin-Key: $ADMIN_API_KEY"
curl "http://localhost:8000/api/admin/status" -H "X-Admin-Key: $ADMIN_API_KEY"
curl -X POST "http://localhost:8000/api/admin/backfill" \
  -H "X-Admin-Key: $ADMIN_API_KEY" -H "Content-Type: application/json" \
  -d '{"start": "2026-01-01", "end": "2026-01-31"}'
```

`ADMIN_API_KEY` тохируулаагүй бол admin endpoint бүгд `503`. Буруу/байхгүй header → `401`. Job аль хэдийн ажиллаж байвал → `409` (нэг дор нэг л job).

## Дэмжигдсэн Банкууд

| Банк | Код | Төрөл | Банк | Код | Төрөл |
| --- | --- | --- | --- | --- | --- |
| Хаан Банк | `KhanBank` | HTTP | Найман Шарга | `NaimanSharga` | HTTP |
| Голомт Банк | `GolomtBank` | HTTP | SendMN | `SendMN` | HTTP |
| Хас Банк | `XacBank` | HTTP | М Банк | `MBank` | HTTP |
| Ариг Банк | `ArigBank` | HTTP | ХХБ | `TDBM` | Playwright |
| Төрийн Банк | `StateBank` | HTTP | Богд Банк | `BogdBank` | Playwright |
| Монгол Банк | `MongolBank` | HTTP | Чингис Хаан Банк | `CKBank` | Playwright |
| Капитрон Банк | `CapitronBank` | HTTP | ҮХОБ | `NIBank` | Playwright |
| | | | Транс Банк | `TransBank` | Playwright |

## Cron Ба Backfill

Always-on орчинд (локал, VPS, Docker Compose):

```bash
python -m scripts.cron                    # CRON_SCHEDULE (default 09:00) цагт өдөр бүр
python -m scripts.backfill 2026-01-01 2026-01-31
```

Render зэрэг always-on worker дэмждэггүй free-tier орчинд эдгээрийг дээрх admin endpoint-ээр HTTP-аар дуудна. Аль ч аргаар ч өдөр бүрийн хооронд `BACKFILL_DELAY_SECONDS` (default 2 сек) азнаж банкны сайтуудыг rapid биш дуудна.

## Render Дээр Deploy Хийх

Free Docker web service байдлаар `render.yaml`-аар deploy хийхэд бэлэн.

1. GitHub repo-г Render dashboard дээр холбож "New Blueprint" → `render.yaml`.
2. Dashboard дээр гараар тохируулах: `ADMIN_API_KEY` (`openssl rand -hex 32`), `ARIGBANK_BEARER_TOKEN` (заавал биш).
3. **Чухал**: Free web service-д persistent disk байхгүй тул default SQLite нь restart болгонд хоослогдоно. Байнгын хадгалалт хэрэгтэй бол Neon/Supabase Postgres үүсгэж, `DATABASE_URL`-г Render dashboard дээр connection string болгож тохируулна (`render.yaml`-д зориудаар тодорхойлогдоогүй).
4. Sleep-ээс сэргийлэхийн тулд `SELF_PING_URL`-г өөрийн Render URL + `/api/health` болгож тохируулж болно (жишээ нь `https://mongolian-bank-exchange-rate-hm3t.onrender.com/api/health`) - энэ нь Render-ийн 750 цагийн сарын instance-hour квотыг бүрэн ашиглана гэдгийг анхаараарай.
5. GitHub Actions daily crawl-ыг ажиллуулахын тулд repo Settings → Secrets/Variables → Actions дээр secret `ADMIN_API_KEY` болон variable `RENDER_APP_URL` тохируулна (`.github/workflows/scheduled-crawl.yml` үзнэ үү).

## Тохиргоо

Бүх хувьсагч заавал биш - `.env.example` дэх default-ууд ажиллахад хангалттай. Бүрэн жагсаалт: `app/config.py`.

| Хувьсагч | Default | Тайлбар |
| --- | --- | --- |
| `DATABASE_URL` | SQLite | Render дээр гараар Postgres руу солино ("Render Дээр Deploy Хийх" үзнэ үү) |
| `ADMIN_API_KEY` | (хоосон) | `/api/admin/*`-г хамгаалах secret. Хоосон бол 503 |
| `SELF_PING_URL` | (хоосон) | Тохируулбал `SELF_PING_INTERVAL_SECONDS`-ийн зайтай өөрийгөө ping хийж Render-ийг сэрүүн байлгана |
| `BACKFILL_DELAY_SECONDS` | `2` | Backfill-ийн өдөр бүрийн хоорондох азналт |
| `LOG_LEVEL` | `INFO` | Python logging түвшин |
| `SSL_VERIFY` | `true` | Crawler HTTP SSL verification |
| `MAX_WORKERS` / `PLAYWRIGHT_MAX_WORKERS` | `8` / `3` | Crawler worker тоо (Render дээр `render.yaml`-аар 4/1) |
| `CORS_ORIGINS`, `RATE_LIMIT_*` | - | Public API хамгаалалт, `app/config.py`-д бүрэн жагсаалт |

Rate limit болон admin job lock нь process-dotor memory ашигладаг тул зөвхөн нэг Uvicorn process-той deploy-д (`--workers` флаггүй) зөв ажиллана - олон replica-той production бол Redis-backed shared limiter нэмнэ.

## Хөгжүүлэгчийн Шалгалт

```bash
isort app tests scripts main.py --check-only && black app tests scripts main.py --check
ruff check app tests scripts main.py
pytest
```

## Release Гаргах

1. `CHANGELOG.md`-д өөрчлөлт нэмнэ, `app/__version__.py`-г шинэчилнэ.
2. `main`-д push болгонд CI `ghcr.io`-руу одоогийн хувилбарын (`app/__version__.py`) `vX.Y.Z` + `latest` image-г дахин push хийж дарж бичнэ - шинэ хувилбар гарах хүртэл нэмэлт image үүсэхгүй. `vX.Y.Z` tag push хийхэд GitHub Release үүсгэнэ.

## Бусад

[CONTRIBUTING.md](CONTRIBUTING.md) · [LICENSE.md](LICENSE.md) (MIT) · [@btseee](https://github.com/btseee) · [bbattseren88@gmail.com](mailto:bbattseren88@gmail.com) · [Buy Me a Coffee](https://buymeacoffee.com/btseee)
