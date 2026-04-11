# Strivon Garmin Sync API

Kleiner **FastAPI**-Dienst: nimmt Workouts + Garmin-Login entgegen (nur bei authentifizierten Supabase-Nutzern), lädt Einheiten in **Garmin Connect**.

## Render (kostenloser Einstieg)

1. Neues **Web Service** auf [render.com](https://render.com) → *Build and deploy from a Git repo* oder *Docker*.
2. **Root Directory** / Build: auf den Ordner `api/garmin` zeigen (oder Repo-Root mit Dockerfile-Pfad anpassen).
3. **Umgebungsvariablen**:
   - `SUPABASE_JWT_SECRET` — Supabase → *Project Settings* → *API* → **JWT Secret** (nicht der `anon` Key).
   - `ALLOWED_ORIGINS` — z. B. `https://DEIN-ORG.github.io,https://strivon.example.com` (CORS). Ohne Eintrag: `*` (nur zum Testen).
4. **Port** (Render): intern `8080` (wie im Dockerfile).

Healthcheck: `GET https://DEIN-Dienst.onrender.com/health`

## Strivon PWA

In `index.html` optional `GARMIN_API_BASE_DEFAULT` setzen, damit Nutzer die URL nicht tippen müssen.

Nutzer tragen **Sync-API-URL**, Garmin-E-Mail und -Passwort in der App ein (localStorage).

## Sicherheit

- Garmin-Passwort liegt **nicht** auf dem Server nach dem Request (nur im RAM während des Syncs).
- Zugriff nur mit gültigem **Supabase Access Token**.
- Für produktive Nutzung: Garmin-Zugangsdaten lieber **verschlüsselt in Supabase** speichern und nicht im localStorage — hier bewusst einfach für nicht-kommerziellen Gebrauch.
