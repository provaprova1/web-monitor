import os
import hashlib
import requests
from playwright.sync_api import sync_playwright

URL = "https://eplay24.it/promozioni"

STATE_FILE = "state.txt"
SCREENSHOT_FILE = "promo_section.png"

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")


# =========================
# TELEGRAM
# =========================
def send(msg):
    if not BOT_TOKEN or not CHAT_ID:
        print("Missing Telegram config")
        return

    try:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data={
                "chat_id": CHAT_ID,
                "text": msg
            },
            timeout=10
        )
    except Exception as e:
        print("Telegram error:", e)


# =========================
# HASH FILE
# =========================
def file_hash(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


# =========================
# STATE
# =========================
def load_state():
    if not os.path.exists(STATE_FILE):
        return None

    return open(STATE_FILE, "r").read().strip()


def save_state(h):
    with open(STATE_FILE, "w") as f:
        f.write(h)


# =========================
# SCREENSHOT SEZIONE PROMO
# =========================
def capture_section():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox"]
        )

        page = browser.new_page(
            viewport={"width": 1400, "height": 3000}
        )

        page.goto(URL, wait_until="networkidle", timeout=60000)

        # attesa JS
        page.wait_for_timeout(10000)

        # scroll per lazy loading
        page.mouse.wheel(0, 4000)
        page.wait_for_timeout(3000)

        # screenshot completo
        page.screenshot(
            path=SCREENSHOT_FILE,
            full_page=True
        )

        browser.close()


# =========================
# MAIN
# =========================
def main():
    print("RUN START")

    capture_section()

    new_hash = file_hash(SCREENSHOT_FILE)
    old_hash = load_state()

    print("OLD:", old_hash)
    print("NEW:", new_hash)

    # primo run
    if old_hash is None:
        save_state(new_hash)

        send("🟢 Monitor visuale avviato (baseline iniziale)")

        print("BASELINE CREATED")
        return

    # cambiamento visivo
    if new_hash != old_hash:
        save_state(new_hash)

        send(
            "⚠️ CAMBIAMENTO VISIVO RILEVATO NELLE PROMO!\n\n"
            + URL
        )

        print("CHANGE DETECTED")

    else:
        print("NO CHANGE")


if __name__ == "__main__":
    main()
