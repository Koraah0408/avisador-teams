"""
Revisa si te escribieron algo nuevo al bot de Telegram y responde usando
Gemini, con tus tareas/avisos de Teams mas recientes como contexto.

Pensado para correr cada varios minutos desde GitHub Actions (no es
instantaneo, pero no requiere servidor propio).
"""

import json
import os

import requests

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

STATE_PATH = "data/bot_state.json"
ACTIVITY_PATH = "data/latest_activity.json"
GEMINI_MODEL = "gemini-2.5-flash"

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


def load_state() -> dict:
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {"last_update_id": 0}


def save_state(state: dict):
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f)


def load_activity_context() -> str:
    if os.path.exists(ACTIVITY_PATH):
        with open(ACTIVITY_PATH, encoding="utf-8") as f:
            items = json.load(f)
        return "\n".join(f"- {item}" for item in items)
    return "(todavia no hay informacion de Teams guardada)"


def ask_gemini(question: str, context: str) -> str:
    prompt = (
        "Eres un asistente que ayuda a un estudiante con dudas sobre sus "
        "tareas y avisos de clase en Microsoft Teams. Responde en espanol, "
        "corto y directo, basandote SOLO en esta informacion (puede tener "
        "hasta un dia de antiguedad).\n\n"
        "Formato de la respuesta: texto plano, SIN markdown (nada de "
        "asteriscos, guiones bajos ni almohadillas). Si listas varias "
        "tareas, pon cada una en su propia linea empezando con '- ', "
        "incluyendo materia y fecha de vencimiento.\n\n"
        f"{context}\n\n"
        f"Pregunta del estudiante: {question}"
    )
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    )
    resp = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]})
    resp.raise_for_status()
    data = resp.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]


def send_telegram(text: str):
    resp = requests.post(
        f"{TELEGRAM_API}/sendMessage",
        data={"chat_id": TELEGRAM_CHAT_ID, "text": text},
    )
    resp.raise_for_status()


def main():
    state = load_state()

    resp = requests.get(
        f"{TELEGRAM_API}/getUpdates",
        params={"offset": state["last_update_id"] + 1, "timeout": 0},
    )
    resp.raise_for_status()
    updates = resp.json().get("result", [])

    if not updates:
        print("Sin mensajes nuevos.")
        return

    context = load_activity_context()

    for update in updates:
        state["last_update_id"] = update["update_id"]
        message = update.get("message")
        if not message or "text" not in message:
            continue
        if str(message["chat"]["id"]) != str(TELEGRAM_CHAT_ID):
            continue  # ignora mensajes que no sean tuyos

        question = message["text"]
        print("Pregunta recibida, generando respuesta...")
        try:
            answer = ask_gemini(question, context)
        except Exception as e:
            answer = f"Hubo un error consultando la IA: {e}"
        send_telegram(answer)

    save_state(state)


if __name__ == "__main__":
    main()
