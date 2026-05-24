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

    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": msg},
        timeout=10
    )


# =========================
# ESTRAZIONE PROMO REALI (CARD-BASED)
# =========================
def extract_promos():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )

        page = browser.new_page()
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(5000)

        cards = page.query_selector_all("a, div")

        promos = []

        for c in cards:
            try:
                text = c.inner_text().strip().lower()
                href = c.get_attribute("href")

                if not text:
                    continue

                # filtro minimo “promo-like”
                if any(k in text for k in ["bonus", "promo", "cashback", "freebet", "rimborso", "€", "%"]):

                    key = (text[:120] + "|" + (href or "")).strip()
                    promos.append(key)

            except:
                continue

        browser.close()

        return sorted(set(promos))


# =========================
# HASH
# =========================
def make_hash(data):
    return hashlib.sha256("\n".join(data).encode()).hexdigest()


# =========================
# STATE
# =========================
def load_state():
    if os.path.exists(STATE_FILE):
        return open(STATE_FILE).read().strip()
    return None


def save_state(h):
    with open(STATE_FILE, "w") as f:
        f.write(h)


# =========================
# MAIN
# =========================
def main():
    promos = extract_promos()

    print("PROMO TROVATE:", len(promos))

    new_hash = make_hash(promos)
    old_hash = load_state()

    print("HASH NUOVO:", new_hash)
    print("HASH VECCHIO:", old_hash)

    if old_hash is None:
        save_state(new_hash)
        send_telegram("🟢 Monitor avviato (baseline promo salvata)")
        print("INIT OK")
        return

    if new_hash != old_hash:
        save_state(new_hash)
        send_telegram("⚠️ NUOVE PROMO RILEVATE!\n\n" + URL)
        print("CAMBIAMENTO RILEVATO")
    else:
        print("NESSUNA VARIAZIONE")


if __name__ == "__main__":
    main()
