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
# ESTRAI SOLO SEZIONE TARGET
# =========================
def extract_section():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox"]
        )

        page = browser.new_page()
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(5000)

        # 🔥 CERCA BLOCCO PROMO SPORT
        sections = page.query_selector_all("section, main, div")

        target_text = ""

        for sec in sections:
            try:
                txt = sec.inner_text().lower()

                # filtro: deve contenere segnali promo sport
                if (
                    "promozioni sport" in txt
                    or "serie a" in txt
                    or "premier league" in txt
                    or "laliga" in txt
                ):
                    target_text = txt
                    break
            except:
                continue

        browser.close()

        return target_text


# =========================
# NORMALIZZAZIONE STABILE
# =========================
def normalize(text):
    import re

    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\d+", "<num>", text)

    return text.strip()


# =========================
# HASH
# =========================
def make_hash(text):
    return hashlib.sha256(text.encode()).hexdigest()


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
    raw = extract_section()
    content = normalize(raw)

    print("CONTENT SAMPLE:")
    print(content[:500])

    new_hash = make_hash(content)
    old_hash = load_state()

    print("HASH NUOVO:", new_hash)
    print("HASH VECCHIO:", old_hash)

    if not old_hash:
        save_state(new_hash)
        send_telegram("🟢 Monitor avviato (baseline Visual-style)")
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
