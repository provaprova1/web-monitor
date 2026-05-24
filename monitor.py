import os
import hashlib
import requests
from playwright.sync_api import sync_playwright

URL = "https://eplay24.it/promozioni"

STATE_FILE = "state.txt"

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")


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

        # 🔥 FIX CRUCIALE: ASPETTA CONTENUTO REALE
        page.wait_for_timeout(8000)

        page.wait_for_load_state("networkidle")

        html = page.content()

        print("HTML SIZE:", len(html))  # debug

        elements = page.query_selector_all("a, h2, h3, p")

        promos = []

        for el in elements:
            try:
                text = el.inner_text().lower().strip()
                text = " ".join(text.split())

                if len(text) < 10:
                    continue

                if any(k in text for k in ["bonus", "promo", "cashback", "freebet", "rimborso"]):
                    promos.append(text[:140])

            except:
                continue

        browser.close()

        return sorted(set(promos))


def make_hash(data):
    return hashlib.sha256("\n".join(data).encode()).hexdigest()


def load_state():
    if not os.path.exists(STATE_FILE):
        return None
    return open(STATE_FILE, "r").read().strip()


def save_state(h):
    with open(STATE_FILE, "w") as f:
        f.write(h)


def main():
    print("RUN START")

    promos = extract_promos()

    print("PROMOS FOUND:", len(promos))
    for p in promos[:10]:
        print("-", p)

    new_hash = make_hash(promos)
    old_hash = load_state()

    print("OLD HASH:", old_hash)
    print("NEW HASH:", new_hash)

    if old_hash is None:
        save_state(new_hash)
        send_telegram("🟢 Monitor avviato (baseline iniziale)")
        print("BASELINE CREATED")
        return

    if new_hash != old_hash:
        save_state(new_hash)
        send_telegram("⚠️ NUOVE PROMO RILEVATE!\n\n" + URL)
        print("CHANGE DETECTED")
    else:
        print("NO CHANGE")


if __name__ == "__main__":
    main()
