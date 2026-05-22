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
        print("❌ Secrets mancanti")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message
    }
    requests.post(url, data=data)


# =========================
# ESTRAZIONE CONTENUTO
# =========================
def get_content(url):
    headers = {"User-Agent": "Mozilla/5.0"}

    r = requests.get(url, headers=headers, timeout=20)
    soup = BeautifulSoup(r.text, "html.parser")

    # rimuove rumore
    for tag in soup(["script", "style", "noscript", "svg", "footer", "header", "nav"]):
        tag.decompose()

    main = soup.find("main")

    if main:
        text = main.get_text(" ", strip=True)
    else:
        text = soup.get_text(" ", strip=True)

    return " ".join(text.split())


# =========================
# HASH
# =========================
def hash_content(content):
    content = content.lower()
    content = " ".join(content.split())
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


# =========================
# STATO (PERSISTENTE SU FILE)
# =========================
def load_old_hash():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return f.read().strip()
    return None


def save_new_hash(h):
    with open(STATE_FILE, "w") as f:
        f.write(h)


# =========================
# MAIN
# =========================
def main():
    content = get_content(URL)
    new_hash = hash_content(content)
    old_hash = load_old_hash()

    print("HASH NUOVO:", new_hash)
    print("HASH VECCHIO:", old_hash)

    # primo run
    if old_hash is None:
        save_new_hash(new_hash)
        send_telegram("🟢 Monitor avviato. Stato iniziale salvato.")
        print("INIT OK")
        return

    # cambiamento
    if new_hash != old_hash:
        save_new_hash(new_hash)

        send_telegram(
            "⚠️ CAMBIAMENTO RILEVATO!\n\n"
            "Pagina aggiornata:\n" + URL
        )

        print("CAMBIAMENTO RILEVATO")
    else:
        print("NESSUN CAMBIAMENTO")


if __name__ == "__main__":
    main()