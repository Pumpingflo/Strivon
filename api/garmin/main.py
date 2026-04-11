"""
Strivon Garmin Sync API — FastAPI
==================================
POST /sync  (Authorization: Bearer <Supabase access_token>)

Env:
  SUPABASE_JWT_SECRET  — Project Settings → API → JWT Secret (nicht anon key!)
  ALLOWED_ORIGINS      — Komma-getrennte Origins für CORS, z.B.
                         https://dein-org.github.io,http://localhost:8080
                         Leer = * (nur für lokale Tests)
"""
from __future__ import annotations

import logging
import os
from typing import Any

import jwt
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from garmin_engine import sync_workouts_to_garmin

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("strivon-api")

app = FastAPI(title="Strivon Garmin Sync", version="1.0.0")


def _cors_origins() -> list[str]:
    raw = (os.environ.get("ALLOWED_ORIGINS") or "").strip()
    if not raw:
        return ["*"]
    return [o.strip() for o in raw.split(",") if o.strip()]


app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


class SyncBody(BaseModel):
    garmin_email: str = Field(..., min_length=3)
    garmin_password: str = Field(..., min_length=1)
    workouts: list[dict[str, Any]] = Field(default_factory=list)


def verify_supabase_jwt(token: str) -> dict:
    secret = os.environ.get("SUPABASE_JWT_SECRET", "").strip()
    if not secret:
        log.error("SUPABASE_JWT_SECRET is not set")
        raise HTTPException(500, "Server misconfigured: missing SUPABASE_JWT_SECRET")
    try:
        return jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(401, "Sitzung abgelaufen — bitte neu anmelden.") from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(401, "Ungültiges Login-Token.") from exc


@app.get("/health")
def health():
    return {"status": "ok", "service": "strivon-garmin-sync"}


@app.post("/sync")
def sync(
    body: SyncBody,
    authorization: str | None = Header(None),
):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "Authorization: Bearer <Supabase access_token> fehlt")

    token = authorization[7:].strip()
    claims = verify_supabase_jwt(token)
    user_id = claims.get("sub")
    log.info("Sync request for user %s | %d workouts", user_id, len(body.workouts))

    if not body.workouts:
        raise HTTPException(422, "workouts-Liste ist leer")

    try:
        result = sync_workouts_to_garmin(body.workouts, body.garmin_email, body.garmin_password)
    except RuntimeError as exc:
        raise HTTPException(401, str(exc)) from exc
    except Exception as exc:
        log.exception("Sync failed")
        raise HTTPException(500, f"Garmin-Sync fehlgeschlagen: {exc}") from exc

    code = 200 if result.get("ok") else 207
    return JSONResponse(content=result, status_code=code)
