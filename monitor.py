import requests
from bs4 import BeautifulSoup
import hashlib
import os
from urllib.parse import urljoin, urlparse

URL = "https://eplay24.it/promozioni"

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

STATE_FILE = "state.txt"


# =========================
# TELEGRAM
# =========================
def send_telegram(msg):
    if not BOT_TOKEN or not CHAT_ID:
        print("Missing secrets")
        return

    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": msg}
    )


# =========================
# NORMALIZZAZIONE URL
# =========================
def clean_url(href):
    if not href:
        return None

    # assolutizza URL
    full = urljoin(URL, href)

    # rimuove query string (IMPORTANTISSIMO)
    parsed = urlparse(full)
    clean = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

    return clean


# =========================
# ESTRAZIONE PROMO STABILE
# =========================
def get_promos():
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(URL, headers=headers, timeout=20)
    soup = BeautifulSoup(r.text, "html.parser")

    for tag in soup(["script", "style", "noscript", "svg", "footer", "header", "nav"]):
        tag.decompose()

    promos = set()

    # SOLO LINK (molto più stabile del testo)
    for a in soup.find_all("a", href=True):
        href = clean_url(a["href"])

        if href and "eplay24.it" in href:
            promos.add(href)

    # fallback minimo
    if not promos:
        promos.add(URL)

    return sorted(promos)


# =========================
# HASH
# =========================
def hash_data(data):
    joined = "||".join(sorted(data))
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


# =========================
# STATE
# =========================
def load_state():
    if os.path.exists(STATE_FILE):
        return open(STATE_FILE).read().strip()
    return None


def save_state(h):
    with open(STATE_FILE, "w") as f:
        f.write(h)


# =========================
# MAIN
# =========================
def main():
    promos = get_promos()

    new_hash = hash_data(promos)
    old_hash = load_state()

    print("PROMO TROVATE:", len(promos))
    print("HASH NUOVO:", new_hash)
    print("HASH VECCHIO:", old_hash)

    if old_hash is None:
        save_state(new_hash)
        send_telegram("🟢 Monitor avviato (baseline salvata)")
        print("INIT OK")
        return

    if new_hash != old_hash:
        save_state(new_hash)
        send_telegram("⚠️ NUOVE PROMO RILEVATE!\n\n" + URL)
        print("CAMBIAMENTO REALE")
    else:
        print("NESSUNA VARIAZIONE")


if __name__ == "__main__":
    main()