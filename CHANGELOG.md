<!-- markdownlint-disable MD024 -->

# Өөрчлөлтийн Түүх

Бүх чухал өөрчлөлтүүд энд бүртгэгдэнэ.

## [Unreleased]

Одоогоор бүртгэсэн unreleased өөрчлөлт алга.

## [v1.0.9] - 2026-05-06

`v1.0.8` хувилбар банкны live API өөрчлөлтүүд болон Heroku worker import тохиргооноос шалтгаалан тогтворгүй байсан тул энэ хувилбараар тогтвортой дахин гаргав.

### Нэмсэн

- Public API хамгаалалт нэмэгдсэн: configurable CORS, pagination дээд хэмжээ, per-process rate limit, `Retry-After` болон `X-RateLimit-*` response header-ууд.
- Swagger/OpenAPI дээр банкны нэрсийг selectable enum болгож, API description-ийг илүү тодорхой болгосон.
- `.env.example` нэмэгдэж local, Docker, Heroku орчны үндсэн тохиргоонууд нэг дор харагддаг болсон.
- GitHub Release auto-generated notes-д зориулсан `.github/release.yml` label category тохиргоо нэмэгдсэн.
- API, scraper service, cron, backfill script-ийн нэмэлт regression test-үүд нэмэгдсэн.

### Өөрчилсөн

- Docker Compose нь `.env` файл заавал шаардахгүйгээр API, cron worker, PostgreSQL-г default тохиргоогоор асаадаг болсон.
- `python main.py` нь scraper ажиллуулахын өмнө database table-уудыг үүсгэдэг болсон.
- Cron worker нь `CRON_SCHEDULE`-ийн өдөр тутмын `M H * * *` хэлбэрийг ашиглаж ажилладаг болсон.
- Backfill script нь огнооны argument-уудаа Playwright/DB setup хийхээс өмнө шалгадаг болсон.
- README болон CONTRIBUTING файлуудыг beginner-friendly, одоогийн Python 3.11+, formatter, lint, Docker, release workflow-той нийцүүлэн шинэчилсэн.
- CI workflow дахь `ruff` шалгалт `main.py`-г хамардаг болсон; GitHub Release title нь tag-тэй ойлгомжтой нэрлэгдэнэ.

### Зассан

- `CAPITRONBANK_URI` хуучин нэршлийг `CAPITRONBANK_API_URL`-тай нийцүүлсэн.
- Heroku/container worker script `ModuleNotFoundError: No module named 'app'` алдааг `PYTHONPATH=/app` болон module-mode command ашиглан зассан.
- API date параметрүүд зөвхөн `YYYY-MM-DD` хэлбэрийг зөвшөөрдөг болсон.
- Rate limit-ийн proxy header trust нь default-оор унтраалттай, memory bucket нь хязгаартай болсон.
- StateBank-ийн шинэ list response болон `curCode`/`cashBuy` field нэршлийг parse хийдэг болсон.
- CapitronBank-ийн одоогийн lowercase `curcode`/`buyrate`/`salerate` response хэлбэрийг дэмждэг болсон.
- MongolBank-ийн одоогийн POST JSON endpoint-ийг ашиглаж, legacy XML parser-ийг fallback байдлаар үлдээсэн.
- TDBM-ийн өнөөдрийн ханшийг static HTML table-оос уншдаг болгож Playwright timeout-ийн flaky алдааг багасгасан.
- ArigBank-ийн expired/static bearer token-оос хамаарахгүйгээр `/exchange/signIn` endpoint-оос шинэ token авч ханш татдаг болсон.
- NaimanSharga-ийн Firestore document URL-д огноог API key query-ийн өмнө зөв залгаж өнөөдрийн ханшийг татдаг болсон.

### Шалгасан

- `2026-05-06` өдрийн live scrape-ээр 15/15 банк амжилттай хадгалагдсан.
- ArigBank 10 валют, NaimanSharga 23 валют татаж байгаа нь баталгаажсан.
- `isort`, `black`, `ruff`, `pytest` бүх шалгалт ногоон болсон.

## [v1.0.8] - 2026-05-05

> Энэ хувилбар тогтворгүй болсон тул `v1.0.9` хувилбараар солигдсон. Гол асуудлууд: ArigBank token expiry, NaimanSharga Firestore URL, MongolBank current JSON endpoint, StateBank/CapitronBank response shape drift, TDBM timeout, Heroku worker import тохиргоо.

### Нэмсэн

- **NaimanSharga** crawler — Найман шарга валют арилжааны ханш. Firebase Firestore REST API (`nsharga-2ec6a` төсөл) ашиглан `currency_rates/{огноо}` документаас `avah` (авах) болон `zarah` (зарах) утгуудыг татна. Өнөөдрийн мэдээлэл байхгүй бол өчигдрийн мэдээлэлд автоматаар шилждэг.
- **SendMN** crawler — SendMN гадаад мөнгөн гуйвуулгын үйлчилгээний ханш. Firebase Firestore REST API (`sendmn-remit` төсөл) ашиглан `rate/exrate` документаас `buy`/`sell` утгуудыг татна. USD, EUR, RUB, CNY, KRW, JPY, TRY, VND, PHP дэмжигдэнэ.
- `app/config.py`-д `SENDMN_FIRESTORE_URL` болон `NSHARGA_FIRESTORE_BASE_URL` тохиргоо нэмэгдсэн.

### Засагдсан (v1.0.7-аас хойш)

- **MongolBank** — XXE (XML External Entity) эмзэг байдлыг `etree.XMLParser(resolve_entities=False, no_network=True)` ашиглан засагдсан.
- **BogdBank** — `?date=YYYY-MM-DD` параметрийн буруу логикийг засагдсан; одоо бүх огноонд параметр зөв дамжуулагдана.
- **TDBM** — `self.date`-ийг үл тоодог байсан алдааг засаж, хүссэн огноог зөв ашиглах болсон.
- **TransBank** — Валютын кодын хэт өргөн шүүлтийг (`len(code) <= 10`) яг гурван тэмдэгт (`len(code) == 3`) болгон засагдсан.
- **MBank** — Нэвтрэх хүсэлтийн дуугүй алдааг `login_resp.raise_for_status()` нэмэн засагдсан.
- **CapitronBank** — `config.py`-д `CAPITRONBANK_URI` → `CAPITRONBANK_API_URL` орчны хувьсагчийн алдааг засагдсан.
- `requirements.txt` — Dependabot аюулгүй байдлын сэрэмжлүүлгүүдийг шийдвэрлэхийн тулд хамаарлуудын хувилбар шинэчлэгдсэн: `requests>=2.32.0`, `lxml>=5.2.0`, `Pygments>=2.15.0`, `pytest>=7.4.4`.
- `.github/workflows/ci.yml` — CodeQL дохионы шийдвэрлэлт: `lint-test` болон `docker-test` ажлуудад `permissions: contents: read` нэмэгдсэн.

### Тоо

- Нийт дэмжигдэх банкны тоо: **13 → 15**

## [v1.0.6] - 2026-02-06

### Өөрчилсөн

- Код бүтцийг бүхэлд нь сайжруулсан
- Crawler-уудыг нэгтгэж, давхардлыг арилгасан
- Base crawler class нэвтрүүлсэн
- Scraper service-ийг хялбарчилсан
- API endpoint-уудыг цэгцэлсэн
- Test-үүдийг шинэчилсэн

### Нэмсэн

- CONTRIBUTING.md
- CODE_OF_CONDUCT.md
- SECURITY.md
- GitHub issue/PR templates
- CHANGELOG.md

### Хассан

- Шаардлагагүй package-ууд
- Давхардсан код
- Хэрэгцээгүй комментууд

## [v1.0.5] - 2026-01-22

### Анхны хувилбар

- 13 банкны валютын ханш цуглуулалт
- FastAPI REST API
- Docker дэмжлэг
- PostgreSQL/SQLite өгөгдлийн сан
- Cron хуваарьт ажиллагаа
