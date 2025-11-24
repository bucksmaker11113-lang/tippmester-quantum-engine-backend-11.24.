# backend/main.py
# Javított, optimalizált FastAPI főfájl Hetzner + Frontend integrációhoz
# - CORS engedélyezés
# - ENV alapú konfiguráció
# - API prefix egységesítés
# - Model registry előkészítés
# - Minimal CPU terhelés

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# ENV betöltése
load_dotenv()

API_PREFIX = "/api"  # frontend API hívásokhoz

app = FastAPI(title="Quantum Engine Backend", version="1.0")

# CORS engedélyezése frontend számára
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Példa: Model registry integráció később
# from backend.core.model_registry import load_models
# models = load_models()

# Router importok (itt érdemes majd összehangolni a frontendtel)
from backend.routers import tips_router, live_router

app.include_router(tips_router.router, prefix=API_PREFIX)
app.include_router(live_router.router, prefix=API_PREFIX)


@app.get(API_PREFIX + "/ping")
def ping():
    return {"status": "ok", "backend": "running"}


# Hetzner kompatibilis indítás (uvicorn a main helyett procfile vagy CLI)
# uvicorn backend.main:app --host 0.0.0.0 --port 8000