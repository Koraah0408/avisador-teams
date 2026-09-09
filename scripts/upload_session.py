"""
Sube state.json (ya generado por login_local.py) como secrets del repo
de GitHub, partido en pedazos porque un secret individual no puede
pesar mas de 48KB. Requiere tener `gh` instalado y logueado.

Uso:
    python scripts/upload_session.py
"""

import base64
import subprocess
import sys

STATE_PATH = "state.json"
REPO = "Koraah0408/avisador-teams"
CHUNK_SIZE = 40000  # bytes de texto base64 por secret, con margen bajo 48KB
MAX_CHUNKS = 8  # tope razonable; borra los que sobren de corridas previas


def gh_secret_set(name: str, value: str):
    subprocess.run(
        ["gh", "secret", "set", name, "--repo", REPO],
        input=value,
        text=True,
        check=True,
    )


def gh_secret_delete(name: str):
    subprocess.run(
        ["gh", "secret", "delete", name, "--repo", REPO],
        check=False,  # puede no existir, no pasa nada
        capture_output=True,
    )


def main():
    try:
        with open(STATE_PATH, "rb") as f:
            raw = f.read()
    except FileNotFoundError:
        print(f"No existe {STATE_PATH}. Corre primero: python scripts/login_local.py")
        sys.exit(1)

    encoded = base64.b64encode(raw).decode("ascii")
    chunks = [encoded[i:i + CHUNK_SIZE] for i in range(0, len(encoded), CHUNK_SIZE)]

    if len(chunks) > MAX_CHUNKS:
        print(f"La sesion es demasiado grande ({len(chunks)} pedazos, maximo {MAX_CHUNKS}).")
        sys.exit(1)

    print(f"Subiendo sesion en {len(chunks)} pedazo(s)...")
    for i, chunk in enumerate(chunks):
        name = f"TEAMS_STATE_B64_{i}"
        gh_secret_set(name, chunk)
        print(f"  {name} listo")

    for i in range(len(chunks), MAX_CHUNKS):
        gh_secret_delete(f"TEAMS_STATE_B64_{i}")

    print("Listo. La sesion ya esta actualizada en GitHub.")


if __name__ == "__main__":
    main()
