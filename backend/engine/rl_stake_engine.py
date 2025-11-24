# backend/engine/rl_stake_engine.py

import numpy as np


class RLStakeEngine:
    """
    REINFORCEMENT LEARNING STAKE ENGINE
    -----------------------------------
    Feladata:
        - Minden tipphez optimális tét meghatározása
        - Kelly + RL kombináció
        - CLV és sharp pénz figyelembevétele
        - Hot / Cold streak alapján agresszivitás változtatás
        - Bankroll protect mód beépítése
        - Piaci stabilitás értékelése
    """

    def __init__(self, config=None):
        self.config = config or {}

        self.base_stake_pct = self.config.get("base_stake_pct", 0.01)   # 1%
        self.max_stake_pct = self.config.get("max_stake_pct", 0.05)    # 5%
        self.min_stake_pct = self.config.get("min_stake_pct", 0.003)   # 0.3%

        self.aggressive_factor = 1.4   # ha hot streak van
        self.protect_factor = 0.55     # ha cold streak van

    # --------------------------------------------------------
    # Simple Kelly formula
    # --------------------------------------------------------
    def _kelly(self, prob, odds):
        edge = prob * odds - (1 - prob)
        if odds <= 1.0:
            return 0
        k = (edge / (odds - 1))
        return max(0, k)

    # --------------------------------------------------------
    # RL reward function
    # --------------------------------------------------------
    def _reward(self, tip):
        """
        Reward a következőkből áll:
          + value_score (0–1)
          + CLV (–0.2 .. +0.3)
          + confidence (0–1)
          - risk (0–1)
        """

        val = tip.get("value_score", 0)
        clv = tip.get("clv", 0)
        conf = tip.get("confidence", 0)
        risk = tip.get("risk", 0)

        reward = (
            val * 0.40 +
            clv * 0.30 +
            conf * 0.20 -
            risk * 0.15
        )

        return round(reward, 4)

    # --------------------------------------------------------
    # Hot / Cold streak modifier
    # --------------------------------------------------------
    def _streak_modifier(self, streaks):
        hot = streaks.get("hot_streak", 0)
        cold = streaks.get("cold_streak", 0)

        if hot >= 4:
            return self.aggressive_factor
        if cold >= 3:
            return self.protect_factor

        return 1.0

    # --------------------------------------------------------
    # Piaci stabilitás (sharp money + volatility)
    # --------------------------------------------------------
    def _market_modifier(self, sharp_strength, volatility):
        if sharp_strength > 0.65:
            return 1.2   # erős sharp → nagyobb tét engedélyezett
        if volatility > 0.02:
            return 0.7   # instabil piac → csökkentés
        return 1.0

    # --------------------------------------------------------
    # FŐ FUNKCIÓ: RL+Kelly stake számítás
    # --------------------------------------------------------
    def compute_stake(self, bankroll, tip, streaks=None):
        prob = tip.get("probability", 0)
        odds = tip.get("odds", 1)
        clv = tip.get("clv", 0)
        sharp = tip.get("sharp_money", 0)
        vol = tip.get("volatility", 0)

        # 1) Kelly alap
        k = self._kelly(prob, odds)

        # 2) RL reward
        reward = self._reward(tip)

        # 3) streak modifier
        streak_mod = self._streak_modifier(streaks or {})

        # 4) market modifier
        market_mod = self._market_modifier(sharp, vol)

        # 5) final stake percent
        stake_pct = (
            self.base_stake_pct +
            (k * 0.5) +
            (reward * 0.3)
        )

        stake_pct = stake_pct * streak_mod * market_mod

        # clamp
        stake_pct = max(self.min_stake_pct, min(self.max_stake_pct, stake_pct))

        stake_amount = bankroll * stake_pct

        return {
            "stake_pct": round(stake_pct, 4),
            "stake_amount": round(stake_amount, 2),
            "kelly_raw": round(k, 4),
            "reward": reward,
            "streak_mod": streak_mod,
            "market_mod": market_mod
        }
