import os
import hashlib
import requests
from playwright.sync_api import sync_playwright

URL = "https://eplay24.it/promozioni"

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

STATE_FILE = "state.txt"


def send_telegram(msg):
    if not BOT_TOKEN or not CHAT_ID:
        print("Missing Telegram config")
        return

    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": msg},
        timeout=10
    )


def extract_promos():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = browser.new_page()

        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(5000)

        elements = page.query_selector_all("a, h1, h2, h3, p")

        promos = []

        for el in elements:
            try:
                text = el.inner_text().lower().strip()

                # normalizzazione forte
                text = " ".join(text.split())

                # filtra solo blocchi realmente “promo-like”
                if any(k in text for k in ["bonus", "promo", "cashback", "freebet", "rimborso"]):

                    # elimina variabili tipiche
                    cleaned = "".join([c for c in text if not c.isdigit()])

                    promos.append(cleaned[:150])

            except:
                continue

        browser.close()

        return sorted(set(promos))


def make_hash(data):
    return hashlib.sha256("\n".join(data).encode()).hexdigest()


def load_state():
    if os.path.exists(STATE_FILE):
        return open(STATE_FILE).read().strip()
    return None


def save_state(h):
    with open(STATE_FILE, "w") as f:
        f.write(h)


def main():
    promos = extract_promos()

    print("PROMO:", len(promos))

    new_hash = make_hash(promos)
    old_hash = load_state()

    print("HASH NUOVO:", new_hash)
    print("HASH VECCHIO:", old_hash)

    if old_hash is None:
        save_state(new_hash)
        send_telegram("🟢 Monitor avviato (baseline salvata)")
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
