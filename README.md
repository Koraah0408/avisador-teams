# Teams Notifier

Manda un resumen diario (por Telegram) de tu feed de Actividad de Microsoft
Teams — tareas nuevas, avisos de canal, menciones — a una hora fija, usando
GitHub Actions (no depende de que tu laptop o celular esten prendidos).

No usa la API oficial de Microsoft Graph para leer tareas/mensajes porque
esos permisos requieren aprobacion de administrador en la mayoria de
instituciones. Tampoco automatiza el login interactivo (Microsoft lo
detecta y lo bloquea). En su lugar, reutiliza una sesion capturada de tu
navegador (Brave) ya autenticado, y automatiza solo la lectura del feed.

## 1. Instalar dependencias localmente

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

## 2. Generar tu sesion de Teams

Cierra Brave por completo, y con tu sesion de Teams ya iniciada ahi
normalmente, corre:

```bash
python scripts/login_local.py
```

Copia tu perfil de Brave a una carpeta temporal, abre esa copia (sin tocar
tu Brave real) y captura la sesion ya autenticada en `state.json` (recortada
para pesar lo mínimo — no se sube a git, esta en `.gitignore`).

## 3. Crear un bot de Telegram para el aviso

1. En Telegram, busca **@BotFather** y mandale `/newbot`.
2. Sigue las instrucciones, te da un **token** (guardalo).
3. Busca tu bot recien creado y mandale cualquier mensaje (ej. "hola").
4. Abre en el navegador:
   `https://api.telegram.org/bot<TU_TOKEN>/getUpdates`
5. Ahi busca `"chat":{"id":NUMERO` — ese numero es tu **chat id**.

## 4. Configurar los secrets del repo en GitHub

Sube la sesion automaticamente (la parte en varios secrets porque uno solo
no puede pesar mas de 48KB):

```bash
python scripts/upload_session.py
```

Los otros dos, con `gh` o desde Settings > Secrets and variables > Actions:

```bash
gh secret set TELEGRAM_BOT_TOKEN --repo Koraah0408/avisador-teams
gh secret set TELEGRAM_CHAT_ID --repo Koraah0408/avisador-teams
```

## 5. Probar

En GitHub, pestaña **Actions** > "Aviso diario de Teams" > **Run workflow**
(boton manual, no hay que esperar al cron). Revisa que te llegue el mensaje
de Telegram.

## 6. Ajustar la hora

El cron en `.github/workflows/notify.yml` esta en **UTC**. Ciudad Madero es
UTC-6 (sin horario de verano), asi que para que corra a las 7:00 AM local,
el cron debe decir `0 13 * * *`. Cambialo si quieres otra hora.

## 7. Bot de preguntas (respuesta instantanea via Cloudflare Worker)

Puedes escribirle al bot de Telegram preguntas como "¿que tareas tengo esta
semana?" y responde al instante usando Gemini, basandose en el ultimo
snapshot guardado (`data/latest_activity.json`, publico en el repo).

El codigo esta en `worker/`. Se despliega asi:

```bash
cd worker
npx wrangler login
npx wrangler deploy
npx wrangler secret put TELEGRAM_BOT_TOKEN
npx wrangler secret put TELEGRAM_CHAT_ID
npx wrangler secret put GEMINI_API_KEY
npx wrangler secret put WEBHOOK_SECRET   # cualquier cadena aleatoria larga
```

Y despues se le dice a Telegram que mande los mensajes a ese Worker
(cambia `<URL>` por la que te dio `wrangler deploy`, y `<SECRET>` por el
mismo valor que pusiste en `WEBHOOK_SECRET`):

```bash
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
  -d "url=<URL>" -d "secret_token=<SECRET>"
```

Nota: el `scripts/answer_bot.py` + workflow `answer_bot.yml` (polling cada
10 min) fue el prototipo inicial. Con el Worker activo ya no corre por cron
(Telegram no deja usar `getUpdates` y webhook a la vez) — se dejo el
workflow con `workflow_dispatch` por si algun dia se quita el webhook y se
quiere volver a ese modo.

## Renovar la sesion cuando expire

Cada cierto tiempo (semanas) la sesion expira y el aviso dira "no se
encontro actividad (o la sesion expiro)". Repite los pasos 2 y 4:

```bash
python scripts/login_local.py
python scripts/upload_session.py
```
