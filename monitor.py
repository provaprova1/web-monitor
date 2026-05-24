import os
import hashlib
import requests
from datetime import datetime
from playwright.sync_api import sync_playwright

URL = "https://eplay24.it/promozioni"

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

STATE_FILE = "state.txt"
STATE_SHA_FILE = "state_sha.txt"


# =========================
# TELEGRAM
# =========================
def send_telegram(msg):
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
# ESTRAZIONE PROMO STABILI
# =========================
def extract_promos():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = browser.new_page()

        page.goto(URL, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(4000)

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


# =========================
# HASH
# =========================
def make_hash(data):
    return hashlib.sha256("\n".join(data).encode()).hexdigest()


# =========================
# STATE PROMO
# =========================
def load_state():
    if not os.path.exists(STATE_FILE):
        return None
    return open(STATE_FILE, "r").read().strip()


def save_state(h):
    with open(STATE_FILE, "w") as f:
        f.write(h)


# =========================
# STATE SHA (RESET LOGICO)
# =========================
def load_sha():
    if not os.path.exists(STATE_SHA_FILE):
        return None
    return open(STATE_SHA_FILE, "r").read().strip()


def save_sha(sha):
    with open(STATE_SHA_FILE, "w") as f:
        f.write(sha)


# =========================
# MAIN
# =========================
def main():
    print("📁 RUN STARTED")
    print("TIME:", datetime.utcnow().isoformat())

    # 🔥 commit SHA corrente (GitHub Actions)
    current_sha = os.environ.get("GITHUB_SHA", "local")

    last_sha = load_sha()

    print("CURRENT SHA:", current_sha)
    print("LAST SHA:", last_sha)

    # =========================
    # RESET SU NUOVO DEPLOY
    # =========================
    if last_sha != current_sha:
        print("🟡 NEW DEPLOY DETECTED → RESET STATE")

        save_sha(current_sha)
        promos = extract_promos()
        save_state(make_hash(promos))

        send_telegram("🟢 Nuova baseline creata (nuovo deploy)")
        print("BASELINE RESET COMPLETED")
        return

    # =========================
    # NORMAL FLOW
    # =========================
    promos = extract_promos()
    new_hash = make_hash(promos)
    old_hash = load_state()

    print("OLD HASH:", old_hash)
    print("NEW HASH:", new_hash)

    if old_hash is None:
        save_state(new_hash)
        send_telegram("🟢 Monitor avviato (baseline iniziale)")
        print("INIT OK")
        return

    if new_hash != old_hash:
        save_state(new_hash)
        send_telegram("⚠️ NUOVE PROMO RILEVATE!\n\n" + URL)
        print("CHANGE DETECTED")
    else:
        print("NO CHANGE")


if __name__ == "__main__":
    main()