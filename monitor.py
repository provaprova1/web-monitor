import os
import hashlib
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import requests

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
# RENDER PAGINA (PLAYWRIGHT)
# =========================
def get_rendered_html():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(URL, wait_until="networkidle", timeout=60000)

        html = page.content()

        browser.close()
        return html


# =========================
# ESTRAZIONE STABILE
# =========================
def extract_promos(html):
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "noscript", "svg", "footer", "header", "nav"]):
        tag.decompose()

    promos = set()

    # prendiamo SOLO link visibili reali
    for a in soup.find_all("a", href=True):
        text = a.get_text(" ", strip=True)
        href = a["href"]

        if text and len(text) > 5:
            promos.add(text.lower().strip())

        if href:
            promos.add(href.split("?")[0])

    return sorted(promos)


# =========================
# HASH
# =========================
def hash_data(data):
    joined = "||".join(sorted(data))
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


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
    html = get_rendered_html()
    promos = extract_promos(html)

    new_hash = hash_data(promos)
    old_hash = load_state()

    print("PROMO:", len(promos))
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
        print("CAMBIAMENTO REALE")
    else:
        print("NESSUNA VARIAZIONE")


if __name__ == "__main__":
    main()