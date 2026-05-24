import os
import hashlib
import requests
from playwright.sync_api import sync_playwright

URL = "https://eplay24.it/promozioni"

STATE_FILE = "state.txt"


def send(msg):
    print("SEND:", msg)


def extract():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(URL, wait_until="networkidle")
        page.wait_for_timeout(3000)
        text = page.inner_text("body")
        browser.close()
        return " ".join(text.lower().split())


def h(x):
    return hashlib.sha256(x.encode()).hexdigest()


def load():
    print("🔍 ABS PATH:", os.path.abspath(STATE_FILE))
    print("🔍 EXISTS:", os.path.exists(STATE_FILE))

    if not os.path.exists(STATE_FILE):
        return None

    with open(STATE_FILE, "r") as f:
        val = f.read()
        print("📄 RAW STATE CONTENT:", repr(val))
        return val.strip()


def save(v):
    with open(STATE_FILE, "w") as f:
        f.write(v)


def main():
    content = extract()
    new = h(content)
    old = load()

    print("NEW HASH:", new)
    print("OLD HASH:", old)

    # 🔥 DEBUG CHIARO
    if old is None or old == "":
        save(new)
        send("🟢 BASELINE CREATA")
        print("INIT OK")
        return

    if new != old:
        save(new)
        send("⚠️ CAMBIAMENTO RILEVATO")
    else:
        print("NO CHANGE")


if __name__ == "__main__":
    main()