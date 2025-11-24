# backend/engine/prop_engine.py

import math

class PropEngine:
    """
    PROP ENGINE
    -----------
    Piac szintű value számítás:
        - Totals (O/U)
        - Handicap (AH)
        - BTTS
        - Cards
        - Corners
        - Player props
    """

    def __init__(self, config):
        self.config = config

    # -----------------------------------------------------------
    # FAIR VALUE számítás prop piacokra
    # -----------------------------------------------------------

    def _value(self, prob, odds):
        return prob * odds - (1 - prob)

    # Expected Goals alap modell (stub)
    def _expected_goals(self, team_stats):
        # később statisztika alapú modell
        return max(0.4, min(3.2, team_stats.get("xG", 1.4)))

    # Cards model (discipline)
    def _expected_cards(self, stats):
        return max(2.5, min(7.5, stats.get("cards_per_game", 4.2)))

    # Corners model
    def _expected_corners(self, stats):
        return max(6, min(14, stats.get("corners_per_game", 9.5)))

    # BTTS model
    def _btts_probability(self, home_xg, away_xg):
        # egyszerű multiplikatív modell
        return max(0.05, min(0.95, (home_xg * away_xg) / 3))

    # -----------------------------------------------------------
    # FŐ FÜGGVÉNY: prop value generálás
    # -----------------------------------------------------------
    def compute_prop_values(self, markets, model_stats):
        results = []

        home_xg = self._expected_goals(model_stats["home"])
        away_xg = self._expected_goals(model_stats["away"])

        # **********************
        # TOTALS → O/U 2.5, 3.5
        # **********************
        totals = markets["totals"]

        # Over 2.5 probability
        prob_over25 = max(0.05, min(0.95, (home_xg + away_xg) / 3.0))
        val_over25 = self._value(prob_over25, totals["over25"])

        results.append({
            "market": "Over 2.5",
            "type": "totals",
            "odds": totals["over25"],
            "prob": round(prob_over25, 3),
            "value": round(val_over25, 3)
        })

        # Under 2.5
        prob_under25 = 1 - prob_over25
        val_under25 = self._value(prob_under25, totals["under25"])

        results.append({
            "market": "Under 2.5",
            "type": "totals",
            "odds": totals["under25"],
            "prob": round(prob_under25, 3),
            "value": round(val_under25, 3)
        })

        # **********************
        # BTTS
        # **********************
        btts = markets["btts"]
        prob_btts = self._btts_probability(home_xg, away_xg)
        val_btts_yes = self._value(prob_btts, btts["yes"])

        results.append({
            "market": "BTTS Yes",
            "type": "btts",
            "odds": btts["yes"],
            "prob": round(prob_btts, 3),
            "value": round(val_btts_yes, 3)
        })

        # **********************
        # HANDICAP
        # **********************
        handicap = markets["handicap"]

        # Example: +1.5 handicp
        prob_plus15 = min(0.95, home_xg + 1.5 > away_xg)
        val_plus15 = self._value(prob_plus15, handicap["+1.5"])

        results.append({
            "market": "Home +1.5",
            "type": "handicap",
            "odds": handicap["+1.5"],
            "prob": float(prob_plus15),
            "value": round(val_plus15, 3)
        })

        # **********************
        # CARDS
        # **********************
        cards = markets["cards"]
        expected_cards = self._expected_cards(model_stats["match"])

        prob_over45 = max(0.05, min(0.95, expected_cards / 5.0))
        val_cards = self._value(prob_over45, cards["over45"])

        results.append({
            "market": "Cards Over 4.5",
            "type": "cards",
            "odds": cards["over45"],
            "prob": round(prob_over45, 3),
            "value": round(val_cards, 3)
        })

        return results
