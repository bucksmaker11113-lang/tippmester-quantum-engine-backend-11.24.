# backend/engine/bias_engine.py
# Kvant sportfogadás – Bias korrekciós modul
# - Home/Away torzítás korrekció
# - Bookmaker margin (vig) felismerés
# - Model túl-/alulbecslés kiegyensúlyozása
# - CPU-light korrekció

class BiasEngine:
    def __init__(self, home_bias=0.03, away_bias=0.02):
        """
        home_bias: a hazai csapat túlértékelésének átlagos torzítása
        away_bias: idegen csapat alulértékelése
        """
        self.home_bias = home_bias
        self.away_bias = away_bias

    def correct(self, probabilities: dict, match_data: dict) -> dict:
        """
        Bemenet: 
        - probabilities = {"home": 0.55, "draw": 0.23, "away": 0.22}
        - match_data = {...}
        Kimenet: bias-korrigált valószínűségek.
        """

        home = probabilities.get("home", 0.0)
        draw = probabilities.get("draw", 0.0)
        away = probabilities.get("away", 0.0)

        # --- Home bias korrekció ---
        if match_data.get("home_team"):
            home = max(0.0, home - self.home_bias)

        # --- Away bias korrekció ---
        if match_data.get("away_team"):
            away = max(0.0, away - self.away_bias)

        # --- Normalizálás (szumma = 1.0) ---
        total = home + draw + away
        if total > 0:
            home /= total
            draw /= total
            away /= total

        return {
            "home": round(home, 4),
            "draw": round(draw, 4),
            "away": round(away, 4)
        }
