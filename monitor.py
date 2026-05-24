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
# ESTRAZIONE PROMO STABILI
# =========================
def extract_promos():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = browser.new_page()

        page.goto(URL, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(4000)

        elements = page.query_selector_all("a, h2, h3, p")

        promos = []

        for el in elements:
            try:
                text = el.inner_text().lower().strip()
                text = " ".join(text.split())

                if len(text) < 10:
                    continue

                # filtro anti rumore
                if any(k in text for k in ["bonus", "promo", "cashback", "freebet", "rimborso"]):
                    promos.append(text[:140])

            except:
                continue

        browser.close()

        return sorted(set(promos))


# =========================
# HASH STABILE
# =========================
def make_hash(data):
    return hashlib.sha256("\n".join(data).encode("utf-8")).hexdigest()


# =========================
# STATE
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
    print("RUN START")

    promos = extract_promos()
    new_hash = make_hash(promos)
    old_hash = load_state()

    print("PROMOS FOUND:", len(promos))
    print("OLD HASH:", old_hash)
    print("NEW HASH:", new_hash)

    # 🟢 PRIMO RUN
    if old_hash is None:
        save_state(new_hash)
        send_telegram("🟢 Monitor avviato (baseline iniziale)")
        print("BASELINE CREATED")
        return

    # ⚠️ CAMBIAMENTO
    if new_hash != old_hash:
        save_state(new_hash)
        send_telegram("⚠️ NUOVE PROMO RILEVATE!\n\n" + URL)
        print("CHANGE DETECTED")
    else:
        print("NO CHANGE")


if __name__ == "__main__":
    main()
