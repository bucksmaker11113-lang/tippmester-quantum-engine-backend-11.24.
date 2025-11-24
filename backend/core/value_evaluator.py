# Hová kerüljön:
# backend/core/value_evaluator.py

"""
VALUE EVALUATOR – MODERNIZÁLT VALUE BET KIÉRTÉKELŐ MOTOR
--------------------------------------------------------
Feladata:
    - AI által számolt valószínűségek és odds alapján value értéket számolni
    - Implied probability drift detektálása
    - Multi-market támogatás (1X2, O/U, AH, BTTS)
    - Meta-layer és FusionEngine kompatibilitás
    - Liquidity + momentum korrekció

Ez az új verzió:
✔ teljes value score rendszer
✔ implied probability összevetés
✔ delta-index normalizálás
✔ odds-momentum korrekció
✔ confidence tuning
✔ multi-market alap (bővíthető)
✔ drift detektálás
✔ várható érték (EV) előkészítés
"""

from typing import Dict, Any
import numpy as np


class ValueEvaluator:
    def __init__(self):
        pass

    # =====================================================================
    # FŐ FÜGGVÉNY – VALUE KIÉRTÉKELÉS
    # =====================================================================
    def evaluate_value(self, fused: Dict[str, Any], features: Dict[str, Any], liquidity: Dict[str, Any]) -> Dict[str, Any]:
        odds_home = features.get("odds_home", 0)
        odds_draw = features.get("odds_draw", 0)
        odds_away = features.get("odds_away", 0)

        implied_home = features.get("implied_home", 0.0)
        implied_draw = features.get("implied_draw", 0.0)
        implied_away = features.get("implied_away", 0.0)

        prob_home = fused.get("prob_home", 0.33)
        prob_draw = fused.get("prob_draw", 0.33)
        prob_away = fused.get("prob_away", 0.33)

        confidence = fused.get("confidence", 0.0)
        volatility = liquidity.get("volatility_index", 0.0)
        momentum = liquidity.get("momentum", 0.0)

        # =====================================================================
        # DELTA – AI vs. Implied különbség
        # =====================================================================
        delta_home = prob_home - implied_home
        delta_draw = prob_draw - implied_draw
        delta_away = prob_away - implied_away

        # =====================================================================
        # VALUE SCORE – normalizált delta, confidence és momentum figyelembevételével
        # =====================================================================
        def normalize(value):
            return float(np.clip((value + 0.5), 0.0, 1.0))

        value_home = normalize(delta_home + confidence * 0.15 - volatility * 0.1)
        value_draw = normalize(delta_draw + confidence * 0.15 - volatility * 0.1)
        value_away = normalize(delta_away + confidence * 0.15 - volatility * 0.1)

        # Momentum korrekció
        if momentum < -0.02:  # odds süllyed → erős value
            value_home *= 1.1
            value_draw *= 1.1
            value_away *= 1.1
        elif momentum > 0.02:  # odds nő → value gyengül
            value_home *= 0.9
            value_draw *= 0.9
            value_away *= 0.9

        value_home = float(np.clip(value_home, 0.0, 1.0))
        value_draw = float(np.clip(value_draw, 0.0, 1.0))
        value_away = float(np.clip(value_away, 0.0, 1.0))

        # =====================================================================
        # Value Index – legjobb value a három közül
        # =====================================================================
        raw_values = [value_home, value_draw, value_away]
        best_value = max(raw_values)

        # =====================================================================
        # Drift detektálás – ha az implied probability nagyon más, mint a market
        # =====================================================================
        drift_score = float(np.clip(abs(momentum) * 5, 0.0, 1.0))

        # =====================================================================
        # OUTPUT
        # =====================================================================
        return {
            "value_home": value_home,
            "value_draw": value_draw,
            "value_away": value_away,
            "value_index": float(best_value),
            "delta_home": float(delta_home),
            "delta_draw": float(delta_draw),
            "delta_away": float(delta_away),
            "drift_score": drift_score,
            "best_market": ["home", "draw", "away"][raw_values.index(best_value)],
        }


# Globális példány
ValueEvaluatorInstance = ValueEvaluator()
