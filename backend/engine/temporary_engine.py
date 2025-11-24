# backend/engine/temporary_engine.py

import numpy as np
from backend.utils.logger import get_logger


class TemporaryEngine:
    """
    TEMPORARY ENGINE – FAILSAFE EDITION
    ------------------------------------
    Feladata:
        • minden engine hibája, üres outputja vagy hiánya esetén
          stabil, matematikailag biztonságos fallback értéket ad
        • normalizált probability + value + risk + confidence
        • garantálja, hogy FusionEngine NEM ÁLL LE
        • garantálja, hogy Training Pipeline mindig kap adatot
        • safe EV / value score / CLV baseline
    """

    def __init__(self, config=None):
        self.config = config or {}
        self.logger = get_logger()

        c = self.config.get("temporary", {})
        self.min_conf = c.get("min_confidence", 0.55)
        self.base_prob = c.get("base_probability", 0.55)
        self.base_value = c.get("base_value", 0.02)
        self.base_risk = c.get("base_risk", 0.45)

    # ----------------------------------------------------------------------
    # MAIN FAILSAFE PREDICTION
    # ----------------------------------------------------------------------
    def analyze(self, missing_module: str = None, meta: dict = None):
        """
        A rendszer bármely engine hibája esetén meghívódik.

        Visszaad:
        {
            "probability": 0.55,
            "value_score": 0.02,
            "ev": 0.01,
            "clv": 0.0,
            "confidence": 0.58,
            "risk": 0.44,
            "source": "TemporaryEngine",
            "note": "fallback activated (trend engine missing)",
        }
        """

        note = f"fallback activated ({missing_module})" if missing_module else "fallback activated"

        prob = float(self.base_prob)
        v = float(self.base_value)
        ev = max(-0.20, min(0.20, prob * 1.01 - 1))  # safe EV approx
        clv = 0.0  # neutral

        conf = self._confidence(prob)
        risk = self._risk(prob, conf)

        return {
            "probability": round(prob, 4),
            "value_score": round(v, 4),
            "ev": round(ev, 4),
            "clv": round(clv, 4),
            "confidence": round(conf, 3),
            "risk": round(risk, 3),
            "source": "TemporaryEngine",
            "note": note
        }

    # ----------------------------------------------------------------------
    # SAFE CONFIDENCE
    # ----------------------------------------------------------------------
    def _confidence(self, prob):
        """
        Fallback confidence:
        - mindig legalább min_conf
        - minél távolabb 0.5-től → annál nagyobb
        """
        conf = 0.5 + abs(prob - 0.5)
        return float(max(self.min_conf, min(1.0, conf)))

    # ----------------------------------------------------------------------
    # SAFE RISK
    # ----------------------------------------------------------------------
    def _risk(self, prob, conf):
        """
        Fallback risk:
        - a stabilitást növeli (nem túl magas)
        - mindig kompatibilis a FusionEngine-nel
        """
        return float(min(1.0, max(0.0, (1 - prob) * 0.4 + (1 - conf) * 0.6)))
