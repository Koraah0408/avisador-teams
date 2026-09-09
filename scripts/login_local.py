"""
Corre esto cuando necesites (re)generar tu sesion de Teams: la primera
vez, y despues cada vez que el aviso diario diga que la sesion expiro.

No automatiza ningun login (Microsoft lo detecta y lo bloquea). En vez
de eso, copia tu perfil real de Brave -donde ya iniciaste sesion tu
mismo- a una carpeta temporal, y abre ESA copia para capturar la
sesion ya autenticada. Al final recorta el resultado (quita cache de
UI que no sirve para nada) para que quepa en los secrets de GitHub.

Requisito: cierra Brave por completo antes de correr esto.

Uso:
    python scripts/login_local.py
    python scripts/upload_session.py   (para subirla a GitHub despues)
"""

import json
import os
import shutil
import tempfile

from playwright.sync_api import sync_playwright

STATE_PATH = "state.json"
TEAMS_URL = "https://teams.cloud.microsoft/"

BRAVE_USER_DATA = os.path.expandvars(
    r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\User Data"
)
BRAVE_EXE = os.path.expandvars(
    r"%PROGRAMFILES%\BraveSoftware\Brave-Browser\Application\brave.exe"
)
PROFILE_NAME = "Default"  # cambia esto si usas otro perfil de Brave

IGNORE_DIRS = {"Cache", "Code Cache", "GPUCache", "GrShaderCache", "ShaderCache"}


def ignore_heavy_dirs(dir_path, names):
    return [n for n in names if n in IGNORE_DIRS]


def trim_state(raw_state: dict) -> dict:
    """Se queda solo con las cookies y las entradas de localStorage
    relacionadas a la sesion (msal), tirando cache de UI que puede
    pesar cientos de KB y no sirve para re-autenticar."""
    origins = []
    for origin in raw_state.get("origins", []):
        ls = [e for e in origin.get("localStorage", []) if "msal" in e["name"].lower()]
        if ls:
            origins.append({"origin": origin["origin"], "localStorage": ls})
    return {"cookies": raw_state.get("cookies", []), "origins": origins}


def main():
    if not os.path.exists(BRAVE_USER_DATA):
        print(f"No encontre el perfil de Brave en: {BRAVE_USER_DATA}")
        return
    if not os.path.exists(BRAVE_EXE):
        print(f"No encontre Brave en: {BRAVE_EXE}")
        return

    input("Cierra Brave por completo (todas las ventanas) y presiona ENTER...")

    tmp_dir = tempfile.mkdtemp(prefix="brave_profile_copy_")
    print("Copiando tu perfil de Brave (puede tardar un poco)...")

    shutil.copy2(
        os.path.join(BRAVE_USER_DATA, "Local State"),
        os.path.join(tmp_dir, "Local State"),
    )
    shutil.copytree(
        os.path.join(BRAVE_USER_DATA, PROFILE_NAME),
        os.path.join(tmp_dir, PROFILE_NAME),
        ignore=ignore_heavy_dirs,
    )

    print("Copia lista. Abriendo Brave con la sesion copiada...")

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=tmp_dir,
            executable_path=BRAVE_EXE,
            headless=False,
            args=[f"--profile-directory={PROFILE_NAME}"],
        )
        page = context.pages[0] if context.pages else context.new_page()
        page.goto(TEAMS_URL)

        print("Deberia cargar tu Teams YA autenticado, sin pedirte login.")
        input("Cuando lo veas cargado, presiona ENTER para guardar la sesion...")

        raw_state = context.storage_state()
        context.close()

    shutil.rmtree(tmp_dir, ignore_errors=True)

    trimmed = trim_state(raw_state)
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(trimmed, f)

    size_kb = os.path.getsize(STATE_PATH) / 1024
    print(f"Sesion guardada en {STATE_PATH} ({size_kb:.0f} KB)")
    print("Ahora corre: python scripts/upload_session.py")


if __name__ == "__main__":
    main()
