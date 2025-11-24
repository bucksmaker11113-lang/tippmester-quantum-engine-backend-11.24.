# backend/engine/psychological_bias_engine.py

import numpy as np
from backend.utils.logger import get_logger

class PsychologicalBiasEngine:
    """
    PSYCHOLOGICAL BIAS ENGINE – PRO EDITION
    ---------------------------------------
    Feladata:
        • Fogadói tömeg pszichológiai torzításainak felismerése
        • Favourite bias (kedvenc csapat túlértékelése)
        • Longshot bias (underdog túlfogadása)
        • Recency bias (legutóbbi eredmények túlértékelése)
        • Overreaction bias
        • Herding behaviour (tömeges iránykövetés)
        • Hype bias (média hatás)

    Output:
        "probability" = korrigált value probability, ahol a tömeg hibája számít.
    """

    def __init__(self, config):
        self.config = config
        self.logger = get_logger()

        # bias scaling paraméterek
        self.fav_scaling = config.get("psybias", {}).get("fav_scaling", 0.20)
        self.longshot_scaling = config.get("psybias", {}).get("longshot_scaling", 0.25)
        self.recency_scaling = config.get("psybias", {}).get("recency_scaling", 0.22)
        self.herding_scaling = config.get("psybias", {}).get("herding_scaling", 0.18)
        self.hype_scaling = config.get("psybias", {}).get("hype_scaling", 0.15)

        # fallback
        self.fallback_prob = 0.53
        self.min_conf = 0.58

    # ----------------------------------------------------------------------
    # MAIN PREDICTOR
    # ----------------------------------------------------------------------
    def predict(self, match_data):
        outputs = {}

        for match_id, data in match_data.items():
            try:
                prob = self._bias_core(data)
            except Exception as e:
                self.logger.error(f"[PsyBias] ERROR → fallback: {e}")
                prob = self.fallback_prob

            prob = float(max(0.01, min(0.99, prob)))

            conf = self._confidence(prob, data)
            risk = self._risk(prob, conf)

            outputs[match_id] = {
                "probability": round(prob, 4),
                "confidence": round(conf, 3),
                "risk": round(risk, 3),
                "meta": {"psychological_bias": True},
                "source": "PsychologicalBias"
            }

        return outputs

    # ----------------------------------------------------------------------
    # CORE LOGIC – BIAS KEZELÉS
    # ----------------------------------------------------------------------
    def _bias_core(self, data):
        """
        Várt input:
            • fav_popularity          (0–1)
            • longshot_popularity    (0–1)
            • recency_strength       (0–1)
            • herding_strength       (0–1)
            • hype_factor            (0–1)
        """

        fav_pop = data.get("fav_popularity", 0.50)
        long_pop = data.get("longshot_popularity", 0.50)
        recency = data.get("recency_strength", 0.50)
        herding = data.get("herding_strength", 0.50)
        hype = data.get("hype_factor", 0.50)

        # Kedvencre túl sok fogadás → fade signal
        fav_effect = (0.5 - fav_pop) * self.fav_scaling

        # Underdog túl nagy hype → fade signal
        longshot_effect = (0.5 - long_pop) * self.longshot_scaling

        # Recency → tömeg túlreagálja a formát
        recency_effect = (0.5 - recency) * self.recency_scaling

        # Tömeges iránykövetés → extra torzítás
        herding_effect = (0.5 - herding) * self.herding_scaling

        # Média hype → odds torzul
        hype_effect = (0.5 - hype) * self.hype_scaling

        prob_shift = (
            fav_effect +
            longshot_effect +
            recency_effect +
            herding_effect +
            hype_effect
        )

        prob = 0.5 + prob_shift
        return prob

    # ----------------------------------------------------------------------
    # CONFIDENCE
    # ----------------------------------------------------------------------
    def _confidence(self, prob, data):
        data_q = data.get("bias_data_quality", 0.8)
        stability = 1 - abs(prob - 0.5)

        conf = data_q * 0.55 + stability * 0.45
        return float(max(self.min_conf, min(1.0, conf)))

    # ----------------------------------------------------------------------
    # RISK
    # ----------------------------------------------------------------------
    def _risk(self, prob, conf):
        return float(min(1.0, max(0.0,
            (1 - conf) * 0.5 + (1 - prob) * 0.5
        )))
