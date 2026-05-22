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
# ESTRAZIONE INTELLIGENTE
# =========================
def get_content(url):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    r = requests.get(url, headers=headers, timeout=15)
    soup = BeautifulSoup(r.text, "html.parser")

    # rimuove rumore inutile
    for tag in soup(["script", "style", "noscript", "svg", "footer", "header", "nav"]):
        tag.decompose()

    # parole chiave rilevanti (filtraggio intelligente)
    keywords = ["promo", "bonus", "offerta", "cashback", "free", "giri", "spin"]

    blocks = []

    for tag in soup.find_all(["div", "section", "article"]):
        text = tag.get_text(" ", strip=True)
        text = " ".join(text.split())

        if len(text) > 30:
            if any(k in text.lower() for k in keywords):
                blocks.append(text)

    # fallback (se non trova blocchi buoni)
    if not blocks:
        text = soup.get_text(" ", strip=True)
        return " ".join(text.split())

    return " | ".join(blocks)


# =========================
# HASH ROBUSTO
# =========================
def hash_content(content):
    content = content.lower()
    content = " ".join(content.split())
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


# =========================
# STATO
# =========================
def load_old():
    if os.path.exists("state.txt"):
        return open("state.txt").read().strip()
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

    print("HASH NUOVO:", new_hash)
    print("HASH VECCHIO:", old_hash)

    if old_hash is None:
        save_new(new_hash)
        send_telegram("🟢 Monitor avviato. Stato iniziale salvato.")
        print("INIT OK")
        return

    if new_hash != old_hash:
        save_new(new_hash)

        send_telegram(
            "⚠️ CAMBIAMENTO RILEVATO!\n\n"
            "Pagina promozioni aggiornata:\n" + URL
        )

        print("CAMBIAMENTO RILEVATO")
    else:
        print("NESSUN CAMBIAMENTO")


if __name__ == "__main__":
    main()