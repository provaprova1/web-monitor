import os
import hashlib
import requests
from playwright.sync_api import sync_playwright

URL = "https://eplay24.it/promozioni"

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

STATE_URL = os.environ.get("STATE_URL")  # raw GitHub file o gist


def send_telegram(msg):
    if not BOT_TOKEN or not CHAT_ID:
        print("Missing Telegram config")
        return

    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": msg},
        timeout=10
    )


def extract_content():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = browser.new_page()

        page.goto(URL, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(5000)

        content = page.inner_text("body")

        browser.close()

        return " ".join(content.lower().split())


def hash_text(t):
    return hashlib.sha256(t.encode()).hexdigest()


def load_state():
    if not STATE_URL:
        return None
    try:
        r = requests.get(STATE_URL, timeout=10)
        if r.status_code == 200:
            return r.text.strip()
    except:
        pass
    return None


def main():
    content = extract_content()

    new_hash = hash_text(content)
    old_hash = load_state()

    print("STATE URL:", STATE_URL)
    print("OLD:", old_hash)
    print("NEW:", new_hash)

    # 🔥 FIX DEFINITIVO
    if old_hash is None:
        send_telegram("🟢 Monitor avviato (baseline iniziale)")
        print("INIT OK")
        return

    if new_hash != old_hash:
        send_telegram("⚠️ NUOVE PROMO RILEVATE!\n\n" + URL)
        print("CHANGE")
    else:
        print("NO CHANGE")


if __name__ == "__main__":
    main()
