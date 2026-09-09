# Teams Notifier

Manda un resumen diario (por Telegram) de tu feed de Actividad de Microsoft
Teams — menciones, avisos de canal, tareas nuevas — a una hora fija, usando
GitHub Actions (no depende de que tu laptop o celular esten prendidos).

No usa la API oficial de Microsoft Graph para leer mensajes/tareas porque esos
permisos requieren aprobacion de administrador en la mayoria de instituciones.
En su lugar, automatiza un navegador (Playwright) que revisa Teams como lo
harias tu, usando una sesion que guardas una sola vez.

## 1. Instalar dependencias localmente

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

## 2. Guardar tu sesion de Teams (una sola vez)

```bash
python scripts/login_local.py
```

Se abre un navegador de verdad. Inicia sesion con tu cuenta institucional
normalmente. Cuando ya veas tu Teams cargado, regresa a la terminal y
presiona ENTER. Esto crea `state.json` (NO se sube a git, esta en
`.gitignore`).

## 3. Crear un bot de Telegram para el aviso

1. En Telegram, busca **@BotFather** y mandale `/newbot`.
2. Sigue las instrucciones, te da un **token** (guardalo).
3. Busca tu bot recien creado y mandale cualquier mensaje (ej. "hola").
4. Abre en el navegador:
   `https://api.telegram.org/bot<TU_TOKEN>/getUpdates`
5. Ahi busca `"chat":{"id":NUMERO` — ese numero es tu **chat id**.

## 4. Configurar los secrets del repo en GitHub

En GitHub: Settings > Secrets and variables > Actions > New repository secret.
Crea estos tres:

- `TEAMS_STATE_B64`: el contenido de `state.json` codificado en base64.
  En PowerShell:
  ```powershell
  [Convert]::ToBase64String([IO.File]::ReadAllBytes("state.json")) | Set-Clipboard
  ```
  (queda copiado al portapapeles, pegalo como valor del secret)
- `TELEGRAM_BOT_TOKEN`: el token del paso 3.
- `TELEGRAM_CHAT_ID`: el numero del paso 3.

## 5. Probar

En GitHub, pestaña **Actions** > "Aviso diario de Teams" > **Run workflow**
(boton manual, no hay que esperar al cron). Revisa que te llegue el mensaje
de Telegram.

## 6. Ajustar la hora

El cron en `.github/workflows/notify.yml` esta en **UTC**. Ciudad Madero es
UTC-6 (sin horario de verano), asi que para que corra a las 7:00 AM local,
el cron debe decir `0 13 * * *`. Cambialo si quieres otra hora.

## Nota sobre la sesion

La sesion guardada (`state.json` / el secret `TEAMS_STATE_B64`) expira cada
cierto tiempo (semanas). Cuando el aviso empiece a decir "no se encontro
actividad (o la sesion expiro)", repite los pasos 2 y 4 para renovarla.
