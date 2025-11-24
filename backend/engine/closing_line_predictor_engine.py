# backend/engine/closing_line_predictor_engine.py

import numpy as np
from backend.utils.logger import get_logger


class ClosingLinePredictor:
    """
    CLOSING LINE PREDICTOR ENGINE – PRO EDITION
    -------------------------------------------
    Feladata:
        • záró odds előrejelzése (expected closing odds)
        • sharp money hatás modellezése
        • drift + volatility + momentum együtt kezelése
        • fair odds baseline becslése
        • CLV (closing line value) számítása
    """

    def __init__(self, config=None):
        self.config = config or {}
        self.logger = get_logger()

        c = self.config.get("closing_line", {})

        self.max_drift = c.get("max_drift", 0.15)           # max ±15% drift
        self.sharp_weight = c.get("sharp_weight", 0.35)     # sharp money hatás
        self.volatility_weight = c.get("volatility_weight", 0.25)
        self.momentum_weight = c.get("momentum_weight", 0.20)
        self.noise = c.get("noise", 0.03)                   # sztochasztikus zaj
        self.simulations = c.get("simulations", 500)        # Monte Carlo futások

    # ======================================================================
    # FAIR ODDS ESTIMATE
    # ======================================================================
    def _fair_odds(self, prob):
        try:
            return 1 / max(prob, 0.01)
        except:
            return None

    # ======================================================================
    # ONE SIMULATION OF ODDS DRIFT
    # ======================================================================
    def _simulate_drift(self, odds, drift, sharp, volatility, momentum):
        """
        Egyetlen oddsmozgás-szimuláció
        """

        # baseline drift
        directional_drift = drift

        # sharp money hatása
        directional_drift += sharp * self.sharp_weight

        # volatility = gyorsabb változás
        directional_drift += volatility * self.volatility_weight

        # momentum (market momentum, nem játék)
        directional_drift += momentum * self.momentum_weight

        # zaj
        directional_drift += np.random.normal(0, self.noise)

        # clamp
        directional_drift = float(np.clip(
            directional_drift,
            -self.max_drift,
            self.max_drift
        ))

        # új odds
        expected = odds * (1 - directional_drift)

        return float(max(1.01, expected))

    # ======================================================================
    # MAIN PREDICTOR
    # ======================================================================
    def predict(self, data):
        """
        data:
            {
                "current_odds": 1.82,
                "drift": 0.06,
                "sharp_money": 0.3,
                "volatility": 0.12,
                "momentum": 0.15,
                "probability": 0.61
            }
        """

        odds = data.get("current_odds", 2.0)
        drift = data.get("drift", 0)
        sharp = data.get("sharp_money", 0)
        volatility = data.get("volatility", 0)
        momentum = data.get("momentum", 0)
        prob = data.get("probability", 0.5)

        # fair odds baseline – biztonságosabb, stabilabb
        fair_odds = self._fair_odds(prob)

        simulations = []

        for _ in range(self.simulations):
            sim = self._simulate_drift(
                odds=odds,
                drift=drift,
                sharp=sharp,
                volatility=volatility,
                momentum=momentum
            )
            simulations.append(sim)

        # expected closing price
        expected_closing = float(np.mean(simulations))

        # CLV
        clv = self.clv(odds, expected_closing)

        return {
            "expected_closing": round(expected_closing, 4),
            "fair_odds": round(fair_odds, 4) if fair_odds else None,
            "clv": round(clv, 4),
            "volatility": float(volatility),
            "sharp": float(sharp),
            "momentum": float(momentum),
            "drift": float(drift),
        }

    # ======================================================================
    # CLV CALCULATION
    # ======================================================================
    def clv(self, current_odds, expected_closing):
        """
        CLV = (expected closing - current) / current
        """
        return float((expected_closing - current_odds) / current_odds)
