# backend/engine/sharp_money_tracker.py

import numpy as np
import math
import statistics


class SharpMoneyTracker:
    """
    SHARP MONEY TRACKER ENGINE
    ---------------------------
    Feladata:
        - oddsmozgások elemzése
        - sharp vs public pénz szétválasztása
        - manipulált piac detektálása
        - várható odds drift erősségének becslése
        - momentum detection
        - integráció a CLV Engine-nel és Value Engine-ekkel
    """

    def __init__(self, config=None):
        self.config = config or {}

        # sharp money threshold beállítások
        self.sharp_speed_threshold = 0.015      # % esés gyorsaság alapján
        self.sharp_volume_threshold = 0.020     # odds-változás súlyossága
        self.public_noise_limit = 0.010         # random közpénzes zaj

    # --------------------------------------------------------
    # Trend irányának felismerése
    # --------------------------------------------------------
    def detect_direction(self, odds_history):
        if len(odds_history) < 3:
            return "neutral"

        if odds_history[-1] < odds_history[-2] < odds_history[-3]:
            return "strong_down"

        if odds_history[-1] > odds_history[-2] > odds_history[-3]:
            return "strong_up"

        return "mixed"

    # --------------------------------------------------------
    # Sharp pénz erősségének becslése
    # --------------------------------------------------------
    def sharp_strength(self, odds_history):
        """
        Nézi:
            - esés gyorsasága
            - esés mértéke
            - volatilitás
        """

        if len(odds_history) < 3:
            return 0.0

        diffs = np.diff(odds_history)
        speed = abs(diffs[-1])
        total_move = abs(odds_history[-1] - odds_history[0])

        vol = statistics.pvariance(odds_history)

        # sharp pénz = gyors + jelentős esés + alacsony volatilitás
        score = (
            (speed > self.sharp_speed_threshold) +
            (total_move > self.sharp_volume_threshold) +
            (vol < 0.003)  # ha alacsony, akkor nem “public noise”
        )

        return round(score / 3, 3)

    # --------------------------------------------------------
    # Public money (közönségpénz) zaj detektálása
    # --------------------------------------------------------
    def public_noise(self, odds_history):
        if len(odds_history) < 3:
            return 0.0

        diffs = np.diff(odds_history)
        mean_diff = np.mean(np.abs(diffs))

        if mean_diff < self.public_noise_limit:
            return 0.0

        return float(min(1.0, mean_diff / 0.05))

    # --------------------------------------------------------
    # Manipulált piac detektálása
    # --------------------------------------------------------
    def is_manipulated(self, odds_history):
        """
        Ha túl nagy, túl gyors opposit mozgatás van:
            pl. 1.80 → 1.75 → 1.85 → 1.70
        Ez gyakran "fake money" illetve odds manipuláció.
        """
        if len(odds_history) < 4:
            return False

        diffs = np.diff(odds_history)

        # először gyors esés → majd hirtelen emelkedés → majd újra esés
        pattern = (
            (diffs[0] < -0.02) and
            (diffs[1] >  0.02) and
            (diffs[2] < -0.02)
        )

        return pattern

    # --------------------------------------------------------
    # FŐ FUNKCIÓ: SHARP MONEY ANALYSIS
    # --------------------------------------------------------
    def analyze(self, odds_history):
        """
        Return:
            {
                "direction": "strong_down",
                "sharp_strength": 0.67,
                "public_noise": 0.12,
                "manipulated": False,
                "momentum": -0.021
            }
        """

        direction = self.detect_direction(odds_history)
        sharp_score = self.sharp_strength(odds_history)
        noise = self.public_noise(odds_history)
        manipulated = self.is_manipulated(odds_history)

        # momentum → az utolsó 3 diff átlaga
        if len(odds_history) > 3:
            last_diffs = np.diff(odds_history[-3:])
            momentum = float(np.mean(last_diffs))
        else:
            momentum = 0.0

        return {
            "direction": direction,
            "sharp_strength": sharp_score,
            "public_noise": round(noise, 3),
            "manipulated": manipulated,
            "momentum": round(momentum, 4)
        }
