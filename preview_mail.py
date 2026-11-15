import argparse
import sys
import webbrowser
from datetime import date
from pathlib import Path

from logger import get_logger
from mail import CSV_FILENAME, EMAIL_TITLE, build_csv, build_email_html
from src.scraper import ultime_estrazioni

logger = get_logger(__name__)

PREVIEW_DIR = Path(__file__).resolve().parent / "preview"


def main() -> int:
    parser = argparse.ArgumentParser(description="Anteprima della email SuperEnalotto")
    parser.add_argument("--no-open", action="store_true", help="non aprire il browser")
    args = parser.parse_args()

    logger.info("Raccolta estrazioni dallo scraper...")
    try:
        estrazioni = ultime_estrazioni()
    except Exception:
        logger.exception("Errore durante l'esecuzione dello scraper")
        return 1

    html = build_email_html(estrazioni)

    PREVIEW_DIR.mkdir(exist_ok=True)
    html_path = PREVIEW_DIR / "preview_mail.html"
    csv_path = PREVIEW_DIR / CSV_FILENAME
    html_path.write_text(html, encoding="utf-8")
    csv_path.write_bytes(build_csv(estrazioni))

    logger.info(f"Estrazioni nella mail: {len(estrazioni)}")
    logger.info(f"Anteprima HTML: {html_path}")
    logger.info(f"Allegato CSV:   {csv_path}")
    logger.info(f"Oggetto: {EMAIL_TITLE} - {date.today():%d/%m/%Y}")

    if not args.no_open:
        webbrowser.open(html_path.as_uri())

    return 0


if __name__ == "__main__":
    sys.exit(main())
