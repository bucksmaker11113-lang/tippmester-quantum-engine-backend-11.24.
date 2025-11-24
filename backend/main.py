# Hová kerüljön:
# backend/main.py

"""
MAIN ENTRYPOINT – ÚJRAÍRT, PROFI, HIBAMENTES VERZIÓ
---------------------------------------------------
Feladata:
- Betölti a környezeti változókat
- Inicializálja a teljes rendszert (modellek, pipelineok, live engine)
- Elindítja a FastAPI szervert (REST + WebSocket)
- Elindítja a scheduler feladatokat (daily pipeline)
- Biztosítja a rendezett backend struktúrát
"""

import uvicorn
import asyncio
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ROUTEREK
from server.chat_api import router as chat_router
from server.value_query_engine import router as value_router

# ORCHESTRATOR
from core.master_orchestrator import MasterOrchestrator

# SCHEDULER
from system.scheduler import start_scheduler

# ENV BETÖLTÉS
from dotenv import load_dotenv
load_dotenv()

# ============================================================================
# FASTAPI APP
# ============================================================================
app = FastAPI(title="Tippmester Quantum Engine API", version="2.0")

# CORS engedélyezés
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ROUTER REGISZTRÁCIÓ
app.include_router(chat_router, prefix="/chat")
app.include_router(value_router, prefix="/value")

# ============================================================================
# RENDSZER INDÍTÁS
# ============================================================================
@app.on_event("startup")
async def startup_event():
    print("[SYSTEM] Backend indul...")

    # Orchestrator példányosítása
    Global.master = MasterOrchestrator()
    await Global.master.initialize_all()
    print("[SYSTEM] Orchestrator kész.")

    # Scheduler indítása (napi tippek, tréning, pipelineok)
    start_scheduler(Global.master)
    print("[SYSTEM] Scheduler elindítva.")


# ============================================================================
# GLOBAL STATE
# ============================================================================
class Global:
    master: MasterOrchestrator = None


# ============================================================================
# INDÍTÁS LOKÁLISBAN
# ============================================================================
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 8000)),
        reload=True,
    )
