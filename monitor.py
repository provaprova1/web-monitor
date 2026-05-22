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
# ESTRAZIONE STABILE (PLAYWRIGHT SAFE)
# =========================
def extract_content():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )

        page = browser.new_page()

        try:
            page.goto(URL, wait_until="domcontentloaded", timeout=60000)

            # aspetta rendering JS
            page.wait_for_timeout(5000)

            # prova a prendere SOLO contenuto principale
            try:
                el = page.locator("main").first
                content = el.inner_text(timeout=5000)
            except:
                content = page.evaluate("document.body.innerText")

        except Exception as e:
            print("Page error:", e)
            content = ""

        finally:
            browser.close()

        # normalizzazione forte
        content = " ".join(content.lower().split())

        return content


# =========================
# HASH
# =========================
def hash_content(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


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
    content = extract_content()

    if not content:
        print("Empty content extracted")
        return

    new_hash = hash_content(content)
    old_hash = load_state()

    print("HASH NUOVO:", new_hash)
    print("HASH VECCHIO:", old_hash)

    # DEBUG (utile su GitHub Actions)
    print("CONTENT LENGTH:", len(content))

    # PRIMO RUN
    if old_hash is None:
        save_state(new_hash)
        send_telegram("🟢 Monitor avviato (baseline salvata)")
        print("INIT OK")
        return

    # CAMBIAMENTO
    if new_hash != old_hash:
        save_state(new_hash)
        send_telegram("⚠️ NUOVE PROMO RILEVATE\n\n" + URL)
        print("CAMBIAMENTO RILEVATO")
    else:
        print("NESSUNA VARIAZIONE")


if __name__ == "__main__":
    main()