import re

URL = "https://www.superenalotto.it/archivio-estrazioni"
N_ESTRAZIONI = 4  # quante estrazioni (le più recenti per data) restituire

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "it-IT,it;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}
TIMEOUT = (10, 60)  # (connessione, lettura) in secondi
CFFI_TIMEOUT = 60  # timeout del fallback curl_cffi
RETRY_TOTALI = 3
RETRY_BACKOFF = 2
RETRY_STATUS = (429, 500, 502, 503, 504)

# --- Parsing ---
MESI = {
    "gennaio": 1, "febbraio": 2, "marzo": 3, "aprile": 4,
    "maggio": 5, "giugno": 6, "luglio": 7, "agosto": 8,
    "settembre": 9, "ottobre": 10, "novembre": 11, "dicembre": 12,
}

RE_TESTATA = re.compile(
    r"Concorso\s*N[^\s\d]{0,2}\s*(\d+)\s+del\s+(\d{1,2})\s+([A-Za-zÀ-ÿ]+)\s+(\d{4})",
    re.IGNORECASE,
)