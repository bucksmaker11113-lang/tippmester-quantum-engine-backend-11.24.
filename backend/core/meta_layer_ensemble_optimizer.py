# backend/core/meta_layer_ensemble_optimizer.py

import numpy as np
from collections import defaultdict
from backend.utils.logger import get_logger


class MetaLayerEnsembleOptimizer:
    """
    META-LAYER ENSEMBLE OPTIMIZER – PRO VERSION
    --------------------------------------------
    Feladata:
        • engine súlyok dinamikus optimalizálása
        • engine performance követése (winrate, EV, variance)
        • liga/sportág alapú súlytáblázat fenntartása
        • stabilitási korrekció
        • noise-reduction / volatilitás csillapítás
        • drift-based súly-up/down scaling
        • integráció FusionEngine + Bayesian updater között
    """

    def __init__(self, config=None):
        self.config = config or {}
        self.logger = get_logger()

        # Súlyok per engine
        # Példa: {"poisson": 0.12, "trend": 0.08, ...}
        self.weights = {}

        # Liga-specifikus súlytáblázat
        # {"EPL": {"poisson": 0.11, "trend": 0.19, ...}, ...}
        self.league_weights = defaultdict(lambda: {})

        # Engine performance tracking
        self.performance = defaultdict(lambda: {
            "wins": 0,
            "losses": 0,
            "ev_total": 0.0,
            "samples": 0,
            "variance": 0.0,
        })

        # Learning rate
        self.lr = self.config.get("meta", {}).get("learning_rate", 0.1)

        # Stabilitási faktor
        self.stability_factor = self.config.get("meta", {}).get("stability_factor", 0.85)

        self.logger.info("[MetaLayer] Initialized meta optimizer.")

    # ======================================================================
    # PERFORMANCE UPDATE
    # ======================================================================
    def update_performance(self, engine_name, result, ev):
        """
        result: 1 vagy 0
        ev: expected value (float)
        """

        p = self.performance[engine_name]
        p["samples"] += 1
        p["ev_total"] += ev

        if result == 1:
            p["wins"] += 1
        else:
            p["losses"] += 1

        # Variance becslés (nagyon egyszerű)
        p["variance"] = abs(ev)  # EV alapú proxy

    # ======================================================================
    # ENGINE REWARD
    # ======================================================================
    def _engine_reward(self, engine_name):
        """Mennyire jó az engine teljesítménye?"""

        p = self.performance[engine_name]

        if p["samples"] < 10:
            return 0.5  # kevés adat → semleges

        winrate = p["wins"] / max(1, p["samples"])
        avg_ev = p["ev_total"] / max(1, p["samples"])
        variance = p["variance"]

        reward = (
            winrate * 0.5 +
            avg_ev * 0.4 +
            (1 - variance) * 0.1
        )

        return float(np.clip(reward, 0.01, 1.0))

    # ======================================================================
    # UPDATE GLOBAL WEIGHTS
    # ======================================================================
    def update_weights(self, engine_list):
        """
        engine_list: FusionEngine által listázott engine nevek
        """

        # Inicializálás
        for eng in engine_list:
            if eng not in self.weights:
                self.weights[eng] = 1 / len(engine_list)

        # Reward alapú módosítás
        for eng in engine_list:
            r = self._engine_reward(eng)
            self.weights[eng] = (
                self.weights[eng] * self.stability_factor +
                r * self.lr
            )

        self._normalize(self.weights)

    # ======================================================================
    # UPDATE LEAGUE-SPECIFIC WEIGHTS
    # ======================================================================
    def update_league_weights(self, league, engine_list):
        table = self.league_weights[league]

        # Inicializálás
        if not table:
            for eng in engine_list:
