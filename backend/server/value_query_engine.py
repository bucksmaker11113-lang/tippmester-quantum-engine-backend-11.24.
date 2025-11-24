# backend/server/value_query_engine.py

import re
from difflib import get_close_matches

from backend.scraper.odds_aggregator import OddsAggregator
from backend.pipeline.ensemble_pipeline import EnsemblePipeline
from backend.pipeline.tip_generator_pro import TipGeneratorPro
from backend.engine.live_engine import LiveEngine
from backend.utils.logger import get_logger


class ValueQueryEngine:
    """
    VALUE QUERY ENGINE
    ------------------
    Chat kérdések feldolgozása:
        - "Van value a Liverpool - Arsenal meccsen?"
        - "Melyik oldalon van value?"
        - "Érdemes fogadni 2.30-on?"
        - "Mi a legjobb fogadás erre a meccsre?"
        - "A screenshotból milyen tippek vannak?"
    """

    def __init__(self, config=None):
        self.config = config or {}

        self.logger = get_logger()
        self.aggregator = OddsAggregator()
        self.ensemble = EnsemblePipeline(config)
        self.tipgen = TipGeneratorPro(config)
        self.live_engine = LiveEngine(config)

        # ismert csapatlista
        self.team_list = self._load_team_list()

    # ----------------------------------------------------------
    # 1) csapatlista beolvasás
    # ----------------------------------------------------------
    def _load_team_list(self):
        return [
            "Liverpool", "Arsenal", "Chelsea", "Manchester City",
            "Manchester United", "Tottenham", "Barcelona", "Real Madrid",
            "Atletico", "Bayern", "PSG", "Juventus", "Inter", "Milan",
            "Napoli", "Roma", "Dortmund", "Leipzig"
        ]

    # ----------------------------------------------------------
    # 2) természetes nyelv → team felismerés
    # ----------------------------------------------------------
    def extract_teams(self, msg: str):
        words = re.findall(r"[A-Za-z]+", msg)

        found = []

        for w in words:
            m = get_close_matches(w, self.team_list, n=1, cutoff=0.7)
            if m:
                found.append(m[0])

        found = list(dict.fromkeys(found))

        if len(found) >= 2:
            return found[0], found[1]

        return None, None

    # ----------------------------------------------------------
    # 3) odds felismerés kérdésből
    # ----------------------------------------------------------
    def extract_odds(self, msg: str):
        raw = re.findall(r"\d+[.,]\d+", msg)
        clean = [float(x.replace(",", ".")) for x in raw]

        for v in clean:
            if 1.01 <= v <= 20:
                return v

        return None

    # ----------------------------------------------------------
    # 4) fő lekérdező logika
    # ----------------------------------------------------------
    def query_value(self, msg: str):

        # 1) csapat felismerés
        home, away = self.extract_teams(msg)
        if not home or not away:
            return {
                "error": "Nem tudom felismerni a csapatneveket.",
                "parsed_text": msg
            }

        self.logger.info(f"VALUE QUERY: {home} vs {away}")

        # 2) odds aggregator → bukikból fair odds
        agg = self.aggregator.get_aggregated_odds(home, away)
        if not agg:
            return {"error": "Nincs odds adat erre a meccsre."}

        # 3) odds kivonása
        fair_odds = agg

        # 4) ensemble pipeline meghívása
        # model_outputs STUB → később engine integráció
        model_outputs = {
            "mc3": {},
            "lstm": {},
            "gnn": {},
            "poisson": {},
            "rl": {},
        }

        final_pred = self.ensemble.run(model_outputs, {0: fair_odds})

        # 5) tip generator → ajánlott oldal
        prediction = next(iter(final_pred.values()))
        single = self.tipgen.generate_single(final_pred, bankroll=1000)

        # 6) értelmes válasz formázás
        response = {
            "match": f"{home} vs {away}",
            "fair_odds": fair_odds,
            "analysis": {
                "probability": prediction.get("probability", 0),
                "value_score": prediction.get("value_score", 0),
                "deep_value": prediction.get("deep_value", 0),
                "confidence": prediction.get("confidence", 0),
            },
            "recommended": single
        }

        return response

    # ----------------------------------------------------------
    # 5) user-kérdés: "Érdemes megtenni 2.30-on?"
    # ----------------------------------------------------------
    def query_specific_odds(self, msg: str):
        user_odds = self.extract_odds(msg)
        if not user_odds:
            return {"error": "Nem találok konkrét oddsot a kérdésben."}

        return {"your_odds": user_odds, "value_estimate": "később készítjük el"}
