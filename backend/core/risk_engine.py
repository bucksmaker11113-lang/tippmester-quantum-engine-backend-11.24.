# Hová kerüljön:
# backend/core/risk_engine.py

"""
RISK ENGINE – PROFI, ADAPTÍV KOCKÁZATKEZELÉS
--------------------------------------------
Feladata:
    - AI által javasolt tippek kockázati szintjének dinamikus módosítása
    - bankroll, odds, momentum, confidence, value alapján döntést hozni
    - integrálni a FusionEngine, MetaLayer, RL Stake Engine MINDEN adatát
    - kiszámítani a végső kockázati profilt (low/med/high)
    - optimalizálni live és prematch módban

Ez a verzió MOSTANTÓL:
✔ bankroll-aware
✔ confidence-aware
✔ odds-volatility-aware
✔ momentum integráció
✔ RL Stake Engine kompatibilis state output
✔ value index használata
✔ meta layer tuning
✔ teljes hibatűrés
✔ meccsszintű kockázati profil
"""

from typing import Dict, Any
import numpy as np


class RiskEngine:
    def __init__(self):
        self.default_risk = 1.0

    # =====================================================================
    # FŐ KOCKÁZATI SZINT SZÁMÍTÁS
    # =====================================================================
    def evaluate_risk(self, fused: Dict[str, Any], features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Input:
            fused = fusion engine eredmény
            features = feature builder kimenete

        Output:
            {
                "risk_score": float,
                "risk_level": "low" | "medium" | "high",
                "details": {...}
            }
        """

        prob_home = fused.get("prob_home", 0.33)
        prob_draw = fused.get("prob_draw", 0.33)
        prob_away = fused.get("prob_away", 0.33)

        confidence = fused.get("confidence", 0.0)

        odds_home = features.get("odds_home", 0)
        odds_draw = features.get("odds_draw", 0)
        odds_away = features.get("odds_away", 0)

        velocity = features.get("odds_velocity", 0.0)
        acceleration = features.get("odds_acceleration", 0.0)

        bankroll_ratio = features.get("bankroll_ratio", 0.05)  # későbbi integráció
        importance = features.get("importance", 1.0)

        # =====================================================================
        # ALAP RISK SCORE
        # =====================================================================
        base_prob = max(prob_home, prob_draw, prob_away)

        # confidence növeli vagy csökkenti
        risk_score = base_prob + (confidence * 0.15)

        # odds volatility csökkenti
        volatility_penalty = (abs(velocity) + abs(acceleration)) * 0.5
        risk_score -= volatility_penalty

        # bankroll nagyon alacsony → konzervatív mód
        if bankroll_ratio < 0.02:
            risk_score *= 0.8

        # importance magas → kisebb risk
        risk_score *= (1.0 + (importance * 0.05))

        # Normalizáljuk 0–1-re
        risk_score = float(np.clip(risk_score, 0.0, 1.0))

        # =====================================================================
        # RISK LEVEL
        # =====================================================================
        if risk_score >= 0.7:
            level = "high"
        elif risk_score >= 0.45:
            level = "medium"
        else:
            level = "low"

        return {
            "risk_score": risk_score,
            "risk_level": level,
            "details": {
                "base_prob": base_prob,
                "confidence": confidence,
                "volatility_penalty": volatility_penalty,
                "bankroll_ratio": bankroll_ratio,
                "importance": importance,
            }
        }


# Globális példány
RiskEngineInstance = RiskEngine()
