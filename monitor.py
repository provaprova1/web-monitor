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
# NORMALIZZAZIONE
# =========================
def clean(text: str) -> str:
    return " ".join(text.lower().split())


# =========================
# STATE
# =========================
def load_state():
    if not os.path.exists(STATE_FILE):
        return set()

    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return set(clean(line) for line in f if line.strip())


def save_state(items):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        for i in sorted(set(clean(x) for x in items)):
            f.write(i + "\n")


# =========================
# ESTRAZIONE ROBUSTA
# =========================
def extract_promos():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = browser.new_page()

        page.goto(URL, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(8000)

        page.mouse.wheel(0, 4000)
        page.wait_for_timeout(4000)

        body_text = page.inner_text("body")
        browser.close()

        items = set()

        keywords = [
            "serie a",
            "premier league",
            "laliga",
            "bundesliga",
            "bonus",
            "promo",
            "freebet",
            "cashback",
            "rimborso"
        ]

        for line in body_text.split("\n"):
            t = clean(line)

            if len(t) < 15:
                continue

            if any(k in t for k in keywords):
                items.add(t)

        return items


# =========================
# HASH STABILE (backup debug)
# =========================
def make_hash(items):
    joined = "\n".join(sorted(items))
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


# =========================
# MAIN
# =========================
def main():
    print("RUN START")

    current = extract_promos()
    previous = load_state()

    new_items = current - previous

    print("CURRENT:", len(current))
    print("PREVIOUS:", len(previous))
    print("NEW ITEMS:", len(new_items))

    # primo run
    if not previous:
        save_state(current)
        send("🟢 Monitor avviato (baseline iniziale)")
        print("BASELINE CREATED")
        return

    # cambi reali
    if new_items:
        save_state(current)

        msg = "⚠️ NUOVE PROMO RILEVATE!\n\n"
        msg += "\n".join(list(new_items)[:10])

        send(msg)
        print("CHANGE DETECTED")
    else:
        print("NO CHANGE")


if __name__ == "__main__":
    main()
