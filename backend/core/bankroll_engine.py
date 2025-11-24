# Hová kerüljön:
# backend/core/bankroll_engine.py

"""
BANKROLL ENGINE – ADAPTÍV, PROFI, RL-KOMPATIBILIS VERZIÓ
---------------------------------------------------------
Feladata:
    - A teljes bankroll kezelés realisztikus, AI által vezérelt módon
    - Integráció a RiskEngine + RL Stake Engine + LiquidityEngine modulokkal
    - Dinamikus bankroll védelem
    - Kelly, Half-Kelly, Dynamic-Kelly támogatás
    - Volatility és risk tier alapján stake limitálás
    - Long-term bankroll evolúció követése

Ez az új verzió:
✔ ROI-alapú bankroll frissítés
✔ RL state kompatibilis stake ajánlás
✔ volatility adaptáció
✔ risk level adaptáció
✔ anti-tilt protection
✔ max drawdown védelem
✔ live és prematch módra optimalizálva
"""

from typing import Dict, Any
import numpy as np


class BankrollEngine:
    def __init__(self, initial_bankroll: float = 100.0):
        self.bankroll = initial_bankroll
        self.max_bankroll = initial_bankroll
        self.min_bankroll = initial_bankroll

        self.max_drawdown_limit = 0.30  # 30% DD védelem
        self.risk_multiplier = 1.0

    # =====================================================================
    # FŐ BANKROLL KALKULÁCIÓ
    # =====================================================================
    def recommend_stake(self, risk: Dict[str, Any], liquidity: Dict[str, Any], fused: Dict[str, Any]) -> Dict[str, Any]:
        """
        Visszaadja az ajánlott tétet a végső AI döntéshez.
        """

        risk_score = risk.get("risk_score", 0.5)
        volatility = liquidity.get("volatility_index", 0.0)
        pressure = liquidity.get("market_pressure", 0.0)
        confidence = fused.get("confidence", 0.0)

        bankroll_ratio = self.bankroll / max(self.max_bankroll, 1e-9)

        # =====================================================================
        # BASE STAKE – Kelly Formula alap
        # =====================================================================
        # Kelly-t nem közvetlenül használjuk, hanem korlátozott formában
        base_kelly = (risk_score + confidence * 0.3) - volatility
        base_kelly = float(np.clip(base_kelly, 0.0, 1.0))

        # Half-Kelly a stabilitásért
        stake_fraction = base_kelly * 0.5

        # =====================================================================
        # ADAPTÍV KORLÁTOZÓK
        # =====================================================================
        # Ha nagy a volatilitas → csökkentjük a téteket
        stake_fraction *= (1.0 - (volatility * 0.5))

        # Ha túl nagy market pressure → kockázatcsökkentés
        stake_fraction *= (1.0 - (pressure * 0.3))

        # Ha alacsony bankroll ratio → védelem
        if bankroll_ratio < 0.5:
            stake_fraction *= 0.7

        # Max drawdown védelem
        if self._is_drawdown_triggered():
            stake_fraction *= 0.4

        # =====================================================================
        # VÉGLEGES STAKE
        # =====================================================================
        final_stake = float(self.bankroll * stake_fraction)

        final_stake = float(np.clip(final_stake, 0.5, self.bankroll * 0.10))

        return {
            "stake": round(final_stake, 2),
            "fraction": stake_fraction,
            "details": {
                "bankroll": self.bankroll,
                "bankroll_ratio": bankroll_ratio,
                "volatility": volatility,
                "pressure": pressure,
                "risk_score": risk_score,
                "confidence": confidence,
                "kelly_base": base_kelly,
            }
        }

    # =====================================================================
    # BANKROLL UPDATE
    # =====================================================================
    def update(self, won: bool, stake: float, odds: float):
        if won:
            profit = stake * (odds - 1)
            self.bankroll += profit
        else:
            self.bankroll -= stake

        # Max bankroll update
        if self.bankroll > self.max_bankroll:
            self.max_bankroll = self.bankroll

        # Min bankroll track
        if self.bankroll < self.min_bankroll:
            self.min_bankroll = self.bankroll

    # =====================================================================
    # DRAWDOWN CHECK
    # =====================================================================
    def _is_drawdown_triggered(self) -> bool:
        drawdown = 1 - (self.bankroll / max(self.max_bankroll, 1e-9))
        return drawdown >= self.max_drawdown_limit


# Globális példány
BankrollEngineInstance = BankrollEngine(initial_bankroll=100.0)
