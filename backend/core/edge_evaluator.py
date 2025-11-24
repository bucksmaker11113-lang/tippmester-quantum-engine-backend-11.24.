# Hová kerüljön:
# backend/core/edge_evaluator.py

"""
EDGE EVALUATOR – PROFI VALUE BET & EDGE DETEKTOR
-------------------------------------------------
Feladata:
    - kiszámolni az AI-modell várható értékét (EV)
    - detektálni a value bet lehetőségeket
    - edge score-t adni 0–1 skálán
    - odds movement, liquidity és momentum alapján korrigálni
    - támogatni a live és prematch tippeket
    - integrálódni a FusionEngine + RiskEngine + BankrollEngine rendszerbe

Ez az új verzió:
✔ expected value (EV) formula
✔ implied probability összevetés
✔ momentum + volatility korrekció
✔ value-index számítás
✔ edge-score normalizálás
✔ stabil, hibatűrő rendszer
✔ RL és meta-layer kompatibilis output
"""

from typing import Dict, Any
import numpy as np


class EdgeEvaluator:
    def __init__(self):
        pass

    # =====================================================================
    # FŐ FÜGGVÉNY – EDGE SZÁMÍTÁS
    # =====================================================================
    def evaluate_edge(self, fused: Dict[str, Any], features: Dict[str, Any], liquidity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Input:
            fused: fusion engine output (probabilities + confidence)
            features: odds + implied + form + meta
            liquidity: volatility + money flow + pressure

        Output:
            {
                "ev_home": float,
                "ev_draw": float,
                "ev_away": float,
                "value_index": float,
                "best_pick": "home" | "draw" | "away",
                "edge_score": 0.0–1.0
            }
        """

        odds_home = features.get("odds_home", 0)
        odds_draw = features.get("odds_draw", 0)
        odds_away = features.get("odds_away", 0)

        prob_home = fused.get("prob_home", 0.33)
        prob_draw = fused.get("prob_draw", 0.33)
        prob_away = fused.get("prob_away", 0.33)

        volatility = liquidity.get("volatility_index", 0.0)
        momentum = liquidity.get("momentum", 0.0)

        # =====================================================================
        # EXPECTED VALUE FORMULA
        # =====================================================================
        def ev(prob, odds):
            if odds <= 1e-9:
                return -1.0
            return prob * (odds - 1) - (1 - prob)

        ev_home = ev(prob_home, odds_home)
        ev_draw = ev(prob_draw, odds_draw)
        ev_away = ev(prob_away, odds_away)

        # =====================================================================
        # VALUE INDEX – az EV pozitivitásának erőssége
        # =====================================================================
        raw_values = [ev_home, ev_draw, ev_away]
        max_ev = max(raw_values)

        # Value index normalizálása
        value_index = float(np.clip((max_ev + 1) / 2, 0.0, 1.0))

        # =====================================================================
        # MOMENTUM + VOLATILITY KORREKCIÓ
        # =====================================================================
        # Ha nagy a volatilitás → óvatos value
        value_index *= (1.0 - volatility * 0.2)

        # Ha jó momentum → erősítjük
        if momentum < -0.02:  # odds süllyed – piaci erő
            value_index *= 1.1
        elif momentum > 0.02:  # odds emelkedik – gyenge piac
            value_index *= 0.9

        value_index = float(np.clip(value_index, 0.0, 1.0))

        # =====================================================================
        # BEST PICK
        # =====================================================================
        best_pick_map = {
            ev_home: "home",
            ev_draw: "draw",
            ev_away: "away",
        }
        best_pick = best_pick_map[max_ev]

        # =====================================================================
        # EDGE SCORE
        # =====================================================================
        edge_score = value_index * fused.get("confidence", 0.5)
        edge_score = float(np.clip(edge_score, 0.0, 1.0))

        # =====================================================================
        # OUTPUT
        # =====================================================================
        return {
            "ev_home": float(ev_home),
            "ev_draw": float(ev_draw),
            "ev_away": float(ev_away),
            "value_index": value_index,
            "best_pick": best_pick,
            "edge_score": edge_score,
        }


# Globális példány
EdgeEvaluatorInstance = EdgeEvaluator()
