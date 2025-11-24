# backend/engine/public_money_engine.py

import numpy as np
from backend.utils.logger import get_logger

class PublicMoneyEngine:
    """
    PUBLIC MONEY ENGINE – PRO EDITION
    -----------------------------------
    Feladata:
        • Public vs sharp money arány detektálása
        • Bookmaker offset figyelése
        • Odds movement elemzése
        • Public bias → anti-public probability shift
        • Market distortion jelzések
    """

    def __init__(self, config):
        self.config = config
        self.logger = get_logger()

        # Scaling
        self.public_scaling = config.get("public", {}).get("public_scaling", 0.18)
        self.sharp_scaling = config.get("public", {}).get("sharp_scaling", 0.25)
        self.odds_move_scaling = config.get("public", {}).get("odds_move_scaling", 0.15)

        # fallback
        self.fallback_prob = 0.53
        self.min_conf = config.get("public", {}).get("min_confidence", 0.60)

    # ----------------------------------------------------------------------
    # PUBLIC PREDICTION
    # ----------------------------------------------------------------------
    def predict(self, match_data):
        outputs = {}

        for match_id, data in match_data.items():

            try:
                prob = self._public_core(data)
            except Exception as e:
                self.logger.error(f"[PublicMoney] Hiba → fallback: {e}")
                prob = self.fallback_prob

            # normalize
            prob = self._normalize(prob)

            # confidence + risk
            conf = self._confidence(prob, data)
            risk = self._risk(prob, conf)

            outputs[match_id] = {
                "probability": round(prob, 4),
                "confidence": round(conf, 3),
                "risk": round(risk, 3),
                "meta": {
                    "public_scaling": self.public_scaling,
                    "sharp_scaling": self.sharp_scaling,
                    "odds_move_scaling": self.odds_move_scaling
                },
                "source": "PublicMoney"
            }

        return outputs

    # ----------------------------------------------------------------------
    # CORE LOGIC – PUBLIC vs SHARP MONEY
    # ----------------------------------------------------------------------
    def _public_core(self, data):
        """
        Várt input:
            • public_pct (public money %)
            • sharp_pct  (sharp money %)
            • odds_open
            • odds_now
            • bookmaker_shift (true book % change)
        """

        public_pct = data.get("public_pct", 0.50)       # 0–1
        sharp_pct = data.get("sharp_pct", 0.50)         # 0–1

        odds_open = data.get("odds_open", 2.00)
        odds_now  = data.get("odds_now", 2.00)

        bookmaker_shift = data.get("bookmaker_shift", 0.0)  # 0–1

        # PUBLIC BIAS (ha public túl nagy → ellenfogadás value)
        public_bias = (public_pct - 0.50) * -self.public_scaling

        # SHARP BIAS (ha sharps egy oldalon → erős jel)
        sharp_bias = (sharp_pct - 0.50) * self.sharp_scaling

        # ODDS MOVEMENT (drift)
        odds_move = (odds_open - odds_now)
        odds_move_effect = odds_move * self.odds_move_scaling

        # Bookmaker correction (ha túl sokat állítanak → jel)
        book_effect = bookmaker_shift * 0.10

        # Probability shift
        prob_shift = public_bias + sharp_bias + odds_move_effect + book_effect

        prob = 0.5 + prob_shift
        return float(prob)

    # ----------------------------------------------------------------------
    # NORMALIZATION
    # ----------------------------------------------------------------------
    def _normalize(self, p):
        return float(max(0.01, min(0.99, p)))

    # ----------------------------------------------------------------------
    # CONFIDENCE
    # ----------------------------------------------------------------------
    def _confidence(self, prob, data):
        public_data_q = data.get("public_data_quality", 0.75)
        stability = 1 - abs(prob - 0.5)

        conf = (public_data_q * 0.6 + stability * 0.4)
        return float(max(self.min_conf, min(1.0, conf)))

    # ----------------------------------------------------------------------
    # RISK
    # ----------------------------------------------------------------------
    def _risk(self, prob, conf):
        return float(min(1.0, max(0.0, (1 - prob) * 0.5 + (1 - conf) * 0.5)))
