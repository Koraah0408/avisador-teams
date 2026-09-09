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

## Renovar la sesion cuando expire

Cada cierto tiempo (semanas) la sesion expira y el aviso dira "no se
encontro actividad (o la sesion expiro)". Repite los pasos 2 y 4:

```bash
python scripts/login_local.py
python scripts/upload_session.py
```
