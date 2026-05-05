# Өөрчлөлтийн Түүх

Бүх чухал өөрчлөлтүүд энд бүртгэгдэнэ.

## [v1.0.8] - 2026-05-05

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
