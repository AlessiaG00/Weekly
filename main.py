import sys

from logger import get_logger
from mail import build_email_html, send_email
from src.scraper import ultime_estrazioni

logger = get_logger(__name__)


def main() -> int:
    logger.info("Avvio raccolta estrazioni SuperEnalotto...")

    try:
        estrazioni = ultime_estrazioni()
    except Exception:
        logger.exception("Errore durante l'esecuzione dello scraper")
        return 1

    if not estrazioni:
        logger.warning("Nessuna estrazione raccolta: email non inviata.")
        return 1

    logger.info(f"Raccolte {len(estrazioni)} estrazioni.")

    try:
        html = build_email_html(estrazioni)
        send_email(html, estrazioni)
    except Exception:
        logger.exception("Errore durante l'invio dell'email")
        return 1

    logger.info("Esecuzione completata con successo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())