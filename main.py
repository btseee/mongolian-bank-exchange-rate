from app.db.database import init_db
from app.services.scraper import ScraperService
from app.utils.playwright_setup import ensure_playwright_browsers


def main():
    ensure_playwright_browsers()
    init_db()
    ScraperService().run_all()


if __name__ == "__main__":
    main()
