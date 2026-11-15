import csv
import io
import os
import smtplib
import ssl
from datetime import date
from email.message import EmailMessage
from html import escape

from logger import get_logger

try:  # opzionale: carica le variabili da un file .env (pip install python-dotenv)
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

logger = get_logger(__name__)

# --- Impostazioni SMTP (da variabili d'ambiente / secret GitHub) ---
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))  # 587 = STARTTLS, 465 = SSL
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", SMTP_USER)
EMAIL_TO = [a.strip() for a in os.getenv("EMAIL_TO", "").split(",") if a.strip()]

# --- Contenuto della mail ---
EMAIL_TITLE = "Estrazioni Del SuperEnalotto"
CSV_FILENAME = "risultato_estrazioni_weekly.csv"
CSV_DELIMITER = ";"  # ";" si apre correttamente in Excel italiano
TABLE_HEADERS = ("Concorso e combinazione vincente", "Jolly", "SuperStar")


def _righe_tabella(estrazioni: list[dict]) -> list[tuple[str, str, str]]:
    """Trasforma le estrazioni nelle 3 colonne della tabella (usate anche per il CSV).

    Esempio riga:
    ("Concorso 183 del 14/11/2026: 26 - 40 - 49 - 64 - 66 - 74", "61", "5")
    """
    righe = []
    for e in estrazioni:
        numeri = " - ".join(str(n) for n in e["numeri"])
        concorso = f"Concorso {e['concorso']} del {e['data']:%d/%m/%Y}: {numeri}"
        righe.append((concorso, str(e["jolly"]), str(e["superstar"])))
    return righe


def build_email_html(estrazioni: list[dict], data_invio: date | None = None) -> str:
    data_invio = data_invio or date.today()
    th_style = "padding:8px 12px;border:1px solid #cccccc;background:#f0f0f0;text-align:left;"
    td_style = "padding:8px 12px;border:1px solid #cccccc;"

    intestazione = "".join(f'<th style="{th_style}">{escape(h)}</th>' for h in TABLE_HEADERS)
    righe = "".join(
        "<tr>" + "".join(f'<td style="{td_style}">{escape(c)}</td>' for c in riga) + "</tr>"
        for riga in _righe_tabella(estrazioni)
    )

    return f"""<!DOCTYPE html>
<html lang="it">
<body style="font-family:Arial,Helvetica,sans-serif;color:#222222;">
  <h2 style="margin-bottom:4px;">{escape(EMAIL_TITLE)}</h2>
  <p style="margin-top:0;color:#555555;">Data di invio: {data_invio:%d/%m/%Y}</p>
  <table style="border-collapse:collapse;font-size:14px;">
    <thead><tr>{intestazione}</tr></thead>
    <tbody>{righe}</tbody>
  </table>
  <p style="color:#777777;font-size:12px;">In allegato il file {escape(CSV_FILENAME)} con gli stessi risultati.</p>
</body>
</html>"""


def build_csv(estrazioni: list[dict]) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=CSV_DELIMITER)
    writer.writerow(TABLE_HEADERS)
    writer.writerows(_righe_tabella(estrazioni))
    return buffer.getvalue().encode("utf-8-sig")  # BOM: Excel legge bene gli accenti


def send_email(html: str, estrazioni: list[dict], data_invio: date | None = None) -> None:
    if not EMAIL_TO:
        raise ValueError("Nessun destinatario: imposta EMAIL_TO (secret GitHub o file .env)")
    if not SMTP_USER or not SMTP_PASSWORD:
        raise ValueError("Credenziali SMTP mancanti: imposta SMTP_USER e SMTP_PASSWORD")

    data_invio = data_invio or date.today()

    msg = EmailMessage()
    msg["Subject"] = f"{EMAIL_TITLE} - {data_invio:%d/%m/%Y}"
    msg["From"] = EMAIL_FROM
    msg["To"] = ", ".join(EMAIL_TO)
    msg.set_content(
        "Questa email contiene tabelle HTML: apri il messaggio con un client che le supporta.\n"
        f"In allegato trovi {CSV_FILENAME}."
    )
    msg.add_alternative(html, subtype="html")
    msg.add_attachment(
        build_csv(estrazioni),
        maintype="text",
        subtype="csv",
        filename=CSV_FILENAME,
    )

    contesto = ssl.create_default_context()
    if SMTP_PORT == 465:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=contesto, timeout=30) as smtp:
            smtp.login(SMTP_USER, SMTP_PASSWORD)
            smtp.send_message(msg)
    else:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as smtp:
            smtp.starttls(context=contesto)
            smtp.login(SMTP_USER, SMTP_PASSWORD)
            smtp.send_message(msg)

    logger.info(f"Email inviata a: {msg['To']}")