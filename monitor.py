import os
import hashlib
import requests
from playwright.sync_api import sync_playwright

URL = "https://eplay24.it/promozioni"

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

IMAGE_FILE = "snapshot.png"
HASH_FILE = "state.txt"


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
# SCREENSHOT SEZIONE
# =========================
def take_snapshot():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(URL, wait_until="networkidle", timeout=60000)

        # aspetta caricamento
        page.wait_for_timeout(3000)

        # 👉 CERCA SEZIONE "PROMOZIONI SPORT"
        # (fallback generico se non trova esatto)
        try:
            element = page.locator("text=Promozioni Sport").first
            box = element.bounding_box()

            if box:
                page.screenshot(path=IMAGE_FILE, clip=box)
            else:
                page.screenshot(path=IMAGE_FILE, full_page=True)

        except:
            page.screenshot(path=IMAGE_FILE, full_page=True)

        browser.close()


# =========================
# HASH IMMAGINE
# =========================
def hash_image():
    with open(IMAGE_FILE, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


# =========================
# STATE
# =========================
def load_hash():
    if os.path.exists(HASH_FILE):
        return open(HASH_FILE).read().strip()
    return None


def save_hash(h):
    with open(HASH_FILE, "w") as f:
        f.write(h)


# =========================
# MAIN
# =========================
def main():
    take_snapshot()

    new_hash = hash_image()
    old_hash = load_hash()

    print("HASH NUOVO:", new_hash)
    print("HASH VECCHIO:", old_hash)

    if old_hash is None:
        save_hash(new_hash)
        send_telegram("🟢 Monitor visuale avviato")
        print("INIT OK")
        return

    if new_hash != old_hash:
        save_hash(new_hash)
        send_telegram("⚠️ CAMBIAMENTO GRAFICO RILEVATO (Promozioni Sport)")
        print("CAMBIAMENTO VISIVO")
    else:
        print("NESSUN CAMBIAMENTO")


if __name__ == "__main__":
    main()