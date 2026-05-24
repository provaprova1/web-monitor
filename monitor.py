import os
import hashlib
import requests
from playwright.sync_api import sync_playwright

URL = "https://eplay24.it/promozioni"

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

STATE_URL = os.environ.get("STATE_URL")  # 👈 stato remoto


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
# CONTENUTO
# =========================
def extract_content():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = browser.new_page()

        page.goto(URL, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(5000)

        content = page.inner_text("body")

        browser.close()

        return " ".join(content.lower().split())


# =========================
# HASH
# =========================
def make_hash(t):
    return hashlib.sha256(t.encode()).hexdigest()


# =========================
# STATE REMOTO (CRUCIALE)
# =========================
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


def save_state(h):
    # qui puoi usare GitHub API o gist update
    print("NEW STATE WOULD BE:", h)


# =========================
# MAIN
# =========================
def main():
    content = extract_content()
    new_hash = make_hash(content)
    old_hash = load_state()

    print("OLD:", old_hash)
    print("NEW:", new_hash)

    # 🔥 FIX ASSOLUTO
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
