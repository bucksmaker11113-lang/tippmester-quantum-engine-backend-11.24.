# backend/engine/montecarlo_v3_engine.py

import numpy as np
from backend.utils.logger import get_logger

class MonteCarloV3Engine:
    """
    MONTE CARLO v3 ENGINE – PRO EDITION
    -----------------------------------
    Több tízezres szimuláció a valószínűségek kiszámítására.
    Integrálja:
        • xG-alapú scoring modelleket
        • Poisson-modellt
        • támadás/védelem ratinget
        • variancia modulációt
        • pace (meccstempó) faktorokat
        • luck-regression (extrém score-ok kisimítása)
    """

    def __init__(self, config):
        self.config = config
        self.logger = get_logger()

        self.simulations = config.get("montecarlo", {}).get("simulations", 50000)
        self.max_goals = config.get("montecarlo", {}).get("max_goals", 10)

        # variancia moduláció
        self.variance_boost = config.get("montecarlo", {}).get("variance_boost", 1.15)

        # xG súly
        self.xg_weight = config.get("montecarlo", {}).get("xg_weight", 0.5)

        # rating súly
        self.rating_weight = config.get("montecarlo", {}).get("rating_weight", 0.5)

        # fallback
        self.fallback_prob = 0.50

    # ----------------------------------------------------------------------
    # PUBLIC: fő Monte Carlo futtatás
    # ----------------------------------------------------------------------
    def predict(self, match_data):
        """
        Bemenet: match_data[match_id] = adatok
        Kimenet:
            {
                match_id: {
                    "probability": p,
                    "confidence": c,
                    "risk": r,
                    "meta": {...},
                    "source": "MonteCarloV3"
                }
            }
        """

        results = {}

        for match_id, data in match_data.items():
            try:
                prob = self._run_simulation(data)
            except Exception as e:
                self.logger.error(f"[MonteCarlo] Hiba, fallback: {e}")
                prob = self.fallback_prob

            prob = float(max(0.01, min(0.99, prob)))

            confidence = self._confidence(prob, data)
            risk = self._risk(prob, confidence)

            results[match_id] = {
                "probability": round(prob, 4),
                "confidence": round(confidence, 3),
                "risk": round(risk, 3),
                "meta": {
                    "simulations": self.simulations,
                    "variance_boost": self.variance_boost
                },
                "source": "MonteCarloV3"
            }

        return results

    # ----------------------------------------------------------------------
    # MONTE CARLO MAG: több tízezer szimuláció
    # ----------------------------------------------------------------------
    def _run_simulation(self, data):

        # bemeneti faktorok
        xg_home = data.get("xg_home", 1.2)
        xg_away = data.get("xg_away", 1.1)

        rating_home = data.get("attack_home", 1.0) * data.get("defense_away", 1.0)
        rating_away = data.get("attack_away", 1.0) * data.get("defense_home", 1.0)

        pace = data.get("pace", 1.0)

        # kombinált lambda paraméterek
        lambda_home = (
            xg_home * self.xg_weight +
            rating_home * self.rating_weight
        ) * pace * self.variance_boost

        lambda_away = (
            xg_away * self.xg_weight +
            rating_away * self.rating_weight
        ) * pace * self.variance_boost

        # ne engedjük elszállni
        lambda_home = max(0.2, min(5.0, lambda_home))
        lambda_away = max(0.2, min(5.0, lambda_away))

        # szimulációk
        home_wins = 0
        draws = 0
        away_wins = 0

        for _ in range(self.simulations):
            home_goals = np.random.poisson(lambda_home)
            away_goals = np.random.poisson(lambda_away)

            # luck regression – extrém eredmények letompítása
            if home_goals > self.max_goals:
                home_goals = self.max_goals
            if away_goals > self.max_goals:
                away_goals = self.max_goals

            if home_goals > away_goals:
                home_wins += 1
            elif home_goals == away_goals:
                draws += 1
            else:
                away_wins += 1

        # kimenet → valószínűség "1-es kimenetre"
        total = home_wins + draws + away_wins
        if total == 0:
            return self.fallback_prob

        return home_wins / total

    # ----------------------------------------------------------------------
    # CONFIDENCE
    # ----------------------------------------------------------------------
    def _confidence(self, prob, data):
        quality = data.get("data_quality", 0.85)
        stability = 1 - abs(0.5 - prob)  # minél távolabb 0.5-től → annál stabilabb

        conf = quality * 0.5 + stability * 0.5

        return float(max(0.55, min(1.0, conf)))

    # ----------------------------------------------------------------------
    # RISK
    # ----------------------------------------------------------------------
    def _risk(self, prob, confidence):
        base = (1 - prob)
        risk = base * 0.6 + (1 - confidence) * 0.4

        return float(max(0.0, min(1.0, risk)))
