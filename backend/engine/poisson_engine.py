# backend/engine/poisson_engine.py

import numpy as np
from backend.utils.logger import get_logger

class PoissonEngine:
    """
    POISSON ENGINE – PRO EDITION
    -----------------------------
    Feladata:
        • Gólvalószínűségek modellezése Poisson eloszlással
        • xG-alapú lambda számítás
        • attack/defense rating beszámítása
        • variance & pace korrekció
        • normalizált probability output
        • confidence + risk számítás
    """

    def __init__(self, config):
        self.config = config
        self.logger = get_logger()

        # Variancia és scaling faktorok
        self.variance_boost = config.get("poisson", {}).get("variance_boost", 1.08)
        self.scaling = config.get("poisson", {}).get("scaling", 1.10)

        # Confidence baseline
        self.min_conf = config.get("poisson", {}).get("min_confidence", 0.56)

        # Fallback lambda
        self.fallback_lambda = config.get("poisson", {}).get("fallback_lambda", 1.20)

        # Max gólmodell korlát (túl extrém számokat vágunk)
        self.max_goals = config.get("poisson", {}).get("max_goals", 10)

    # ----------------------------------------------------------------------
    # PUBLIC: fő Poisson predikció
    # ----------------------------------------------------------------------
    def predict(self, match_data):
        outputs = {}

        for match_id, data in match_data.items():

            try:
                prob = self._calculate_poisson_prob(data)
            except Exception as e:
                self.logger.error(f"[Poisson] Hiba, fallback: {e}")
                prob = 0.50

            prob = self._normalize(prob)

            conf = self._confidence(prob, data)
            risk = self._risk(prob, conf)

            outputs[match_id] = {
                "probability": round(prob, 4),
                "confidence": round(conf, 3),
                "risk": round(risk, 3),
                "meta": {
                    "variance_boost": self.variance_boost,
                    "scaling": self.scaling
                },
                "source": "Poisson"
            }

        return outputs

    # ----------------------------------------------------------------------
    # POISSON MAG
    # ----------------------------------------------------------------------
    def _calculate_poisson_prob(self, data):
        """
        Klasszikus Poisson logika:
            P(home_goals > away_goals)
        """

        # xG paraméterek
        xg_home = data.get("xg_home", None)
        xg_away = data.get("xg_away", None)

        # ratingek
        att_h = data.get("attack_home", 1.0)
        def_h = data.get("defense_home", 1.0)
        att_a = data.get("attack_away", 1.0)
        def_a = data.get("defense_away", 1.0)
        pace = data.get("pace", 1.0)

        # lambda Home
        if xg_home:
            lambda_home = xg_home * att_h * def_a
        else:
            lambda_home = self.fallback_lambda

        # lambda Away
        if xg_away:
            lambda_away = xg_away * att_a * def_h
        else:
            lambda_away = self.fallback_lambda

        # Variancia + pace korrekció
        lambda_home *= pace * self.variance_boost
        lambda_away *= pace * self.variance_boost

        # limitálás
        lambda_home = max(0.1, min(5.0, lambda_home))
        lambda_away = max(0.1, min(5.0, lambda_away))

        # Gólmátrix
        total_prob = 0
        home_win_prob = 0

        for hg in range(self.max_goals + 1):
            for ag in range(self.max_goals + 1):

                # Poisson probability
                pg_h = self._poisson_p(hg, lambda_home)
                pg_a = self._poisson_p(ag, lambda_away)

                p = pg_h * pg_a
                total_prob += p

                if hg > ag:
                    home_win_prob += p

        if total_prob == 0:
            return 0.5

        return home_win_prob / total_prob

    # ----------------------------------------------------------------------
    # POISSON PROBABILITY
    # ----------------------------------------------------------------------
    def _poisson_p(self, goals, lam):
        return (lam ** goals) * np.exp(-lam) / np.math.factorial(goals)

    # ----------------------------------------------------------------------
    # NORMALIZÁLÁS
    # ----------------------------------------------------------------------
    def _normalize(self, p):
        p *= self.scaling
        return float(max(0.01, min(0.99, p)))

    # ----------------------------------------------------------------------
    # CONFIDENCE
    # ----------------------------------------------------------------------
    def _confidence(self, prob, data):
        # adatminőség
        quality = data.get("data_quality", 0.80)

        # minél távolabb van 0.5-től → annál erősebb jel
        stability = 1 - abs(0.5 - prob)

        conf = quality * 0.5 + stability * 0.5
        return float(max(self.min_conf, min(1.0, conf)))

    # ----------------------------------------------------------------------
    # RISK
    # ----------------------------------------------------------------------
    def _risk(self, prob, conf):
        return float(min(1.0, max(0.0, (1 - prob) * 0.6 + (1 - conf) * 0.4)))
