# backend/server/chat_api.py

import uvicorn
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

from backend.server.value_query_engine import ValueQueryEngine
from backend.engine.ocr_engine import OCREngine
from backend.pipeline.tip_generator_pro import TipGeneratorPro
from backend.system.system_flow import SystemFlow
from backend.utils.logger import get_logger


app = FastAPI()
logger = get_logger()

# AI modulok
config = {}
value_engine = ValueQueryEngine(config)
ocr = OCREngine(config)
flow = SystemFlow(config)
tipper = TipGeneratorPro(config)

# CORS – frontend számára engedélyezett
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------------------------------
# STATUS / ALAP
# -------------------------------------------------------
@app.get("/api/status")
def status():
    return {
        "status": "online",
        "modules": [
            "chat_api",
            "value_query_engine",
            "ocr_engine",
            "tip_generator",
            "system_flow"
        ]
    }


# -------------------------------------------------------
# CHAT ÜZENET → AI VÁLASZ
# -------------------------------------------------------
@app.post("/api/chat")
async def chat_endpoint(message: str):
    """
    Bemenet: szöveg (kérdés, meccs, odds, value)
    Válasz: AI által generált adat
    """
    result = value_engine.query_value(message)
    return result


# -------------------------------------------------------
# VALUE KÉRÉS (külön endpoint)
# -------------------------------------------------------
@app.post("/api/value")
async def value_endpoint(home: str, away: str):
    question = f"{home} {away} value?"
    result = value_engine.query_value(question)
    return result


# -------------------------------------------------------
# OCR KÉPFELDOLGOZÁS
# -------------------------------------------------------
@app.post("/api/ocr")
async def ocr_endpoint(file: UploadFile = File(...)):
    img = await file.read()
    r = ocr.analyze_image(img)
    return r


# -------------------------------------------------------
# TIPPEK LEKÉRÉSE (frontend gombhoz)
# -------------------------------------------------------
@app.get("/api/predict")
async def api_predict():
    result = flow.run_daily_prediction()
    return result


# -------------------------------------------------------
# LIVE TIPPEK
# -------------------------------------------------------
@app.get("/api/live")
async def api_live():
    live_data = flow.run_live()
    return live_data


# -------------------------------------------------------
# SZERVER INDÍTÁSA
# -------------------------------------------------------
def start_chat_api():
    uvicorn.run(app, host="0.0.0.0", port=8090)
