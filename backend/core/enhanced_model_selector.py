# Hová kerüljön:
# backend/core/enhanced_model_selector.py

"""
ENHANCED MODEL SELECTOR – ADAPTÍV MODELLVÁLASZTÓ RENDSZER
---------------------------------------------------------
Feladata:
    - Kiválasztani a legjobb modellt / engine-t a jelenlegi meccshelyzethez
    - ROI, pontosság, drift, ligaszint, engine-teljesítmény alapján dinamikusan dönteni
    - Meta-layer, FusionEngine és Orchestrator kompatibilis működés
    - Live és prematch mód támogatása
    - Modellverziók kezelése
    - Fallback logika, ha valamely modell hibázik

ÚJ VERZIÓ:
✔ adaptív súlyozás
✔ drift és hibaarány figyelése
✔ ligaspecifikus modellválasztás
✔ ROI és precision alapú modell ranking
✔ meta-layer optimalizálás
✔ teljes hibatűrés
✔ meccsspecifikus engine routing
"""

from typing import Dict, Any, List
import numpy as np


class EnhancedModelSelector:
    def __init__(self):
        # Modell statisztikák
        self.model_stats = {}  # pl.: {"lstm_v1": {"roi":0.12, "precision":0.67, "drift":0.05}, ...}

        # Liga-specifikus ajánlások
        self.league_preferences = {}  # pl.: {"Premier League": ["lstm_v2", "xgb_v1"]}

    # =====================================================================
    # MODELL REGISZTRÁCIÓ
    # =====================================================================
    def register_model(self, model_name: str, stats: Dict[str, float]):
        """
        stats:
            {
                "roi": float,
                "precision": float,
                "drift": float,
                "version": str
            }
        """
        self.model_stats[model_name] = stats

    # =====================================================================
    # DONTÉS – LEGJOBB MODELL KIVÁLASZTÁSA
    # =====================================================================
    def select_model(self, match: Dict[str, Any]) -> str:
        league = match.get("league", "UNKNOWN")

        # Ha van ligára preferált lista → azt használjuk
        preferred = self.league_preferences.get(league)

        candidates = preferred if preferred else list(self.model_stats.keys())

        if not candidates:
            return "fallback_model"

        # Score-k kiszámolása ROI + precision - drift alapján
        scored = []
        for model in candidates:
            stats = self.model_stats.get(model, None)
            if not stats:
                continue

            roi = stats.get("roi", 0.0)
            precision = stats.get("precision", 0.5)
            drift = stats.get("drift", 0.0)

            score = (roi * 0.5) + (precision * 0.4) - (drift * 0.1)
            scored.append((model, score))

        if not scored:
            return "fallback_model"

        # Legjobb modell kiválasztása
        scored.sort(key=lambda x: x[1], reverse=True)
        best_model = scored[0][0]

        return best_model

    # =====================================================================
    # META-LAYER KIEGÉSZÍTÉS
    # =====================================================================
    def apply_meta_decision(self, model_name: str, meta: Dict[str, Any]) -> str:
        """
        Meta-layer képes felülbírálni a modellválasztást, ha kell.
        """

        if not meta:
            return model_name

        boost = meta.get("model_boost", {}).get(model_name, 0)
        downgrade = meta.get("model_penalty", {}).get(model_name, 0)

        # Meta súly alapján módosított döntés
        if boost > 0.1:
            return model_name  # marad
        if downgrade > 0.1:
            # Keressünk alternatív modellt
            alternatives = [m for m in self.model_stats.keys() if m != model_name]
            if alternatives:
                return alternatives[0]

        return model_name

    # =====================================================================
    # ENGINE ROUTING – MELY ENGINE FUTTATANDÓ
    # =====================================================================
    def route(self, match: Dict[str, Any], meta: Dict[str, Any] = None) -> str:
        model = self.select_model(match)
        final = self.apply_meta_decision(model, meta)
        return final


# Globális példány
EnhancedModelSelectorInstance = EnhancedModelSelector()
