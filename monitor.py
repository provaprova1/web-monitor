import requests
from bs4 import BeautifulSoup
import hashlib
import os

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
# ESTRAZIONE STABILE
# =========================
def get_promos(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=20)
    soup = BeautifulSoup(r.text, "html.parser")

    # rimuove rumore
    for tag in soup(["script", "style", "noscript", "svg", "footer", "header", "nav"]):
        tag.decompose()

    promos = set()

    # CERCA TITOLI + LINK (più stabile del testo intero)
    for a in soup.find_all("a"):
        text = a.get_text(" ", strip=True)
        href = a.get("href")

        if text and len(text) > 5:
            if any(k in text.lower() for k in ["promo", "bonus", "cashback", "offerta", "%"]):
                promos.add(text.lower().strip())

        if href and "/promo" in href:
            promos.add(href.strip())

    # fallback se non trova nulla
    if not promos:
        fallback = soup.get_text(" ", strip=True)
        promos = {" ".join(fallback.split())[:2000]}

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
    promos = get_promos(URL)

    new_hash = hash_data(promos)
    old_hash = load_state()

    print("PROMO TROVATE:", len(promos))
    print("HASH NUOVO:", new_hash)
    print("HASH VECCHIO:", old_hash)

    if old_hash is None:
        save_state(new_hash)
        send_telegram("🟢 Monitor avviato (baseline promo salvata)")
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