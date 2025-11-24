# backend/engine/bayesian_updater.py
# Bayesian Updater – stabilizált, kvant-szintű valószínűségfrissítés
# - Shrinkeli az extrém model predikciókat
# - Priorokkal korrigál (league-level priors)
# - CPU-barát

import numpy as np

class BayesianUpdater:
    def __init__(self, prior_strength: float = 0.25):
        """
        prior_strength: milyen erősen húzza vissza a modelt a prior irányába
        0.25 = 25% shrink (kvant standard)
        """
        self.prior_strength = prior_strength

        # Alap priorok (league-level win/draw/lose distribution)
        self.priors = {
            "home": 0.45,
            "draw": 0.27,
            "away": 0.28,
        }

    def update(self, model_probs: dict, match_data: dict) -> dict:
        """
        model_probs = {"home": p1, "draw": p2, "away": p3}
        Bayesian shrinkage a túl extrém valószínűségek ellen.
        """
        updated = {}

        for key in ["home", "draw", "away"]:
            p_model = model_probs.get(key, 0.0)
            p_prior = self.priors.get(key, 0.0)

            # Bayesian shrinkage formula
            p_final = (
                (1 - self.prior_strength) * p_model +
                self.prior_strength * p_prior
            )

            updated[key] = max(0.0, min(1.0, p_final))

        # normalize
        total = sum(updated.values())
        if total > 0:
            for k in updated:
                updated[k] = round(updated[k] / total, 4)

        return updated