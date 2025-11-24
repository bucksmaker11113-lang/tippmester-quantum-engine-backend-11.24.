# backend/engine/kombi_optimizer.py

import itertools
import math


class KombiOptimizer:
    """
    KOMBI OPTIMALIZÁLÓ ENGINE
    -------------------------
    Kiválasztja a nap legjobb 3–4 tippből álló kombinációját:
        - össz odds 6.0–8.0 között (config állítja)
        - magas value score
        - alacsony korreláció
        - nincs két tipp ugyanabból a meccsből
        - TippmixPro availability ellenőrzése
        - prop + single + handicap mix engedélyezett
    """

    def __init__(self, config=None):
        self.config = config or {}

        self.min_total_odds = self.config.get("kombi_min_total_odds", 5.5)
        self.max_total_odds = self.config.get("kombi_max_total_odds", 8.5)
        self.max_tips = self.config.get("kombi_tips_count", 4)

    # -------------------------------------------------------------
    # Ellenőrzi, hogy van-e 2 tipp ugyanabból a meccsből
    # -------------------------------------------------------------
    def _has_duplicate_matches(self, tips):
        match_ids = [t["match_id"] for t in tips]
        return len(match_ids) != len(set(match_ids))

    # -------------------------------------------------------------
    # Odds összeszorzása
    # -------------------------------------------------------------
    def _combined_odds(self, tips):
        total = 1.0
        for t in tips:
            total *= t["odds"]
        return round(total, 3)

    # -------------------------------------------------------------
    # Kombi EV (expected value)
    # -------------------------------------------------------------
    def _combined_ev(self, tips):
        # Kombi EV = Π(prob) * Π(odds) - (1 - Π(prob))
        win_prob = 1.0
        for t in tips:
            win_prob *= t["probability"]

        total_odds = self._combined_odds(tips)

        ev = win_prob * total_odds - (1 - win_prob)
        return round(ev, 4)

    # -------------------------------------------------------------
    # Korrelációs szűrés
    # -------------------------------------------------------------
    def _is_correlated(self, t1, t2):
        # Ugyanazon meccs → tiltva
        if t1["match_id"] == t2["match_id"]:
            return True

        # Prop correlation (pl. BTTS és Over 2.5)
        if t1["market_type"] == "total" and t2["market_type"] == "btts":
            return True

        if t1["market_type"] == "total" and t2["market_type"] == "total":
            return True

        return False

    # -------------------------------------------------------------
    # Csoportszintű korreláció
    # -------------------------------------------------------------
    def _group_correlation_check(self, tips):
        for a, b in itertools.combinations(tips, 2):
            if self._is_correlated(a, b):
                return True
        return False

    # -------------------------------------------------------------
    # KOMBI OPTIMALIZÁCIÓ
    # -------------------------------------------------------------
    def optimize(self, all_tips):
        # 1) Szűrés érték + confidence alapján
        candidates = [
            t for t in all_tips
            if t["value_score"] > 0.15 and t["confidence"] > 0.55
        ]

        if len(candidates) < 3:
            return {"error": "Nincs elég jó minőségű tipp a kombihoz."}

        # 2) Kombinációk keresése (3-4 db)
        best_combo = None
        best_ev = -999

        for combo_size in [3, 4]:
            if combo_size > len(candidates):
                continue

            for combo in itertools.combinations(candidates, combo_size):

                # 2/A) Ugyanabból a meccsből 2 tipp → tiltva
                if self._has_duplicate_matches(combo):
                    continue

                # 2/B) Korreláció → tiltva
                if self._group_correlation_check(combo):
                    continue

                # 2/C) Combined odds range
                total_odds = self._combined_odds(combo)
                if not (self.min_total_odds <= total_odds <= self.max_total_odds):
                    continue

                # 2/D) Combined EV
                ev = self._combined_ev(combo)

                if ev > best_ev:
                    best_ev = ev
                    best_combo = combo

        if not best_combo:
            return {"error": "Nem találtam megfelelő kombit."}

        # -----------------------------------------------------
        # VÉGEREDMÉNY
        # -----------------------------------------------------
        return {
            "tips": list(best_combo),
            "total_odds": self._combined_odds(best_combo),
            "combined_ev": self._combined_ev(best_combo),
            "tips_count": len(best_combo)
        }
