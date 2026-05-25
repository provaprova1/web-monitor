import os
import requests
from playwright.sync_api import sync_playwright
from PIL import Image, ImageChops

URL = "https://eplay24.it/promozioni"

BASELINE = "baseline.png"
CURRENT = "current.png"

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")


# =========================
# TELEGRAM
# =========================
def send(msg):
    if not BOT_TOKEN or not CHAT_ID:
        print("Telegram config missing")
        return

    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": msg},
        timeout=10
    )


# =========================
# SCREENSHOT
# =========================
def capture(path):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = browser.new_page(viewport={"width": 1400, "height": 2500})

        page.goto(URL, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(12000)

        page.mouse.wheel(0, 2500)
        page.wait_for_timeout(3000)

        page.screenshot(
            path=path,
            clip={"x": 0, "y": 500, "width": 1400, "height": 900}
        )

        browser.close()


# =========================
# DIFF
# =========================
def diff(img1, img2):
    im1 = Image.open(img1)
    im2 = Image.open(img2)

    d = ImageChops.difference(im1, im2)
    return sum(d.histogram())


# =========================
# MAIN LOGIC CORRETTA
# =========================
def main():
    print("RUN START")

    # =========================
    # 🟢 FIRST RUN (BASELINE ONLY)
    # =========================
    if not os.path.exists(BASELINE):
        print("NO BASELINE FOUND → CREATING IT")

        capture(BASELINE)

        send("🟢 Baseline creata (primo run)")

        print("BASELINE CREATED - EXIT")
        return  # 🔥 STOP QUI (FONDAMENTALE)

    # =========================
    # 🟡 NORMAL RUN
    # =========================
    capture(CURRENT)

    score = diff(BASELINE, CURRENT)

    print("DIFF SCORE:", score)

    THRESHOLD = 50000  # soglia anti-falsi positivi

    if score > THRESHOLD:
        print("CHANGE DETECTED")

        # aggiorna baseline SOLO se cambia davvero
        os.replace(CURRENT, BASELINE)

        send("⚠️ CAMBIAMENTO VISIVO RILEVATO NELLE PROMO SPORT!")

    else:
        print("NO CHANGE")
        os.remove(CURRENT)


if __name__ == "__main__":
    main()
