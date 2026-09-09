"""
Corre esto UNA VEZ en tu propia PC para guardar tu sesión de Teams.
No sube ni comparte tu contraseña: abre un navegador de verdad para
que inicies sesion tu mismo, y solo guarda las cookies/sesion resultante.

Uso:
    python scripts/login_local.py
"""

from playwright.sync_api import sync_playwright

STATE_PATH = "state.json"
TEAMS_URL = "https://teams.microsoft.com/v2/"


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto(TEAMS_URL)

        print("Inicia sesion con tu cuenta institucional en la ventana que se abrio.")
        print("Cuando ya veas tu lista de equipos/chats de Teams cargada, regresa aqui")
        input("y presiona ENTER para guardar la sesion...")

        context.storage_state(path=STATE_PATH)
        print(f"Sesion guardada en {STATE_PATH}")

        browser.close()


if __name__ == "__main__":
    main()
