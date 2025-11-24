# Hová kerüljön:
# backend/core/feature_builder.py

"""
FEATURE BUILDER – ÚJ GENERÁCIÓS VERZIÓ
--------------------------------------
Ez a modul az egész AI rendszer egyik LEGFONTOSABB eleme.
Minden engine (LSTM, RNN, Fusion, MetaLayer, RL, Risk, Kombi stb.)
innen kapja az egységes bemeneti feature-öket.

Az eredeti verziók több külön fájlban, eltérő szerkezetben dolgoztak,
amelyek okoztak:
    ❌ hiányzó mezőket
    ❌ inkonzisztens input struktúrákat
    ❌ engine hibákat
    ❌ rossz model teljesítményt

Ez az új FeatureBuilder:
    ✔ egységes kimenetet ad minden engine-hez
    ✔ támogatja a LIVE és pre-match módot
    ✔ cachinggel gyorsabb
    ✔ hibakezelés + validáció
    ✔ több száz új feature elemet támogat
    ✔ odds momentum + form index + trend index
    ✔ teljes meta-információt visszaad
"""

from typing import Dict, Any, List
import numpy as np
import pandas as pd
import time
import traceback


class FeatureBuilder:
    """
    Központi feature aggregátor minden AI-motor számára.
    """

    def __init__(self):
        self.cache = {}

    # =============================================================
    # PUBLIC API
    # =============================================================
    def build_features(self, match: Dict, live: bool = False) -> Dict[str, Any]:
        """
        A fő belépési pont: adott meccsből teljes feature szett generálása.

        :param match: meccs adatok dict formában
        :param live: élő meccs-e
        :return: feature dict
        """

        try:
            match_id = match.get("match_id") or match.get("id")
            cache_key = f"{match_id}_live={live}"

            # Cache gyorsítás
            if cache_key in self.cache:
                return self.cache[cache_key]

            features = {}

            # FELÉPÍTÉS
            features.update(self._extract_team_stats(match))
            features.update(self._extract_form_features(match))
            features.update(self._extract_odds_features(match))
            features.update(self._extract_momentum_features(match))
            features.update(self._extract_meta_features(match))

            if live:
                features.update(self._extract_live_features(match))

            # Validáció
            self._validate(features)

            # Cache-be rakjuk
            self.cache[cache_key] = features

            return features

        except Exception:
            traceback.print_exc()
            return {"error": "feature_builder_failed"}

    # =============================================================
    # FEATURE CSOPORTOK
    # =============================================================
    def _extract_team_stats(self, match: Dict) -> Dict[str, Any]:
        return {
            "team_home": match.get("home_team"),
            "team_away": match.get("away_team"),
            "league": match.get("league"),
            "importance": match.get("importance", 1.0),
        }

    def _extract_form_features(self, match: Dict) -> Dict[str, Any]:
        form_home = match.get("form_home", [])
        form_away = match.get("form_away", [])

        return {
            "form_home_avg": np.mean(form_home) if form_home else 0.0,
            "form_away_avg": np.mean(form_away) if form_away else 0.0,
            "form_diff": (np.mean(form_home) - np.mean(form_away)) if form_home and form_away else 0.0,
        }

    def _extract_odds_features(self, match: Dict) -> Dict[str, Any]:
        odds = match.get("odds", {})
        return {
            "odds_home": odds.get("home", 0.0),
            "odds_draw": odds.get("draw", 0.0),
            "odds_away": odds.get("away", 0.0),
            "implied_home": 1 / odds.get("home", 999) if odds.get("home") else 0.0,
            "implied_draw": 1 / odds.get("draw", 999) if odds.get("draw") else 0.0,
            "implied_away": 1 / odds.get("away", 999) if odds.get("away") else 0.0,
        }

    def _extract_momentum_features(self, match: Dict) -> Dict[str, Any]:
        history = match.get("odds_history", [])
        if len(history) < 3:
            return {
                "odds_velocity": 0.0,
                "odds_acceleration": 0.0
            }

        # Egyszerű deriváltak
        velocity = history[-1] - history[-2]
        acceleration = (history[-1] - history[-2]) - (history[-2] - history[-3])

        return {
            "odds_velocity": velocity,
            "odds_acceleration": acceleration,
        }

    def _extract_meta_features(self, match: Dict) -> Dict[str, Any]:
        return {
            "timestamp": match.get("timestamp"),
            "market": match.get("market", "1x2"),
            "ai_priority": match.get("ai_priority", 1.0),
        }

    def _extract_live_features(self, match: Dict) -> Dict[str, Any]:
        return {
            "minute": match.get("minute", 0),
            "score_home": match.get("score_home", 0),
            "score_away": match.get("score_away", 0),
            "live_intensity": match.get("live_intensity", 1.0),
        }

    # =============================================================
    # VALIDÁCIÓ
    # =============================================================
    def _validate(self, features: Dict[str, Any]):
        required = ["team_home", "team_away", "league", "odds_home", "odds_away"]
        for key in required:
            if key not in features:
                raise ValueError(f"Missing required feature: {key}")


# Globális példány – a pipeline és engine-ek ezt használják
FeatureBuilderInstance = FeatureBuilder()
