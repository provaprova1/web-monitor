import requests
from bs4 import BeautifulSoup
import hashlib
import os

# =========================
# CONFIG
# =========================
URL = "https://eplay24.it/promozioni"

# Se usi GitHub Actions (consigliato)
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    print("ERRORE: Secrets mancanti")
    exit(1)
print("BOT_TOKEN presente:", BOT_TOKEN is not None)
print("CHAT_ID presente:", CHAT_ID is not None)


# =========================
# TELEGRAM
# =========================
def send_telegram(message):
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
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    r = requests.get(url, headers=headers, timeout=15)
    soup = BeautifulSoup(r.text, "html.parser")

    # rimuove rumore
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()

    # prova a prendere solo contenuto principale
    main = soup.find("main")
    if main:
        text = main.get_text(separator=" ", strip=True)
    else:
        text = soup.get_text(separator=" ", strip=True)

    # normalizzazione forte
    text = " ".join(text.split())

    return text


# =========================
# HASH
# =========================
def hash_content(content):
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


# =========================
# STATO LOCALE
# =========================
def load_old():
    if os.path.exists("state.txt"):
        with open("state.txt", "r") as f:
            return f.read().strip()
    return None


def save_new(h):
    with open("state.txt", "w") as f:
        f.write(h)


# =========================
# MAIN
# =========================
def main():
    content = get_content(URL)
    new_hash = hash_content(content)
    old_hash = load_old()

    # prima esecuzione
    if old_hash is None:
        save_new(new_hash)
        send_telegram("🟢 Monitor avviato. Stato iniziale salvato.")
        print("Prima esecuzione → salvato stato")
        return

    # cambiamento
    if new_hash != old_hash:
        save_new(new_hash)
        print("⚠️ CAMBIAMENTO RILEVATO")

        send_telegram(
            "⚠️ CAMBIAMENTO RILEVATO!\n\nPagina promozioni aggiornata:\n" + URL
        )
    else:
        print("Nessun cambiamento")


if __name__ == "__main__":
    main()