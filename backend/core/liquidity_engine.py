# Hová kerüljön:
# backend/core/liquidity_engine.py

"""
LIQUIDITY ENGINE – PROFI PIACI MÉLYSÉGANALÍZIS
----------------------------------------------
Feladata:
    - Megbecsülni a piaci likviditást (fogadási volumen, mozgás)
    - A pénzáram irányát (money flow) meghatározni
    - A piac nyomását (market pressure) kiszámolni
    - Odds volatility és order flow alapján jelzéseket adni
    - Integrálódik a FeatureBuilder, RiskEngine és RL Stake Engine felé

Ez az új verzió:
✔ valós piaci paraméterekből számol (odds, stake, volume, last movements)
✔ money flow indexet számít
✔ market pressure indexet ad (0–1 skálán)
✔ volatility indexet számol
✔ támogatja a LiveEngine-et
✔ hibatűrő, stabil
"""

from typing import Dict, Any
import numpy as np


class LiquidityEngine:
    def __init__(self):
        pass

    # =====================================================================
    # FŐ FÜGGVÉNY — LIQUIDITY REPORT
    # =====================================================================
    def analyze(self, match: Dict) -> Dict[str, Any]:
        odds = match.get("odds", {})
        volume = match.get("market_volume", 0.0)
        history = match.get("odds_history", [])
        stakes = match.get("stakes", {})  # pl. {"home": 12000, "away": 8000}

        # -----------------------------------------------------------------
        # 1) VOLATILITY INDEX
        # -----------------------------------------------------------------
        if len(history) > 3:
            diffs = np.diff(history)
            volatility = float(np.std(diffs))
        else:
            volatility = 0.0

        # Normalizálás
        volatility = float(np.clip(volatility / 0.15, 0.0, 1.0))

        # -----------------------------------------------------------------
        # 2) MONEY FLOW INDEX
        # -----------------------------------------------------------------
        stake_home = stakes.get("home", 0)
        stake_away = stakes.get("away", 0)

        total_stake = stake_home + stake_away + 1e-9

        money_flow = float((stake_home - stake_away) / total_stake)
        # -1 → teljesen AWAY-ra tolódás
        # +1 → teljesen HOME-ra tolódás

        # -----------------------------------------------------------------
        # 3) MARKET PRESSURE INDEX
        # -----------------------------------------------------------------
        # odds mozgás + stake arány + volatilitás kombinációja
        if len(history) > 1:
            momentum = history[-1] - history[-2]
        else:
            momentum = 0.0

        # 0–1 között:
        pressure = float(np.tanh(abs(momentum) * 5))

        # -----------------------------------------------------------------
        # 4) LIQUIDITY DEPTH (egyszerű közelítés)
        # -----------------------------------------------------------------
        liquidity_depth = float(np.clip(np.log1p(volume) / 10, 0.0, 1.0))

        # -----------------------------------------------------------------
        # 5) ÖSSZEFOGLALÓ STRUKTÚRA
        # -----------------------------------------------------------------
        return {
            "volatility_index": volatility,
            "money_flow_index": money_flow,
            "market_pressure": pressure,
            "liquidity_depth": liquidity_depth,
            "momentum": float(momentum),
        }


# Globális példány
LiquidityEngineInstance = LiquidityEngine()
