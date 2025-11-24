# backend/engine/live_engine.py

import numpy as np
from backend.utils.logger import get_logger

class LiveEngine:
    """
    LIVE ENGINE – REAL-TIME ANALYSIS
    --------------------------------
    Elemzi:
        - momentum
        - xG soránynomat
        - pressing indexet
        - event rhythm
        - dangerous attack clusters
        - next event prediction
    """

    def __init__(self, config=None):
        self.config = config or {}
        self.logger = get_logger()

    # -----------------------------------------------------------
    # PUBLIC INTERFACE
    # -----------------------------------------------------------
    def analyze_live_state(self, match_data):
        """
        match_data formátum:
            {
                "attacks_home": int,
                "attacks_away": int,
                "dangerous_home": int,
                "dangerous_away": int,
                "shots_home": int,
                "shots_away": int,
                "possession_home": float,
                "possession_away": float,
                "time": int,
                ...
            }
        """

        momentum = self._momentum(match_data)
        xg = self._live_xg(match_data)
        events = self._next_event_prob(match_data)

        final_score = (
            0.4 * momentum +
            0.4 * xg +
            0.2 * events
        )

        final_score = max(0.0, min(1.0, final_score))

        return {
            "game_chance": round(final_score, 4),
            "momentum": round(momentum, 3),
            "live_xg": round(xg, 3),
            "event_predict": events,
            "source": "LiveEngine"
        }

    # -----------------------------------------------------------
    # MOMENTUM INDEX
    # -----------------------------------------------------------
    def _momentum(self, d):
        """
        Momentum = veszélyes támadások + labdabirtoklás súlyozása
        """
        danger_home = d.get("dangerous_home", 0)
        danger_away = d.get("dangerous_away", 0)

        poss_home = d.get("possession_home", 50)

        # veszély + passzív nyomás
        mom = (danger_home - danger_away) * 0.02 + (poss_home - 50) * 0.01
        mom = 1 / (1 + np.exp(-mom))       # sigmoid
        return mom

    # -----------------------------------------------------------
    # LIVE xG INDEX
    # -----------------------------------------------------------
    def _live_xg(self, d):
        shots = d.get("shots_home", 0)
        danger = d.get("dangerous_home", 0)

        xg = 0.03 * shots + 0.015 * danger
        xg = min(1.0, xg)
        return xg

    # -----------------------------------------------------------
    # NEXT EVENT PREDICTOR
    # -----------------------------------------------------------
    def _next_event_prob(self, d):
        attacks = d.get("attacks_home", 0)
        danger = d.get("dangerous_home", 0)

        shot_prob = min(1.0, 0.02 * attacks + 0.03 * danger)
        corner_prob = min(1.0, 0.01 * attacks)
        foul_prob = min(1.0, 0.005 * (attacks + danger))

        return {
            "shot": round(shot_prob, 3),
            "corner": round(corner_prob, 3),
            "foul": round(foul_prob, 3)
        }
