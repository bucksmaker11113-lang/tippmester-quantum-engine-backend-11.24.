# backend/core/bayesian_updater.py

import numpy as np
from backend.utils.logger import get_logger


class BayesianUpdater:
    """
    BAYESIAN UPDATER – PRO VERSION
    -------------------------------
    Feladata:
        • Több engine valószínűségét Bayes szerint összevonni
        • Engine megbízhatóság (reliability) súlyozása
        • Volatility-adjusted likelihood
        • Prior → Posterior frissítés
        • Hibatűrő, 50 engine-ig stabil
    """

    def __init__(self, config=None):
        self.config = config or {}

        self.prior = self.config.get("prior", 0.5)
        self.min_reliability = self.config.get("min_reliability", 0.1)
        self.max_engines = self.config.get("max_engines", 50)
        self.volatility_weight = self.config.get("volatility_weight", 0.15)

        self.logger = get_logger()

    # ======================================================================
    # VOLATILITY CORRECTION
    # ======================================================================
    def _correct_for_volatility(self, prob, volatility):
        """
        A nagy volatilitás csökkenti az engine biztosításába vetett hitet.
        (0–1 skálán)
        """
        vol = np.clip(volatility, 0, 1)
        damp = 1 - vol * self.volatility_weight
        return np.clip(prob * damp, 0.01, 0.99)

    # ======================================================================
    # FŐ FUNKCIÓ
    # ======================================================================
    def update(self, engine_outputs):
        """
        Bemenet:
        engine_outputs = [
            {
                "prob": float(0–1),
                "reliability": float(0–1),
                "volatility": float(0–1)
            },
            ...
        ]

        Visszatér:
            posterior probability (0–1)
        """

        if not engine_outputs:
            return self.prior

        # Biztonsági limit: túl sok engine → downscale
        if len(engine_outputs) > self.max_engines:
            engine_outputs = engine_outputs[: self.max_engines]

        log_likelihoods = []
        log_weights = []

        for eng in engine_outputs:
            try:
                prob = float(eng.get("prob", 0.5))
                reliability = float(eng.get("reliability", 0.5))
                volatility = float(eng.get("volatility", 0.0))
            except:
                continue

            # Minimum reliability biztosítása
            reliability = np.clip(reliability, self.min_reliability, 1.0)

            # Volatility correction
            prob = self._correct_for_volatility(prob, volatility)

            # Bayes likelihood odds formában
            likelihood = np.clip(prob / (1 - prob + 1e-9), 1e-6, 1e6)

            # Logarithmikus súlyozás (numerikusan stabil)
            log_likelihoods.append(np.log(likelihood))
            log_weights.append(reliability)

        if not log_likelihoods:
            return self.prior

        # Weighted log-likelihood
        weighted_ll = np.average(log_likelihoods, weights=log_weights)

        # Posterior odds
        prior_odds = self.prior / (1 - self.prior + 1e-9)
        post_odds = prior_odds * np.exp(weighted_ll)

        posterior = post_odds / (1 + post_odds)

        # clamp
        posterior = float(np.clip(posterior, 0.01, 0.99))

        self.logger.info(f"[BayesianUpdater] Posterior={round(posterior,4)}")

        return posterior
