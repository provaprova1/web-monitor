import os
import hashlib
import requests
from playwright.sync_api import sync_playwright

URL = "https://eplay24.it/promozioni"

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

STATE_FILE = "state.txt"


# =========================
# TELEGRAM
# =========================
def send_telegram(msg):
    if not BOT_TOKEN or not CHAT_ID:
        print("Missing Telegram config")
        return

    try:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg},
            timeout=10
        )
    except Exception as e:
        print("Telegram error:", e)


# =========================
# ESTRAZIONE CONTENUTO STABILE
# =========================
def extract_content():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )

        page = browser.new_page()
        page.goto(URL, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(5000)

        # SOLO contenuto visibile stabile
        content = page.inner_text("body")

        browser.close()

        # normalizzazione forte (riduce falsi positivi)
        content = " ".join(content.lower().split())

        return content


# =========================
# HASH
# =========================
def make_hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# =========================
# STATE (persistito su repo)
# =========================
def load_state():
    if not os.path.exists(STATE_FILE):
        return None

    with open(STATE_FILE, "r") as f:
        return f.read().strip()


def save_state(h):
    with open(STATE_FILE, "w") as f:
        f.write(h)


# =========================
# MAIN
# =========================
def main():
    content = extract_content()
    new_hash = make_hash(content)
    old_hash = load_state()

    print("NEW HASH:", new_hash)
    print("OLD HASH:", old_hash)
    print("STATE FILE EXISTS:", os.path.exists(STATE_FILE))

    # 🔥 PRIMO RUN
    if old_hash is None:
        save_state(new_hash)
        send_telegram("🟢 Monitor avviato (baseline salvata)")
        print("INIT OK")
        return

    # 🔥 CAMBIO
    if new_hash != old_hash:
        save_state(new_hash)
        send_telegram("⚠️ NUOVE PROMO RILEVATE!\n\n" + URL)
        print("CHANGE DETECTED")
    else:
        print("NO CHANGE")


if __name__ == "__main__":
    main()
