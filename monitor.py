import requests
from bs4 import BeautifulSoup
import hashlib
import os

# =========================
# CONFIG
# =========================
URL = "https://eplay24.it/promozioni"

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

STATE_FILE = "state.txt"


# =========================
# TELEGRAM
# =========================
def send_telegram(message):
    if not BOT_TOKEN or not CHAT_ID:
        print("Missing secrets")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": message})


# =========================
# ESTRAZIONE SOLO PROMO
# =========================
def get_promotions(url):
    headers = {"User-Agent": "Mozilla/5.0"}

    r = requests.get(url, headers=headers, timeout=20)
    soup = BeautifulSoup(r.text, "html.parser")

    # rimuove rumore
    for tag in soup(["script", "style", "noscript", "svg", "footer", "header", "nav"]):
        tag.decompose()

    promos = []

    # prova a prendere blocchi "logici"
    for block in soup.find_all(["div", "section", "article"]):
        text = block.get_text(" ", strip=True)
        text = " ".join(text.split())

        # filtro minimo qualità
        if len(text) < 40:
            continue

        # deve sembrare promo
        keywords = ["promo", "bonus", "cashback", "offerta", "free", "spin", "%"]
        if any(k in text.lower() for k in keywords):
            promos.append(text)

    # fallback
    if not promos:
        promos = [soup.get_text(" ", strip=True)]

    return sorted(set(promos))


# =========================
# HASH STABILE
# =========================
def hash_data(data_list):
    joined = "||".join(sorted([d.lower().strip() for d in data_list]))
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
    promos = get_promotions(URL)
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
        send_telegram("⚠️ NUOVE PROMO RILEVATE!\n\nControlla il sito: " + URL)
        print("CAMBIAMENTO REALE RILEVATO")
    else:
        print("NESSUNA NUOVA PROMO")


if __name__ == "__main__":
    main()