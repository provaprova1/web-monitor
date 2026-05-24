import os
import hashlib
import requests
from playwright.sync_api import sync_playwright

URL = "https://eplay24.it/promozioni"

STATE_FILE = "state.txt"

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
            data={"chat_id": CHAT_ID, "text": msg},
            timeout=10
        )
    except Exception as e:
        print("Telegram error:", e)


# =========================
# STATE
# =========================
def load_state():
    if not os.path.exists(STATE_FILE):
        return None
    return open(STATE_FILE, "r").read().strip()


def save_state(v):
    with open(STATE_FILE, "w") as f:
        f.write(v)


def make_hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# =========================
# EXTRACT SOLO PROMO SPORT
# =========================
def extract_promos():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = browser.new_page()

        page.goto(URL, wait_until="networkidle", timeout=60000)

        # attesa JS
        page.wait_for_timeout(8000)

        # scroll per trigger contenuti dinamici
        page.mouse.wheel(0, 3000)
        page.wait_for_timeout(3000)

        # 🔥 CERCA SOLO SEZIONE PROMO SPORT
        section = page.query_selector("text=Promozioni Sport")

        if section:
            text = section.evaluate("""
                el => el.parentElement ? el.parentElement.innerText : el.innerText
            """)
            browser.close()
            return text.lower().strip()

        # fallback se non trova la sezione
        html = page.content()
        browser.close()
        return html[:2000]


# =========================
# MAIN
# =========================
def main():
    print("RUN START")

    data = extract_promos()
    new_hash = make_hash(data)
    old_hash = load_state()

    print("OLD:", old_hash)
    print("NEW:", new_hash)

    # primo run
    if old_hash is None:
        save_state(new_hash)
        send("🟢 Monitor avviato (baseline iniziale)")
        print("BASELINE CREATED")
        return

    # cambiamento
    if new_hash != old_hash:
        save_state(new_hash)
        send("⚠️ NUOVE PROMO RILEVATE!\n\n" + URL)
        print("CHANGE DETECTED")
    else:
        print("NO CHANGE")


if __name__ == "__main__":
    main()
