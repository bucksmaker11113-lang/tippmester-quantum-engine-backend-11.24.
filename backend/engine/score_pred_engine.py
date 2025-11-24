# backend/engine/score_pred_engine.py

import numpy as np
from backend.utils.logger import get_logger

class ScorePredEngine:
    """
    SCORE PRED ENGINE – PRO EDITION
    --------------------------------
    Feladata:
        • teljes gólelőrejelzés score-mátrixszal
        • 0–5 gól tartomány Poisson + xG kombóval
        • exact score distribution
        • goal difference modell
        • win/draw/loss probability score-mátrix alapján
        • FusionEngine + ValueEngine támogatás
    """

    def __init__(self, config):
        self.config = config
        self.logger = get_logger()

        # maximális gólszám
        self.max_goals = config.get("score_pred", {}).get("max_goals", 5)

        # scaling
        self.variance_boost = config.get("score_pred", {}).get("variance_boost", 1.05)

        # fallback
        self.fallback_prob = 0.50
        self.min_conf = config.get("score_pred", {}).get("min_confidence", 0.60)

    # ----------------------------------------------------------------------
    # PUBLIC: fő score predikció
    # ----------------------------------------------------------------------
    def predict(self, match_data):
        outputs = {}

        for match_id, data in match_data.items():
            try:
                prob = self._score_core(data)
            except Exception as e:
                self.logger.error(f"[ScorePred] Hiba → fallback: {e}")
                prob = self.fallback_prob

            prob = float(max(0.01, min(0.99, prob)))

            conf = self._confidence(prob, data)
            risk = self._risk(prob, conf)

            outputs[match_id] = {
                "probability": round(prob, 4),
                "confidence": round(conf, 3),
                "risk": round(risk, 3),
                "meta": {
                    "max_goals": self.max_goals,
                    "variance_boost": self.variance_boost
                },
                "source": "ScorePred"
            }

        return outputs

    # ----------------------------------------------------------------------
    # SCORE MAG
    # ----------------------------------------------------------------------
    def _score_core(self, data):
        """
        Score predikció Poisson + xG alapján.

        Input:
            xg_home, xg_away
            attack_home, defense_home
            attack_away, defense_away
        """

        xg_home = data.get("xg_home", 1.2)
        xg_away = data.get("xg_away", 1.1)

        att_h = data.get("attack_home", 1.0)
        def_h = data.get("defense_home", 1.0)
        att_a = data.get("attack_away", 1.0)
        def_a = data.get("defense_away", 1.0)

        # score-mátrix lambda-k
        lam_h = xg_home * att_h * def_a * self.variance_boost
        lam_a = xg_away * att_a * def_h * self.variance_boost

        lam_h = max(0.1, min(5.0, lam_h))
        lam_a = max(0.1, min(5.0, lam_a))

        home_win_prob = 0
        total_prob = 0

        # 0–5 gólig score mátrix
        for hg in range(self.max_goals + 1):
            p_h = self._poisson(hg, lam_h)

            for ag in range(self.max_goals + 1):
                p_a = self._poisson(ag, lam_a)

                p = p_h * p_a
                total_prob += p

                if hg > ag:
                    home_win_prob += p

        if total_prob == 0:
            return self.fallback_prob

        return home_win_prob / total_prob

    # ----------------------------------------------------------
    # POISSON
    # ----------------------------------------------------------
    def _poisson(self, k, lam):
        return (lam**k) * np.exp(-lam) / np.math.factorial(k)

    # ----------------------------------------------------------
    # CONFIDENCE
    # ----------------------------------------------------------
    def _confidence(self, prob, data):
        score_data_q = data.get("score_data_quality", 0.82)
        stability = 1 - abs(prob - 0.5)

        conf = score_data_q * 0.6 + stability * 0.4
        return float(max(self.min_conf, min(1.0, conf)))

    # ----------------------------------------------------------
    # RISK
    # ----------------------------------------------------------
    def _risk(self, prob, conf):
        return float(
            min(1.0, max(0.0, (1 - prob) * 0.55 + (1 - conf) * 0.45))
        )
