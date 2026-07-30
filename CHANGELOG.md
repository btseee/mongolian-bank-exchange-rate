<!-- markdownlint-disable MD024 -->

# Өөрчлөлтийн Түүх

## [v1.1.0] - 2026-07-30

Heroku-г бүрмөсөн хасаж, Render.com-ийн free Docker web service рүү шилжсэн том refactor. **API restructure нь breaking change** - өмнөх unprefixed зам (`/rates`, `/health`) ашиглаж байсан клиентүүд `/api/` prefix рүү шилжих шаардлагатай.

### Нэмсэн

- Swagger docs `/` root дээр, бүх функциональ endpoint `/api/` prefix-тэй болсон (өмнөх root info endpoint нь `GET /api/info`).
- Admin endpoint-ууд: `POST /api/admin/crawl`, `crawl/{bank_name}`, `backfill`, `GET /api/admin/status` - `X-Admin-Key` header-ээр хамгаалагдсан.
- `render.yaml` Blueprint болон `.github/workflows/scheduled-crawl.yml` - Render free tier дээр always-on worker байхгүй тул admin endpoint-ийг өдөр бүр дуудаж амжилтыг баталгаажуулна.
- `SELF_PING_URL` тохиргоо - тохируулбал өөрийгөө тогтмол зайтай ping хийж Render instance-ийг idle-аар унтахаас сэргийлнэ.
- `CurrencyRate` дээр `(bank_name, date)` unique constraint, атом upsert (`INSERT ... ON CONFLICT`) - давхардсан мөр үүсэх race condition арилсан.
- Crawler-уудад retry (`requests` `Retry`/`HTTPAdapter`) болон нийтлэг browser-like `User-Agent`; `0` валют татсан тохиолдолд `WARNING` log.
- Backfill-ийн өдөр бүрийн хооронд `BACKFILL_DELAY_SECONDS` азнах логик.

### Өөрчилсөн

- Python 3.14 дээр стандартчилагдсан (өмнө нь 3.11/3.13/3.14 холилдсон байсан); `requirements.txt` бүх хамаарал `==` тэмдэгтээр тогтмол хувилбарт лацдагдсан.
- `psycopg2-binary` → `psycopg[binary]` (psycopg3); `SSL_VERIFY` default `false` → `true`.
- `MBank` crawler зөв `HTTP_CRAWLERS` бүлэгт орсон (өмнө нь илүү удаан Playwright бүлэгт байсан).
- `.env.example` хялбарчлагдсан - бүх банкны URL нь `app/config.py`-д код defaults болсон тул `.env`-д давхардуулах шаардлагагүй болсон.
- `ScraperService.run_all()`/`backfill()` одоо гүйцэтгэлийн тойм (`succeeded`/`failed`/`failed_banks`) буцаадаг.
- README, CHANGELOG хялбарчлагдсан.

### Зассан

Бүх 15 банкыг `2026-07-30`-ны өдөр live crawl хийж баталгаажуулахад 3 банк бодитоор эвдэрсэн болохыг илрүүлж засав (15/15 амжилттай):

- **MongolBank** - API өнөөдрийн ханшийг хараахан нийтлээгүй үед хамгийн сүүлийн боломжит мөрд буцаж очих fallback болсон.
- **BogdBank** - валютын код баганын текст `<img>` флаг болсон тул зурагны файлын нэрнээс кодыг гаргаж авдаг болсон.
- **TransBank** - `wait_until="networkidle"` бараг үргэлж timeout өгдөг байсныг `domcontentloaded` болгосон.

### Хассан

- `bin/post_compile` (Heroku buildpack hook), ашиглагдаагүй Docker `./logs` volume, `[tool.flake8]` тохиргоо, ашиглагдаагүй `Pygments` хамаарал.

## [v1.0.9] - 2026-05-06

`v1.0.8`-ийн банкны live API өөрчлөлт, Heroku worker import асуудлаас болж тогтворгүй байсныг засаж тогтвортой дахин гаргасан хувилбар.

- Public API хамгаалалт нэмэгдсэн: configurable CORS, pagination дээд хэмжээ, rate limit, `Retry-After`/`X-RateLimit-*` header.
- StateBank, CapitronBank, MongolBank, TDBM, ArigBank, NaimanSharga-ийн upstream response өөрчлөлтөөс болсон parsing алдаанууд засагдсан.
- `.env.example` анх удаа нэмэгдсэн; README/CONTRIBUTING шинэчлэгдсэн.
- `2026-05-06`: 15/15 банк амжилттай, бүх шалгалт ногоон.

## [v1.0.8] - 2026-05-05

> Тогтворгүй болсон тул `v1.0.9`-ээр солигдсон (ArigBank token expiry, NaimanSharga Firestore URL, MongolBank JSON endpoint, StateBank/CapitronBank response drift, TDBM timeout, Heroku worker import).

- **NaimanSharga**, **SendMN** crawler-ууд нэмэгдсэн (Firebase Firestore-based).
- MongolBank XXE эмзэг байдал, BogdBank/TDBM/TransBank/MBank/CapitronBank-ийн бодит алдаанууд засагдсан.
- Нийт дэмжигдэх банкны тоо: 13 → 15.

## [v1.0.6] - 2026-02-06

Код бүтцийг бүхэлд нь сайжруулсан refactor: crawler-уудыг нэгтгэж давхардал арилгасан, base crawler class, хялбаршуулсан scraper service, цэгцтэй API endpoint. CONTRIBUTING.md, CODE_OF_CONDUCT.md, SECURITY.md, issue/PR template, энэ CHANGELOG нэмэгдсэн.

## [v1.0.5] - 2026-01-22

Анхны хувилбар - 13 банкны валютын ханш цуглуулалт, FastAPI REST API, Docker, PostgreSQL/SQLite, cron scheduler.
