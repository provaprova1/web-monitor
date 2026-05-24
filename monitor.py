import os
import hashlib
import requests
from playwright.sync_api import sync_playwright
from PIL import Image, ImageChops
import io

URL = "https://eplay24.it/promozioni"

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

STATE_FILE = "state.png"


# =========================
# TELEGRAM
# =========================
def send_telegram(msg):
    if not BOT_TOKEN or not CHAT_ID:
        print("Missing Telegram config")
        return

    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": msg},
        timeout=10
    )


# =========================
# SCREENSHOT SEZIONE
# =========================
def take_screenshot():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = browser.new_page()

        page.goto(URL, wait_until="networkidle", timeout=60000)

        page.wait_for_timeout(5000)

        # screenshot pagina intera
        screenshot = page.screenshot(full_page=True)

        browser.close()

        return screenshot


# =========================
# DIFF IMMAGINI
# =========================
def images_different(img1_bytes, img2_bytes):
    img1 = Image.open(io.BytesIO(img1_bytes)).convert("RGB")
    img2 = Image.open(io.BytesIO(img2_bytes)).convert("RGB")

    diff = ImageChops.difference(img1, img2)

    # misura differenza totale
    bbox = diff.getbbox()

    return bbox is not None


# =========================
# STATE
# =========================
def load_state():
    if os.path.exists(STATE_FILE):
        return open(STATE_FILE, "rb").read()
    return None


def save_state(img_bytes):
    with open(STATE_FILE, "wb") as f:
        f.write(img_bytes)


# =========================
# MAIN
# =========================
def main():
    current = take_screenshot()

    old = load_state()

    if old is None:
        save_state(current)
        send_telegram("🟢 Monitor avviato (baseline visiva salvata)")
        print("INIT OK")
        return

    if images_different(old, current):
        save_state(current)
        send_telegram("⚠️ NUOVE PROMO RILEVATE!\n\n" + URL)
        print("CAMBIAMENTO RILEVATO")
    else:
        print("NESSUNA VARIAZIONE")


if __name__ == "__main__":
    main()
