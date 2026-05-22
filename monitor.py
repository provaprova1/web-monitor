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
        print("Missing secrets")
        return

    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": msg}
    )


# =========================
# ESTRAZIONE STABILE (DOM TARGET)
# =========================
def extract_content():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(URL, wait_until="networkidle", timeout=60000)

        page.wait_for_timeout(3000)

        # 🔥 prova a isolare la sezione visibile
        selectors = [
            "text=Promozioni Sport",
            "h1:has-text('Promozioni')",
            "section",
            "main"
        ]

        content = ""

        for sel in selectors:
            try:
                el = page.locator(sel).first
                txt = el.inner_text(timeout=2000)

                if txt and len(txt) > 100:
                    content = txt
                    break
            except:
                continue

        browser.close()

        # fallback totale
        if not content:
            content = page.content()

        # normalizzazione forte
        content = " ".join(content.lower().split())

        return content


# =========================
# HASH
# =========================
def hash_data(data):
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


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
    content = extract_content()

    new_hash = hash_data(content)
    old_hash = load_state()

    print("HASH NUOVO:", new_hash)
    print("HASH VECCHIO:", old_hash)

    # 🔥 DEBUG FONDAMENTALE
    print("LUNGHEZZA CONTENUTO:", len(content))
    print(content[:300])

    if old_hash is None:
        save_state(new_hash)
        send_telegram("🟢 Monitor avviato (baseline stabile)")
        print("INIT OK")
        return

    if new_hash != old_hash:
        save_state(new_hash)
        send_telegram("⚠️ NUOVE PROMO RILEVATE\n\n" + URL)
        print("CAMBIAMENTO REALE")
    else:
        print("NESSUNA VARIAZIONE")


if __name__ == "__main__":
    main()