# backend/engine/trend_engine.py

import numpy as np
from backend.utils.logger import get_logger


class TrendEngine:
    """
    TREND ENGINE – PRO EDITION
    ---------------------------
    Feladata:
        • csapatformák elemzése (win/loss, goal diff)
        • xG trend stabilitás
        • goal trend (scored/conceded)
        • over/under trend
        • streak-ek hatása (win streak, scoring streak)
        • pace trend (liga tempó)
        • regressziós stabilizáció
        • trend-alapú win probability
    """

    def __init__(self, config=None):
        self.config = config or {}
        self.logger = get_logger()

        c = self.config.get("trend", {})

        self.form_weight = c.get("form_weight", 0.30)
        self.goal_weight = c.get("goal_weight", 0.20)
        self.xg_weight = c.get("xg_weight", 0.25)
        self.streak_weight = c.get("streak_weight", 0.15)
        self.pace_weight = c.get("pace_weight", 0.10)

        self.min_conf = 0.55

    # ------------------------------------------------------------------
    #  FORM TREND: last N match results (win:1, draw:0.5, loss:0)
    # ------------------------------------------------------------------
    def _form_trend(self, results):
        """
        results = ["W","W","D","L","W"]
        """
        if not results:
            return 0.5

        mapping = {"W": 1.0, "D": 0.5, "L": 0.0}
        vals = [mapping.get(r, 0.5) for r in results]

        return float(np.mean(vals))

    # ------------------------------------------------------------------
    # GOAL TREND: scored-conceded normalized
    # ------------------------------------------------------------------
    def _goal_trend(self, goals_for, goals_against):
        try:
            if len(goals_for) == 0:
                return 0.5

            diff = np.array(goals_for) - np.array(goals_against)
            scaled = np.tanh(np.mean(diff) / 2.5)  # normalize
            return 0.5 + scaled * 0.5
        except:
            return 0.5

    # ------------------------------------------------------------------
    # xG TREND: stability over last games
    # ------------------------------------------------------------------
    def _xg_trend(self, xg_for, xg_against):
        if len(xg_for) < 2:
            return 0.5

        # net xG
        net = np.array(xg_for) - np.array(xg_against)

        # trend slope
        try:
            slope = np.polyfit(range(len(net)), net, 1)[0]
            slope_score = np.tanh(slope * 2)
            return 0.5 + slope_score * 0.5
        except:
            return 0.5

    # ------------------------------------------------------------------
    # STREAK TREND
    # ------------------------------------------------------------------
    def _streak(self, results):
        """
        W-streak = pozitív
        L-streak = negatív
        Draw = semleges
        """
        if not results:
            return 0.5

        streak_value = 0
        for r in reversed(results):
            if r == "W":
                streak_value += 1
            elif r == "L":
                streak_value -= 1
            else:
                break

        return 0.5 + np.tanh(streak_value / 4) * 0.5

    # ------------------------------------------------------------------
    # PACE TREND: league tempo (shots + xG + transitions)
    # ------------------------------------------------------------------
    def _pace(self, pace_history):
        if not pace_history:
            return 0.5

        pace_val = np.mean(pace_history)
        return float(np.clip(pace_val, 0.3, 0.7))

    # ------------------------------------------------------------------
    # FŐ TREND ANALÍZIS
    # ------------------------------------------------------------------
    def analyze(self, data):
        """
        data = {
            "form": ["W","D","W","L","W"],
            "goals_for": [2,1,3,0,2],
            "goals_against": [1,1,0,2,1],
            "xg_for": [...],
            "xg_against": [...],
            "pace": [0.52,0.54,0.56,0.55],
            "data_quality": 0.82
        }
        """

        form_score = self._form_trend(data.get("form", []))
        goal_score = self._goal_trend(
            data.get("goals_for", []),
            data.get("goals_against", [])
        )
        xg_score = self._xg_trend(
            data.get("xg_for", []),
            data.get("xg_against", [])
        )
        streak_score = self._streak(data.get("form", []))
        pace_score = self._pace(data.get("pace", []))

        # weighted probability
        prob = (
            form_score * self.form_weight +
            goal_score * self.goal_weight +
            xg_score * self.xg_weight +
            streak_score * self.streak_weight +
            pace_score * self.pace_weight
        )

        prob = float(np.clip(prob, 0.05, 0.95))

        confidence = self._confidence(prob, data)
        risk = self._risk(prob, confidence)

        return {
            "trend_probability": round(prob, 4),
            "form": form_score,
            "goal_trend": goal_score,
            "xg_trend": xg_score,
            "streak": streak_score,
            "pace": pace_score,
            "confidence": round(confidence, 3),
            "risk": round(risk, 3)
        }

    # ------------------------------------------------------------------
    # CONFIDENCE
    # ------------------------------------------------------------------
    def _confidence(self, prob, data):
        stability = 1 - abs(0.5 - prob)
        data_quality = data.get("data_quality", 0.80)

        conf = stability * 0.4 + data_quality * 0.6
        return float(max(self.min_conf, min(1.0, conf)))

    # ------------------------------------------------------------------
    # RISK
    # ------------------------------------------------------------------
    def _risk(self, prob, conf):
        return float(min(1.0, max(0.0, (1 - prob) * 0.5 + (1 - conf) * 0.5)))
