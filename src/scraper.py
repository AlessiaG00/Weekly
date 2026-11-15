from datetime import date

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src import config


def _scarica_con_requests(url: str) -> str:
    sessione = requests.Session()
    retry = Retry(
        total=config.RETRY_TOTALI,
        connect=config.RETRY_TOTALI,
        read=config.RETRY_TOTALI,
        backoff_factor=config.RETRY_BACKOFF,
        status_forcelist=config.RETRY_STATUS,
        allowed_methods=["GET"],
    )
    sessione.mount("https://", HTTPAdapter(max_retries=retry))
    r = sessione.get(url, headers=config.HEADERS, timeout=config.TIMEOUT)
    r.raise_for_status()
    return r.text


def _scarica_con_curl_cffi(url: str) -> str:
    # Imita l'impronta TLS di Chrome: utile contro le protezioni anti-bot
    from curl_cffi import requests as cffi_requests

    r = cffi_requests.get(url, impersonate="chrome", timeout=config.CFFI_TIMEOUT)
    r.raise_for_status()
    return r.text


def scarica_pagina(url: str = config.URL) -> str:
    try:
        return _scarica_con_requests(url)
    except requests.exceptions.RequestException as e:
        print(f"[requests fallito: {type(e).__name__}] provo con curl_cffi...")
        try:
            return _scarica_con_curl_cffi(url)
        except ImportError:
            raise RuntimeError(
            ) from e


def estrai_estrazioni(html: str) -> list[dict]:
    """Legge tutte le estrazioni presenti nella tabella dell'archivio."""
    soup = BeautifulSoup(html, "html.parser")
    trovate = {}

    for tr in soup.find_all("tr"):
        celle = tr.find_all("td")
        if len(celle) < 4:
            continue

        m = config.RE_TESTATA.search(celle[0].get_text(" ", strip=True))
        if not m:
            continue

        concorso, giorno, mese, anno = m.groups()
        mese_num = config.MESI.get(mese.lower())
        if mese_num is None:
            continue

        numeri = [int(x) for x in celle[1].stripped_strings if x.isdigit()]
        jolly = celle[2].get_text(strip=True)
        superstar = celle[3].get_text(strip=True)

        if len(numeri) != 6 or not jolly.isdigit() or not superstar.isdigit():
            continue  # riga anomala, la salto

        trovate[int(concorso)] = {
            "concorso": int(concorso),
            "data": date(int(anno), mese_num, int(giorno)),
            "numeri": numeri,
            "jolly": int(jolly),
            "superstar": int(superstar),
        }

    return list(trovate.values())


def ultime_estrazioni(n: int = config.N_ESTRAZIONI) -> list[dict]:
    """Ordina per data (più recente prima) e restituisce le prime n."""
    estrazioni = estrai_estrazioni(scarica_pagina())
    if not estrazioni:
        raise RuntimeError("Nessuna estrazione trovata: la struttura della pagina potrebbe essere cambiata.")
    estrazioni.sort(key=lambda e: (e["data"], e["concorso"]), reverse=True)
    return estrazioni[:n]


if __name__ == "__main__":
    for e in ultime_estrazioni():
        numeri = " - ".join(f"{x:02d}" for x in e["numeri"])
        print(
            f"Concorso {e['concorso']} del {e['data']:%d/%m/%Y}: {numeri} | "
            f"Jolly: {e['jolly']} | SuperStar: {e['superstar']}"
        )