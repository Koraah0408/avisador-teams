"""
Revisa el feed de Actividad de Teams (menciones, tareas nuevas, avisos de
canal) usando una sesion guardada previamente, y manda un resumen por
Telegram. Pensado para correr diario desde GitHub Actions.
"""

import os
import sys

import requests
from playwright.sync_api import sync_playwright

STATE_PATH = os.environ.get("STATE_PATH", "state.json")
TEAMS_ACTIVITY_URL = "https://teams.microsoft.com/v2/#/activity/"
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
MAX_ITEMS = 20


def get_activity_items(page) -> list[str]:
    page.goto(TEAMS_ACTIVITY_URL)
    page.wait_for_timeout(8000)

    items = page.locator("[data-tid='activity-item'], [role='listitem']")
    count = min(items.count(), MAX_ITEMS)

    texts = []
    for i in range(count):
        text = items.nth(i).inner_text().strip()
        if text:
            texts.append(text.replace("\n", " | "))
    return texts


def send_telegram(message: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Falta TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID, no se envio nada.")
        print(message)
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    # Telegram limita ~4096 caracteres por mensaje
    for chunk_start in range(0, len(message), 4000):
        chunk = message[chunk_start:chunk_start + 4000]
        resp = requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": chunk})
        resp.raise_for_status()


def main():
    if not os.path.exists(STATE_PATH):
        print(f"No existe {STATE_PATH}. Corre primero scripts/login_local.py")
        sys.exit(1)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state=STATE_PATH)
        page = context.new_page()

        items = get_activity_items(page)
        browser.close()

    if items:
        body = "\n\n".join(f"- {item}" for item in items)
        message = f"Resumen de Teams de hoy:\n\n{body}"
    else:
        message = "Resumen de Teams de hoy: no se encontro actividad nueva (o la sesion expiro)."

    send_telegram(message)


if __name__ == "__main__":
    main()
