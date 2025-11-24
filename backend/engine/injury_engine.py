# backend/engine/injury_engine.py

import numpy as np
from backend.utils.logger import get_logger

class InjuryEngine:
    """
    INJURY ENGINE – PRO EDITION
    ----------------------------
    Feladata:
        • sérülések, eltiltások és lineup változások hatásának modellezése
        • kulcsjátékos hiány → strength-drop becslés
        • helyettesítő játékos minősége
        • csapatmélység (depth) hatása
        • sérülés-intenzitási faktor (impact_score)
    """

    def __init__(self, config):
        self.config = config
        self.logger = get_logger()

        self.scaling = config.get("injury", {}).get("injury_scaling", 0.30)
        self.depth_scaling = config.get("injury", {}).get("depth_scaling", 0.20)
        self.min_conf = config.get("injury", {}).get("min_confidence", 0.58)

        # fallback
        self.fallback_prob = 0.52

    # ----------------------------------------------------------------------
    # PUBLIC: fő injury predikció
    # ----------------------------------------------------------------------
    def predict(self, match_data):
        outputs = {}

        for match_id, data in match_data.items():
            try:
                prob = self._injury_core(data)
            except Exception as e:
                self.logger.error(f"[Injury] Hiba → fallback: {e}")
                prob = self.fallback_prob

            prob = self._normalize(prob)
            conf = self._confidence(prob, data)
            risk = self._risk(prob, conf)

            outputs[match_id] = {
                "probability": round(prob, 4),
                "confidence": round(conf, 3),
                "risk": round(risk, 3),
                "meta": {
                    "injury_scaling": self.scaling,
                    "depth_scaling": self.depth_scaling
                },
                "source": "Injury"
            }

        return outputs

    # ----------------------------------------------------------------------
    # INJURY MAG – LINEUP DROPOUT MODEL
    # ----------------------------------------------------------------------
    def _injury_core(self, data):
        """
        Bemenő jellemzők:

            • injury_home_weight
            • injury_away_weight
            • missing_key_home
            • missing_key_away
            • depth_home
            • depth_away

        Ezek alapján számolunk strength-drop értéket.
        """

        injury_home = data.get("injury_home_weight", 0.0)
        injury_away = data.get("injury_away_weight", 0.0)

        missing_home = data.get("missing_key_home", 0)      # 0-3
        missing_away = data.get("missing_key_away", 0)

        depth_home = data.get("depth_home", 0.8)            # csapat mélység 0-1
        depth_away = data.get("depth_away", 0.8)

        # KOMBINÁLT HATÁS: (sérülés + hiány + csapatmélység)
        home_drop = (
            injury_home * 0.5 +
            (missing_home * 0.2) -
            (depth_home * self.depth_scaling)
        )

        away_drop = (
            injury_away * 0.5 +
            (missing_away * 0.2) -
            (depth_away * self.depth_scaling)
        )

        # win probability shift
        prob_shift = (away_drop - home_drop) * self.scaling
        prob = 0.5 + prob_shift

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
        injury_quality = data.get("injury_data_quality", 0.75)
        stability = 1 - abs(prob - 0.5)

        conf = injury_quality * 0.6 + stability * 0.4
        return float(max(self.min_conf, min(1.0, conf)))

    # ----------------------------------------------------------------------
    # RISK
    # ----------------------------------------------------------------------
    def _risk(self, prob, conf):
        return float(min(1.0, max(0.0, (1 - prob) * 0.5 + (1 - conf) * 0.5)))
