import os
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

    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": msg},
        timeout=10
    )


# =========================
# STATE (SET DI PROMO)
# =========================
def load_state():
    if not os.path.exists(STATE_FILE):
        return set()
    return set(open(STATE_FILE, "r", encoding="utf-8").read().splitlines())


def save_state(items):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(items)))


# =========================
# NORMALIZZAZIONE TESTO
# =========================
def clean(text):
    return " ".join(text.lower().split())


# =========================
# ESTRAZIONE PRO (SOLO SEZIONE GIUSTA)
# =========================
def extract_promos():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = browser.new_page()

        page.goto(URL, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(8000)

        # scroll per lazy load
        page.mouse.wheel(0, 3000)
        page.wait_for_timeout(3000)

        section = page.query_selector("text=Promozioni Sport")

        if not section:
            browser.close()
            return set()

        container = section.evaluate("""
            el => el.parentElement ? el.parentElement.innerText : el.innerText
        """)

        browser.close()

        lines = set()

        for line in container.split("\n"):
            t = clean(line)

            if len(t) < 15:
                continue

            # filtra roba utile
            if any(k in t for k in ["bonus", "promo", "cashback", "freebet", "rimborso"]):
                lines.add(t)

        return lines


# =========================
# MAIN (DIFF INTELLIGENTE)
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

    # cambiamenti reali
    if new_items:
        save_state(current)

        msg = "⚠️ NUOVE PROMO RILEVATE:\n\n" + "\n".join(list(new_items)[:10])
        send(msg)

        print("NEW PROMOS DETECTED")
    else:
        print("NO CHANGE")


if __name__ == "__main__":
    main()
