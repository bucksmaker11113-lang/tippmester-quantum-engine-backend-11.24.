# backend/engine/gameflow_engine.py

import numpy as np
from backend.utils.logger import get_logger

class GameflowEngine:
    """
    GAMEFLOW ENGINE – PRO EDITION
    ------------------------------
    Feladata:
        • Meccs tempó, pressing, momentum és flow modellezése
        • Live és pre-match dinamika előrejelzése
        • Team-attack vs team-defense interakció elemzése
        • Flow → win probability konverzió
        • Confidence + risk számítás
        • Támogatja a FusionEngine és LiveEngine rétegeket
    """

    def __init__(self, config):
        self.config = config
        self.logger = get_logger()

        # scaling és stabilizáció
        self.flow_scaling = config.get("gameflow", {}).get("flow_scaling", 1.12)
        self.momentum_weight = config.get("gameflow", {}).get("momentum_weight", 0.35)
        self.press_weight = config.get("gameflow", {}).get("press_weight", 0.25)
        self.pace_weight = config.get("gameflow", {}).get("pace_weight", 0.40)

        # fallback
        self.fallback_prob = 0.55
        self.min_conf = config.get("gameflow", {}).get("min_confidence", 0.60)

    # ----------------------------------------------------------------------
    # PUBLIC PREDICTOR
    # ----------------------------------------------------------------------
    def predict(self, match_data):
        outputs = {}

        for match_id, data in match_data.items():
            try:
                prob = self._flow_core(data)
            except Exception as e:
                self.logger.error(f"[Gameflow] Hiba, fallback: {e}")
                prob = self.fallback_prob

            prob = self._normalize(prob)
            conf = self._confidence(prob, data)
            risk = self._risk(prob, conf)

            outputs[match_id] = {
                "probability": round(prob, 4),
                "confidence": round(conf, 3),
                "risk": round(risk, 3),
                "meta": {
                    "flow_scaling": self.flow_scaling,
                    "momentum_weight": self.momentum_weight,
                    "press_weight": self.press_weight,
                    "pace_weight": self.pace_weight
                },
                "source": "Gameflow"
            }

        return outputs

    # ----------------------------------------------------------------------
    # GAMEFLOW MAG – TEMPÓ + MOMENTUM + PRESSING
    # ----------------------------------------------------------------------
    def _flow_core(self, data):
        """
        A Gameflow a következő komponensekből épül fel:
            • pace_index       (game speed)
            • momentum_home    (attack momentum)
            • momentum_away
            • pressing_home     (pressure intensity)
            • pressing_away
        """

        pace = data.get("pace", 1.0)
        momentum_home = data.get("momentum_home", 0.5)
        momentum_away = data.get("momentum_away", 0.5)
        press_home = data.get("press_home", 0.5)
        press_away = data.get("press_away", 0.5)

        # flow iránya
        flow = (
            (momentum_home - momentum_away) * self.momentum_weight +
            (press_home - press_away) * self.press_weight +
            (pace - 1.0) * self.pace_weight
        )

        # probability konverzió
        prob = 0.5 + (flow * self.flow_scaling)

        return float(prob)

    # ----------------------------------------------------------------------
    # NORMALIZÁLÁS
    # ----------------------------------------------------------------------
    def _normalize(self, p):
        return float(max(0.01, min(0.99, p)))

    # ----------------------------------------------------------------------
    # CONFIDENCE
    # ----------------------------------------------------------------------
    def _confidence(self, prob, data):
        stability = 1 - abs(prob - 0.5)
        data_quality = data.get("data_quality", 0.85)

        conf = (stability * 0.3 + data_quality * 0.7)
        return float(max(self.min_conf, min(1.0, conf)))

    # ----------------------------------------------------------------------
    # RISK
    # ----------------------------------------------------------------------
    def _risk(self, prob, conf):
        return float(min(1.0, max(0.0, (1 - prob) * 0.5 + (1 - conf) * 0.5)))
