# backend/server/chat_server.py

import uvicorn
from fastapi import FastAPI, UploadFile, WebSocket
from backend.system.system_flow import SystemFlow
from backend.scraper.odds_aggregator import OddsAggregator
from backend.pipeline.tip_generator_pro import TipGeneratorPro
from backend.engine.live_engine import LiveEngine
from backend.utils.logger import get_logger


app = FastAPI()
logger = get_logger()

# rendszer komponensek
config = {}
flow = SystemFlow(config)
aggregator = OddsAggregator()
tips = TipGeneratorPro(config)
live_engine = LiveEngine()


# ---------------------------------------------------------
# 1) Alap health check
# ---------------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok", "module": "chat_server"}


# ---------------------------------------------------------
# 2) Chat kérdés text formában
# ---------------------------------------------------------
@app.post("/chat")
async def chat_query(message: str):

    msg = message.lower()

    if "value" in msg:
        # példák:
        #  "van value a liverpool - arsenal meccsen?"
        #  "value odds real madrid?"
        return await process_value_query(msg)

    if "tippek" in msg:
        return {"tips": "Tippekhez írd: /predict"}

    return {"answer": f"Nem értem pontosan: {message}"}


# ---------------------------------------------------------
# 3) Kép feltöltés (OCR)
# ---------------------------------------------------------
@app.post("/image")
async def image_upload(file: UploadFile):

    content = await file.read()
    # OCR modul egy későbbi lépésben jön👈
    text = "OCR-kép elemzés helye (később TOP szintre megírva)"

    return {"recognized_text": text}


# ---------------------------------------------------------
# 4) Predikció kérés
# ---------------------------------------------------------
@app.get("/predict")
async def predict():
    result = flow.run_daily_prediction()
    return result


# ---------------------------------------------------------
# 5) WebSocket élő chat kapcsolat
# ---------------------------------------------------------
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    await ws.send_text("Kapcsolat létrejött TippMester AI-val!")

    while True:
        msg = await ws.receive_text()
        response = await process_value_query(msg)
        await ws.send_json(response)


# ---------------------------------------------------------
# 6) VALUE QUERY feldolgozása
# ---------------------------------------------------------
async def process_value_query(msg: str):

    # csapatok felismerése (egyszerű placeholder)
    import re
    teams = re.findall(r"[a-zA-Z]+", msg)
    if len(teams) < 2:
        return {"error": "Nem érthető a mérkőzés neve."}

    home = teams[0]
    away = teams[1]

    logger.info(f"VALUE QUERY: {home} vs {away}")

    odds = aggregator.get_aggregated_odds(home, away)
    if not odds:
        return {"error": "Nem található odds erre a mérkőzésre."}

    # egyszerű value score formula
    fair1 = odds["1"]
    fair2 = odds["2"]

    value_score = {
        "team_1_value": round(1 / fair1, 4),
        "team_2_value": round(1 / fair2, 4),
        "odds": odds
    }

    return value_score


# ---------------------------------------------------------
# 7) Indítás
# ---------------------------------------------------------
def start_server():
    uvicorn.run(app, host="0.0.0.0", port=8080)
