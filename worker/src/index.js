// Worker de Cloudflare: responde al instante cuando le escribes al bot
// de Telegram, usando Gemini con el ultimo snapshot de actividad de
// Teams (el que genera check_teams.py y sube a data/latest_activity.json
// en el repo de GitHub) como contexto.

const GEMINI_MODEL = "gemini-2.5-flash";
const ACTIVITY_URL =
  "https://raw.githubusercontent.com/Koraah0408/avisador-teams/master/data/latest_activity.json";

export default {
  async fetch(request, env) {
    if (request.method !== "POST") {
      return new Response("ok");
    }

    const secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token");
    if (secret !== env.WEBHOOK_SECRET) {
      return new Response("forbidden", { status: 403 });
    }

    let update;
    try {
      update = await request.json();
    } catch {
      return new Response("ok");
    }

    const message = update.message;
    if (!message || !message.text) {
      return new Response("ok");
    }
    if (String(message.chat.id) !== String(env.TELEGRAM_CHAT_ID)) {
      return new Response("ok"); // ignora mensajes que no sean tuyos
    }

    const context = await loadActivityContext();
    let answer;
    try {
      answer = await askGemini(env, message.text, context);
    } catch (e) {
      answer = `Hubo un error consultando la IA: ${e}`;
    }
    await sendTelegram(env, answer);

    return new Response("ok");
  },
};

async function loadActivityContext() {
  try {
    const resp = await fetch(ACTIVITY_URL, { cf: { cacheTtl: 0 } });
    if (!resp.ok) return "(todavia no hay informacion de Teams guardada)";
    const items = await resp.json();
    return items.map((i) => `- ${i}`).join("\n");
  } catch {
    return "(todavia no hay informacion de Teams guardada)";
  }
}

function hoyEnMexico() {
  // UTC-6 fijo (Ciudad Madero, sin horario de verano)
  const now = new Date(Date.now() - 6 * 60 * 60 * 1000);
  return now.toISOString().slice(0, 10);
}

async function askGemini(env, question, context) {
  const hoy = hoyEnMexico();
  const prompt = `Eres un asistente que ayuda a un estudiante con dudas sobre sus tareas y avisos de clase en Microsoft Teams. Responde en espanol, corto y directo, basandote SOLO en esta informacion (puede tener hasta un dia de antiguedad).

Hoy es ${hoy}. Si te preguntan por tareas PENDIENTES, incluye solo las que vencen hoy o en el futuro segun esta fecha -- una tarea cuya fecha de vencimiento ya paso se asume entregada y NO se debe mencionar como pendiente (a menos que el estudiante pida el historial completo o pregunte especificamente por tareas viejas).

La lista de actividad esta ordenada de mas reciente a mas antigua y puede mencionar la MISMA tarea varias veces (por ejemplo primero "agrego" y despues "actualizo" la misma tarea porque el profesor le cambio la fecha). Si el nombre de la materia y el nombre de la tarea coinciden, cuentala como una sola tarea y usa el dato mas reciente (la primera mencion que aparece en la lista) -- nunca la repitas ni la cuentes dos veces.

Formato de la respuesta: texto plano, SIN markdown (nada de asteriscos, guiones bajos ni almohadillas). Si listas varias tareas, pon cada una en su propia linea empezando con '- ', incluyendo materia y fecha de vencimiento.

${context}

Pregunta del estudiante: ${question}`;

  const url = `https://generativelanguage.googleapis.com/v1beta/models/${GEMINI_MODEL}:generateContent?key=${env.GEMINI_API_KEY}`;
  const resp = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ contents: [{ parts: [{ text: prompt }] }] }),
  });
  if (!resp.ok) {
    const errText = await resp.text();
    throw new Error(`${resp.status} ${errText}`);
  }
  const data = await resp.json();
  return data.candidates[0].content.parts[0].text;
}

async function sendTelegram(env, text) {
  const url = `https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/sendMessage`;
  await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ chat_id: env.TELEGRAM_CHAT_ID, text }),
  });
}
