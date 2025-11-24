# backend/analysis/historical_roi_analyzer.py

import os
import json
import datetime
import numpy as np


class HistoricalROIAnalyzer:
    """
    HISTORICAL ROI ANALYZER (HRA Engine)
    -----------------------------------
    Feladata:
        - Tipp-történet tárolás (DB vagy JSON)
        - Engine teljesítmények elemzése (MC3, LSTM, GNN, PropEngine stb.)
        - Piac ROI elemzés (1X2, totals, handicap, props)
        - Kombinált ROI idősoron
        - Hot/Cool streak és volatilitás mérése
        - Sharpe ratio számítás
        - Adat export frontend grafikonokhoz
    """

    def __init__(self, config=None):
        self.config = config or {}

        self.data_path = "backend/data/history/roi_history.json"
        os.makedirs("backend/data/history", exist_ok=True)

        if not os.path.exists(self.data_path):
            with open(self.data_path, "w") as f:
                json.dump({"history": []}, f, indent=4)

    # -----------------------------------------------------------
    # Adat betöltés
    # -----------------------------------------------------------
    def load_history(self):
        with open(self.data_path, "r") as f:
            return json.load(f).get("history", [])

    # -----------------------------------------------------------
    # Adat mentés
    # -----------------------------------------------------------
    def save_history(self, history):
        with open(self.data_path, "w") as f:
            json.dump({"history": history}, f, indent=4)

    # -----------------------------------------------------------
    # Napi eredmény rögzítése
    # -----------------------------------------------------------
    def record_day(self, date, bankroll_start, bankroll_end, tips):
        history = self.load_history()

        roi = (bankroll_end - bankroll_start) / bankroll_start

        history.append({
            "date": date,
            "bankroll_start": bankroll_start,
            "bankroll_end": bankroll_end,
            "roi": round(roi, 4),
            "tips": tips
        })

        self.save_history(history)

    # -----------------------------------------------------------
    # ROI idősor lekérése
    # -----------------------------------------------------------
    def get_roi_timeseries(self):
        history = self.load_history()
        return [day["roi"] for day in history]

    # -----------------------------------------------------------
    # ENGINE ROI elemzés
    # -----------------------------------------------------------
    def engine_roi(self):
        """
        Kiszámolja:
            {
                "MC3": 0.042,
                "LSTM": -0.012,
                "GNN": 0.018,
                "PropEngine": 0.055,
                ...
            }
        """

        history = self.load_history()
        engine_data = {}

        for day in history:
            for t in day["tips"]:
                engine = t.get("engine", "unknown")
                profit = t.get("profit", 0)
                stake = t.get("stake", 1)

                if engine not in engine_data:
                    engine_data[engine] = {"profit": 0, "stake": 0}

                engine_data[engine]["profit"] += profit
                engine_data[engine]["stake"] += stake

        # ROI számítás
        roi_out = {}
        for engine, d in engine_data.items():
            if d["stake"] > 0:
                roi_out[engine] = round(d["profit"] / d["stake"], 4)

        return roi_out

    # -----------------------------------------------------------
    # PIAC ROI elemzés
    # -----------------------------------------------------------
    def market_roi(self):
        """
        ROI piacok szerint:
            "1X2", "totals", "handicap", "btts", "cards", "corners", "player_props"
        """

        history = self.load_history()
        market_data = {}

        for day in history:
            for t in day["tips"]:
                m = t.get("market_category", "unk")

                if m not in market_data:
                    market_data[m] = {"profit": 0, "stake": 0}

                market_data[m]["profit"] += t.get("profit", 0)
                market_data[m]["stake"] += t.get("stake", 1)

        roi_out = {}
        for m, d in market_data.items():
            if d["stake"] > 0:
                roi_out[m] = round(d["profit"] / d["stake"], 4)

        return roi_out

    # -----------------------------------------------------------
    # VOLATILITY + SHARPE RATIO
    # -----------------------------------------------------------
    def volatility_and_sharpe(self):
        rois = self.get_roi_timeseries()
        if len(rois) < 2:
            return {"volatility": 0.0, "sharpe": 0.0}

        vol = float(np.std(rois))
        avg_roi = float(np.mean(rois))

        sharpe = avg_roi / vol if vol > 0 else 0.0

        return {
            "volatility": round(vol, 4),
            "sharpe": round(sharpe, 4)
        }

    # -----------------------------------------------------------
    # HOT / COLD streak detection
    # -----------------------------------------------------------
    def streaks(self):
        rois = self.get_roi_timeseries()

        if not rois:
            return {"hot_streak": 0, "cold_streak": 0}

        hot = 0
        cold = 0
        current = 0

        for r in rois:
            if r > 0:
                current += 1
                hot = max(hot, current)
            else:
                current = 0

        current = 0
        for r in rois:
            if r < 0:
                current += 1
                cold = max(cold, current)
            else:
                current = 0

        return {"hot_streak": hot, "cold_streak": cold}

    # -----------------------------------------------------------
    # FRONTEND export formátum
    # -----------------------------------------------------------
    def export_dashboard(self):
        return {
            "roi_timeseries": self.get_roi_timeseries(),
            "engine_roi": self.engine_roi(),
            "market_roi": self.market_roi(),
            "volatility": self.volatility_and_sharpe(),
            "streaks": self.streaks()
        }
