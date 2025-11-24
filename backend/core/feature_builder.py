# backend/engine/feature_builder.py
# Profi Feature Builder – modellezés előtt minden adatot normalizál
# A kvant sportfogadási modellek egyik legfontosabb eleme
# - Odds logit transzformáció
# - Gólvárható érték normalizálás
# - Formamutatók skálázása
# - Statisztikai feature pipeline

import numpy as np

class FeatureBuilder:
    def __init__(self):
        pass

    def build(self, match_data: dict) -> dict:
        """
        Meccsadatokból model input feature készítése.
        """
        features = {}

        # --- Odds logit transform (kvant standard) ---
        if "odds_home" in match_data:
            features["logit_home"] = self._logit_odds(match_data["odds_home"])
        if "odds_draw" in match_data:
            features["logit_draw"] = self._logit_odds(match_data["odds_draw"])
        if "odds_away" in match_data:
            features["logit_away"] = self._logit_odds(match_data["odds_away"])

        # --- Gólvárható érték ---
        if "xg_home" in match_data:
            features["xg_home"] = float(match_data["xg_home"])
        if "xg_away" in match_data:
            features["xg_away"] = float(match_data["xg_away"])

        # --- Formamutatók normalizálása ---
        if "form_home" in match_data:
            features["form_home_norm"] = self._normalize(match_data["form_home"], 0, 100)
        if "form_away" in match_data:
            features["form_away_norm"] = self._normalize(match_data["form_away"], 0, 100)

        # --- Team strength ---
        if "home_strength" in match_data:
            features["home_strength"] = float(match_data["home_strength"]) / 100
        if "away_strength" in match_data:
            features["away_strength"] = float(match_data["away_strength"]) / 100

        # --- Over/Under implicit probabilities ---
        if "over25_odds" in match_data:
            features["over25_prob"] = 1 / float(match_data["over25_odds"])
        if "under25_odds" in match_data:
            features["under25_prob"] = 1 / float(match_data["under25_odds"])

        return features

    # -------------------- SEGÉDFÜGGVÉNYEK --------------------

    def _logit_odds(self, odds: float) -> float:
        """
        Odds logit transzformáció (piaci hatékonysághoz szükséges)
        logit(p) = log(p / (1 - p))
        p = 1 / odds (fair approx)
        """
        p = max(1 / float(odds), 1e-6)
        p = min(p, 1 - 1e-6)
        return float(np.log(p / (1 - p)))

    def _normalize(self, value, min_val, max_val):
        value = float(value)
        return (value - min_val) / (max_val - min_val + 1e-6)

    # -----------------------------------------------------------

    def build_training_dataset(self, dataset: list):
        """
        Edzési dataset előkészítése modellekhez.
        """
        X = []
        y = []
        for record in dataset:
            features = self.build(record)
            X.append(list(features.values()))
            y.append(record.get("label", 0))
        return X, y
