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
# HASH UTILITY
# =========================
def h(txt):
    return hashlib.sha256(txt.encode("utf-8")).hexdigest()


# =========================
# LOAD / SAVE STATE
# =========================
def load_state():
    if not os.path.exists(STATE_FILE):
        return None
    return open(STATE_FILE, "r").read().strip()


def save_state(v):
    with open(STATE_FILE, "w") as f:
        f.write(v)


# =========================
# EXTRACT (ROBUSTO)
# =========================
def extract_content():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox"]
        )

        page = browser.new_page()

        page.goto(URL, wait_until="domcontentloaded", timeout=60000)

        # 🔥 attesa forte per JS
        page.wait_for_timeout(10000)

        # scroll per trigger lazy load
        page.mouse.wheel(0, 3000)
        page.wait_for_timeout(3000)

        html = page.content()

        print("HTML SIZE:", len(html))

        # =========================
        # FALLBACK 1: HTML valido
        # =========================
        if len(html) > 2000:
            text_blocks = page.query_selector_all("a, h2, h3, p, span, div")

            items = []

            for el in text_blocks:
                try:
                    t = el.inner_text().lower().strip()
                    t = " ".join(t.split())

                    if len(t) < 10:
                        continue

                    if any(k in t for k in ["bonus", "promo", "cashback", "freebet", "rimborso"]):
                        items.append(t[:150])

                except:
                    continue

            browser.close()

            return sorted(set(items))

        # =========================
        # FALLBACK 2: HTML BLOCCATO → screenshot hash
        # =========================
        print("⚠️ HTML troppo piccolo → fallback screenshot")

        screenshot = page.screenshot(full_page=True)

        browser.close()

        return [h(screenshot.hex())]


# =========================
# MAIN
# =========================
def main():
    print("RUN START")

    data = extract_content()
    new_hash = h("\n".join(data))

    old_hash = load_state()

    print("ITEMS:", len(data))
    print("OLD:", old_hash)
    print("NEW:", new_hash)

    # 🟢 primo run
    if old_hash is None:
        save_state(new_hash)
        send("🟢 Monitor avviato (baseline iniziale)")
        print("BASELINE CREATED")
        return

    # ⚠️ cambio
    if new_hash != old_hash:
        save_state(new_hash)
        send("⚠️ NUOVE PROMO RILEVATE!\n\n" + URL)
        print("CHANGE DETECTED")
    else:
        print("NO CHANGE")


if __name__ == "__main__":
    main()
