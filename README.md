# Монголын Банкуудын Валютын Ханш API

Монголын 15 банк болон санхүүгийн байгууллагын валютын ханшийг цуглуулж, өгөгдлийн санд хадгалаад FastAPI REST API-аар түгээдэг open source төсөл.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

## Юу Хийдэг Вэ?

1. Банк, санхүүгийн байгууллагуудын ханшийг HTTP болон Playwright crawler-уудаар зэрэгцээ татна.
2. Валютын ханшийг нэг JSON бүтэцтэй болгож өгөгдлийн санд хадгална.
3. REST API-аар хамгийн сүүлийн, банкны, өдрийн болон түүхэн ханшийг буцаана.
4. `scripts/cron.py` өдөр бүр автоматаар crawler ажиллуулна.
5. `scripts/backfill.py` өмнөх огнооны ханшийг нөхөж татна.
6. Docker Compose нь API, scheduler worker, PostgreSQL-г хамтад нь ажиллуулна.

## Хурдан Эхлэх: Local

```bash
git clone https://github.com/btseee/mongolian-bank-exchange-rate.git
cd mongolian-bank-exchange-rate

python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m playwright install chromium

python -m uvicorn app.api.api:app --reload
```

Linux/macOS дээр virtual environment идэвхжүүлэх команд:

```bash
source .venv/bin/activate
```

API: [http://localhost:8000](http://localhost:8000)  
Swagger docs: [http://localhost:8000/docs](http://localhost:8000/docs)

Анхны өгөгдөл татах:

```bash
python main.py
```

## Хурдан Эхлэх: Docker

`.env` файл заавал хэрэггүй. Default тохиргоогоор API, cron worker, PostgreSQL хамт асна.

```bash
docker compose up --build
```

API: [http://localhost:8000](http://localhost:8000)  
Swagger docs: [http://localhost:8000/docs](http://localhost:8000/docs)

Өөр тохиргоо хэрэгтэй бол `.env.example`-ийг `.env` болгож хуулж утгуудыг өөрчилнө. Docker Compose `.env` файлыг автоматаар уншиж default утгуудыг дарна.

## Төслийн Бүтэц

| Зам | Үүрэг |
| --- | --- |
| `app/api/api.py` | FastAPI app, Swagger metadata, API rate limit, endpoint-ууд |
| `app/crawlers/` | Банк бүрийн crawler. HTTP болон Playwright crawler гэж хуваагдана |
| `app/services/scraper.py` | Crawler-уудыг зэрэгцээ ажиллуулж үр дүнг хадгална |
| `app/db/` | SQLAlchemy session, repository query/upsert логик |
| `app/models/` | Database model болон API response model |
| `scripts/cron.py` | Өдөр тутмын scheduler worker |
| `scripts/backfill.py` | Огнооны интервалаар ханш нөхөж татах script |
| `tests/` | API, crawler, service test-үүд |

## API Endpoint-ууд

Swagger UI дээр банкны нэрийг selectable enum байдлаар сонгож болно.

| Endpoint | Тайлбар |
| --- | --- |
| `GET /` | API мэдээлэл, дэмждэг банкууд |
| `GET /health` | Health check |
| `GET /rates?skip=0&limit=100` | Бүх ханш, pagination-тэй |
| `GET /rates/latest` | Банк бүрийн хамгийн сүүлийн ханш |
| `GET /rates/bank/{bank_name}` | Сонгосон банкны ханш |
| `GET /rates/date/{date}` | Сонгосон өдрийн бүх ханш |
| `GET /rates/bank/{bank_name}/date/{date}` | Банк ба өдрөөр нэг бичлэг авах |

Жишээ:

```bash
curl "http://localhost:8000/rates/bank/KhanBank?limit=10"
curl "http://localhost:8000/rates/date/2026-05-06"
```

## Дэмжигдсэн Банкууд

| Банк / Байгууллага | Код | Төрөл |
| --- | --- | --- |
| Хаан Банк | `KhanBank` | HTTP |
| Голомт Банк | `GolomtBank` | HTTP |
| Хас Банк | `XacBank` | HTTP |
| Ариг Банк | `ArigBank` | HTTP |
| Төрийн Банк | `StateBank` | HTTP |
| Монгол Банк | `MongolBank` | HTTP |
| Капитрон Банк | `CapitronBank` | HTTP |
| Найман Шарга | `NaimanSharga` | HTTP |
| SendMN | `SendMN` | HTTP |
| ХХБ | `TDBM` | Playwright |
| Богд Банк | `BogdBank` | Playwright |
| Чингис Хаан Банк | `CKBank` | Playwright |
| ҮХОБ | `NIBank` | Playwright |
| Транс Банк | `TransBank` | Playwright |
| М Банк | `MBank` | Playwright |

## Cron Ба Backfill

Өдөр бүр ажиллуулах worker:

```bash
python -m scripts.cron
```

Default `CRON_SCHEDULE=0 9 * * *`, өөрөөр хэлбэл server/container-ийн local time-аар 09:00 цагт ажиллана. Одоогоор өдөр тутмын `M H * * *` хэлбэрийн cron expression дэмжинэ.

Өгөгдөл нөхөж татах:

```bash
python -m scripts.backfill
python -m scripts.backfill 2026-01-01
python -m scripts.backfill 2026-01-01 2026-01-31
```

## Тохиргоо

| Хувьсагч | Default | Тайлбар |
| --- | --- | --- |
| `DATABASE_URL` | `sqlite:///./exchange_rates.db` | Local database URL. Docker Compose default нь PostgreSQL ашиглана |
| `CRON_SCHEDULE` | `0 9 * * *` | Daily scheduler цаг |
| `SSL_VERIFY` | `false` | Crawler HTTP SSL verification |
| `REQUEST_TIMEOUT` | `30` | HTTP request timeout секундээр |
| `PLAYWRIGHT_TIMEOUT` | `60000` | Playwright timeout миллисекундээр |
| `ENABLE_PARALLEL` | `true` | Crawler-уудыг зэрэгцээ ажиллуулах эсэх |
| `MAX_WORKERS` | `8` | HTTP crawler worker тоо |
| `PLAYWRIGHT_MAX_WORKERS` | `3` | Playwright crawler worker тоо |
| `API_MAX_LIMIT` | `100` | Pagination `limit`-ийн дээд хэмжээ |
| `CORS_ORIGINS` | `*` | Зөвшөөрөх origin-ууд, comma-separated |
| `CORS_ALLOW_CREDENTIALS` | `false` | CORS credential зөвшөөрөх эсэх |
| `TRUST_PROXY_HEADERS` | `false` | Heroku/reverse proxy ард ажиллах үед `X-Forwarded-For`-г client IP гэж үзэх эсэх |
| `RATE_LIMIT_ENABLED` | `true` | API rate limit асаах эсэх |
| `RATE_LIMIT_REQUESTS` | `60` | Нэг client-ийн window доторх request тоо |
| `RATE_LIMIT_WINDOW_SECONDS` | `60` | Rate limit window секундээр |
| `RATE_LIMIT_MAX_CLIENTS` | `10000` | Memory-д хадгалах rate-limit client bucket-ийн дээд тоо |

Rate limit нь application process дотор memory ашигладаг тул олон dyno, replica, эсвэл олон worker-тэй production орчинд global limit болохгүй. Strict production хамгаалалт хэрэгтэй бол Heroku router/CDN/reverse proxy/Redis-backed limiter зэрэг shared түвшний хамгаалалт нэмнэ. `TRUST_PROXY_HEADERS=true`-г зөвхөн client-ийн `X-Forwarded-For` header-ийг proxy өөрөө strip/overwrite хийдэг найдвартай proxy-ийн ард ажиллах үед асаана.

## Хөгжүүлэгчийн Шалгалт

```bash
isort app tests scripts main.py --check-only
black app tests scripts main.py --check
ruff check app tests scripts main.py
pytest
```

Автоматаар засах:

```bash
isort app tests scripts main.py
black app tests scripts main.py
```

## Release Гаргах

1. `CHANGELOG.md`-д хэрэглэгчид ойлгомжтой өөрчлөлтийн тайлбар нэмнэ.
2. Version-ийг `app/__version__.py` дээр шинэчилнэ.
3. `vX.Y.Z` tag push хийхэд CI Docker image build/push хийж GitHub Release үүсгэнэ.
4. Release title нь tag-аар нэрлэгдэж, auto-generated notes нь label-уудаар ангилагдана.

## Хувь Нэмэр Оруулах

[CONTRIBUTING.md](CONTRIBUTING.md) файлыг уншина уу. Issue template, pull request template, security policy, code of conduct бүгд repository-д багтсан.

## Лиценз

MIT License - [LICENSE.md](LICENSE.md)

## Холбогдох

- GitHub: [@btseee](https://github.com/btseee)
- Email: [bbattseren88@gmail.com](mailto:bbattseren88@gmail.com)
- Дэмжих: [Buy Me a Coffee](https://buymeacoffee.com/btseee)
