"""Legge il monitor pubblico del Pronto Soccorso del GOM di Reggio Calabria
e aggiunge una riga al file CSV del mese in data/.

Il monitor si apre da una pagina "ponte" che genera un ticket temporaneo
e carica il vero monitor in un iframe: il programma fa lo stesso percorso
di un browser. Il ticket non viene mai salvato.
"""

import csv
import html
import http.cookiejar
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

BRIDGE_URL = "https://prontosoccorso.ospedalerc.it/areasLoginBridge/"
USER_AGENT = "InSala-monitor/1.0 (progetto civico; lettura ogni 5 minuti)"
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

FIELDS = [
    "letto_utc", "letto_roma", "aggiornato_monitor",
    "rossi_entrati", "arancioni_entrati", "azzurri_entrati",
    "verdi_entrati", "bianchi_entrati",
    "totale_entrati", "in_attesa", "affollamento", "casi_24h",
]


def fetch(opener, url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with opener.open(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def input_value(page, name):
    m = re.search(r"<input[^>]*name='%s'[^>]*value='(\d+)'" % name, page)
    return int(m.group(1)) if m else None


def span_text(page, span_id):
    m = re.search(r"<span[^>]*id='%s'[^>]*>(.*?)</span>" % span_id, page, re.S)
    return html.unescape(m.group(1)).strip() if m else None


def last_int(text):
    if text is None:
        return None
    m = re.findall(r"\d+", text)
    return int(m[-1]) if m else None


def parse_monitor(page):
    aggiornato = span_text(page, "lblAggiornato")
    if aggiornato:
        aggiornato = re.sub(r"\s+", " ", aggiornato.replace("Aggiornato alle ore :", "")).strip()
    affollamento = span_text(page, "lblInfo3")
    if affollamento and ":" in affollamento:
        affollamento = affollamento.split(":", 1)[1].strip()
    row = {
        "aggiornato_monitor": aggiornato,
        "rossi_entrati": input_value(page, "txtCodiciRossi"),
        "arancioni_entrati": input_value(page, "txtCodiciArancioni"),
        "azzurri_entrati": input_value(page, "txtCodiciAzzurri"),
        "verdi_entrati": input_value(page, "txtCodiciVerdi"),
        "bianchi_entrati": input_value(page, "txtCodiciBianchi"),
        "totale_entrati": last_int(span_text(page, "lblInfo1")),
        "in_attesa": last_int(span_text(page, "lblInfo2")),
        "affollamento": affollamento,
        "casi_24h": last_int(span_text(page, "lblInfo4")),
    }
    if row["in_attesa"] is None or row["verdi_entrati"] is None:
        raise ValueError("Il monitor non ha la forma attesa: forse la pagina è cambiata.")
    return row


def read_live():
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    bridge = fetch(opener, BRIDGE_URL)
    m = re.search(r'<iframe[^>]*id="iframeMonitor"[^>]*src="([^"]+)"', bridge)
    if not m:
        raise ValueError("Non trovo il monitor nella pagina ponte.")
    return fetch(opener, html.unescape(m.group(1)))


def append_row(row, now):
    os.makedirs(DATA_DIR, exist_ok=True)
    path = os.path.join(DATA_DIR, "monitor_gom_%s.csv" % now.astimezone(ZoneInfo("Europe/Rome")).strftime("%Y-%m"))
    new_file = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if new_file:
            writer.writeheader()
        writer.writerow(row)
    return path


def main():
    now = datetime.now(timezone.utc)
    page = sys.stdin.read() if "--stdin" in sys.argv else read_live()
    row = parse_monitor(page)
    row["letto_utc"] = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    row["letto_roma"] = now.astimezone(ZoneInfo("Europe/Rome")).strftime("%Y-%m-%d %H:%M:%S")
    if "--dry-run" in sys.argv:
        print(row)
        return
    path = append_row(row, now)
    print("Salvato in %s: %s in attesa, %s" % (os.path.basename(path), row["in_attesa"], row["affollamento"]))


if __name__ == "__main__":
    main()
