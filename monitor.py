import os
import hashlib
import requests
from bs4 import BeautifulSoup

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
# ESTRAZIONE PROMO STRUTTURATE
# =========================
def extract_promos():
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(URL, headers=headers, timeout=20)
    soup = BeautifulSoup(r.text, "html.parser")

    # rimuove rumore
    for tag in soup(["script", "style", "noscript", "svg", "footer", "header", "nav"]):
        tag.decompose()

    promos = set()

    # CERCHIAMO “card-like content”
    for block in soup.find_all(["div", "section", "article"]):

        text = block.get_text(" ", strip=True)
        text = " ".join(text.split())

        # filtro qualità minimo
        if len(text) < 30:
            continue

        # deve sembrare promo
        keywords = ["bonus", "promo", "cashback", "offerta", "%", "free", "spin"]

        if any(k in text.lower() for k in keywords):

            # normalizzazione forte
            cleaned = text.lower().strip()

            # riduce rumore numerico random
            cleaned = "".join(c for c in cleaned if c.isalnum() or c.isspace())

            promos.add(cleaned)

    return sorted(promos)


# =========================
# HASH STABILE
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
    promos = extract_promos()

    new_hash = hash_data(promos)
    old_hash = load_state()

    print("PROMO TROVATE:", len(promos))
    print("HASH NUOVO:", new_hash)
    print("HASH VECCHIO:", old_hash)

    # DEBUG UTILE (puoi lasciarlo o rimuoverlo)
    for p in promos[:5]:
        print("PROMO:", p)

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