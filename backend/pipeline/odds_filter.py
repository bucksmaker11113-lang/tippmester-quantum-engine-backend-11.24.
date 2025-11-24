# Hová kerüljön:
# backend/pipeline/odds_filter.py

"""
ODDS FILTER – ÚJ GENERÁCIÓS ODDS NORMALIZÁLÓ ÉS PIACI ZAJCSÖKKENTŐ RÉTEG
-------------------------------------------------------------------------
Feladata:
    - odds adatok tisztítása, normalizálása és korrekciója
    - piaci torzulások, manipulált oddsok kiszűrése
    - extrém értékek eltávolítása
    - liquidity + volatility + momentum figyelembevétele
    - frontend és AI motorok számára stabil odds input biztosítása

Ez az új verzió:
✔ LiquidityEngine integráció
✔ momentum alapú korrekció
✔ volatilitás-érzékeny odds scaling
✔ extrém érték detectálás és kiszűrés
✔ zárt kimeneti forma (safe_odds)
✔ MasterOrchestrator és FusionEngine kompatibilitás
"""

from typing import Dict, Any
import numpy as np

from core.liquidity_engine import LiquidityEngineInstance


class OddsFilter:
    def __init__(self):
        pass

    # =====================================================================
    # FŐ FUNKCIÓ – ODDS TISZTÍTÁS ÉS NORMALIZÁLÁS
    # =====================================================================
    def filter_odds(self, match: Dict[str, Any]) -> Dict[str, Any]:
        odds = match.get("odds", {})

        # hiányzó oddsok kezelése
        home = float(odds.get("home", 0)) or 0.0
        draw = float(odds.get("draw", 0)) or 0.0
        away = float(odds.get("away", 0)) or 0.0

        # liquidity alapú piaci állapot elemzése
        liquidity = LiquidityEngineInstance.analyze(match)
        volatility = liquidity.get("volatility_index", 0.0)
        momentum = liquidity.get("momentum", 0.0)

        # =====================================================================
        # 1) Extrém érték detektálása
        # =====================================================================
        def is_extreme(x: float) -> bool:
            return x <= 1.05 or x > 25

        if is_extreme(home): home = 0
        if is_extreme(draw): draw = 0
        if is_extreme(away): away = 0

        # =====================================================================
        # 2) Odds normalizálása – túl nagy különbségek kisimítása
        # =====================================================================
        def normalize(x: float) -> float:
            if x <= 1: return 1
            return float(np.clip(x, 1.01, 15.0))

        home = normalize(home)
        draw = normalize(draw)
        away = normalize(away)

        # =====================================================================
        # 3) Volatility alapú scaling
        # =====================================================================
        scale_factor = 1 + (volatility * 0.15)

        home *= scale_factor
        draw *= scale_factor
        away *= scale_factor

        # =====================================================================
        # 4) Momentum alapú odds shifting
        # =====================================================================
        # Ha momentum < 0 → odds esik → value erősödik
        # Ha momentum > 0 → odds nő → value gyengül

        shift = np.clip(momentum * 0.05, -0.1, 0.1)

        home *= (1 - shift)
        draw *= (1 - shift)
        away *= (1 - shift)

        # =====================================================================
        # 5) Biztonságos (safe) odds létrehozása
        # =====================================================================
        safe_odds = {
            "home": round(home, 3),
            "draw": round(draw, 3),
            "away": round(away, 3)
        }

        return {
            "safe_odds": safe_odds,
            "volatility": volatility,
            "momentum": momentum
        }


# Globális példány
OddsFilterInstance = OddsFilter()
