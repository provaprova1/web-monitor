import os
import re
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
        print("Missing BOT_TOKEN or CHAT_ID")
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
# ESTRAZIONE PAGINA
# =========================
def get_page_text():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )

        page = browser.new_page()

        try:
            page.goto(URL, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(5000)

            text = page.evaluate("document.body.innerText")

        except Exception as e:
            print("Page error:", e)
            text = ""

        finally:
            browser.close()

        return text


# =========================
# ESTRAZIONE PROMO STABILI
# =========================
def extract_promos(text):
    lines = text.splitlines()
    promos = []

    keywords = [
        "bonus", "promo", "freebet",
        "cashback", "rimborso",
        "scomm", "quote", "€", "%"
    ]

    for line in lines:
        line = line.lower().strip()

        # pulizia base
        line = re.sub(r"\s+", " ", line)
        line = re.sub(r"\d+", "<num>", line)

        if len(line) < 20:
            continue

        if len(line) > 180:
            continue

        if any(k in line for k in keywords):
            promos.append(line)

    # stabilizzazione totale
    promos = sorted(set(promos))

    return promos


# =========================
# HASH STABILE
# =========================
def make_hash(promos):
    return hashlib.sha256("\n".join(promos).encode("utf-8")).hexdigest()


# =========================
# STATE
# =========================
def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return f.read().strip()
    return None


def save_state(h):
    with open(STATE_FILE, "w") as f:
        f.write(h)


# =========================
# MAIN
# =========================
def main():
    text = get_page_text()

    if not text:
        print("EMPTY PAGE")
        return

    promos = extract_promos(text)

    print("\nPROMO RILEVATE:")
    for p in promos[:20]:
        print("-", p)

    new_hash = make_hash(promos)
    old_hash = load_state()

    print("\nHASH NUOVO:", new_hash)
    print("HASH VECCHIO:", old_hash)

    # PRIMO RUN
    if old_hash is None:
        save_state(new_hash)
        send_telegram("🟢 Monitor avviato (baseline salvata)")
        print("INIT OK")
        return

    # CAMBIAMENTO
    if new_hash != old_hash:
        save_state(new_hash)
        send_telegram("⚠️ NUOVE PROMO RILEVATE!\n\n" + URL)
        print("CAMBIAMENTO RILEVATO")
    else:
        print("NESSUNA VARIAZIONE")


if __name__ == "__main__":
    main()
