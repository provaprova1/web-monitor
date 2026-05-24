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
        return set()

    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())


def save_state(items):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        for i in sorted(items):
            f.write(i + "\n")


# =========================
# NORMALIZZAZIONE
# =========================
def clean(t):
    return " ".join(t.lower().split())


# =========================
# ESTRAZIONE ROBUSTA (NO DOM FRAGILE)
# =========================
def extract_promos():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = browser.new_page()

        page.goto(URL, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(8000)

        # scroll per caricare contenuti dinamici
        page.mouse.wheel(0, 4000)
        page.wait_for_timeout(4000)

        # prendi testo visibile globale
        body_text = page.inner_text("body").lower()

        browser.close()

        items = set()

        for line in body_text.split("\n"):
            t = clean(line)

            if len(t) < 15:
                continue

            # filtri "sport promo reali"
            if any(k in t for k in [
                "serie a",
                "premier league",
                "laliga",
                "bundesliga",
                "bonus",
                "promo",
                "freebet",
                "cashback",
                "rimborso"
            ]):
                items.add(t)

        return items


# =========================
# HASH STABILE
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
    removed_items = previous - current

    print("CURRENT:", len(current))
    print("PREVIOUS:", len(previous))
    print("NEW ITEMS:", len(new_items))

    # primo run
    if not previous:
        save_state(current)
        send("🟢 Monitor avviato (baseline iniziale)")
        print("BASELINE CREATED")
        return

    # cambiamenti veri
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
