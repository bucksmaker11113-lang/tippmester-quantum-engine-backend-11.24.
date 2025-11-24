# backend/core/kombi_engine.py

import itertools
import numpy as np
from backend.utils.logger import get_logger


class KombiEngine:
    """
    KOMBI ENGINE – PRO VERSION
    ---------------------------
    Feladata:
        • Kombinációk generálása a TipSelector jelöltjeiből
        • Odds-limit, risk-limit, correlation és value alapján optimalizál
        • Készít 2-es, 3-as, 4-es kombikat konfiguráció szerint
        • Value-optimalizált rangsor (TOP kombik)
    """

    def __init__(self, config=None):
        self.config = config or {}
        self.logger = get_logger()

        kombi_cfg = self.config.get("kombi", {})

        # Kombi méretek (pl.: [2,3])
        self.kombi_sizes = kombi_cfg.get("sizes", [2, 3])

        # Odds limit
        self.max_odds = kombi_cfg.get("max_odds", 10.0)

        # Risk limit
        self.max_risk = kombi_cfg.get("max_risk", 0.65)

        # Maximális visszaküldött kombik
        self.top_n = kombi_cfg.get("top_n", 5)

        self.logger.info(f"[KombiEngine] Initialized — sizes={self.kombi_sizes}")

    # ======================================================================
    # CORRELATION SCORE
    # ======================================================================
    def _correlation_score(self, tips):
        diffs = []
        for a, b in itertools.combinations(tips, 2):
            dp = abs(a["probability"] - b["probability"])
            dv = abs(a["value_score"] - b["value_score"])
            diffs.append(dp + dv)

        corr = np.mean(diffs) if diffs else 0.0

        # minél kisebb → annál nagyobb a correlation veszély
        normalized = max(0.0, 1.0 - corr)

        return float(normalized)

    # ======================================================================
    # KOMBI ÉRTÉKELÉSE
    # ======================================================================
    def _evaluate_kombi(self, combo):
        """
        combo: list[dict] (tippek)

        Számolja:
            - combined_probability (függetlenítés feltételezésével)
            - combined_odds (szorzat)
            - avg value_score
            - avg risk
            - correlation_score
            - final_score (ranking)
        """

        # ==========================
        # Combined probability
        # ==========================
        probs = [t["probability"] for t in combo]
        combined_prob = float(np.prod(probs))  # függetlenítés feltételezése

        # ==========================
        # Combined odds
        # ==========================
        odds = [t.get("odds", 2.0) for t in combo]
        combined_odds = float(np.prod(odds))

        # ==========================
        # Value
        # ==========================
        avg_value = float(np.mean([t.get("value_score", 0.0) for t in combo]))

        # ==========================
        # Risk
        # ==========================
        avg_risk = float(np.mean([t.get("risk", 0.5) for t in combo]))

        # ==========================
        # Correlation danger
        # ==========================
        corr = self._correlation_score(combo)

        # ==========================
        # Final score
        # ==========================
        final_score = (
            combined_prob * 0.25 +
            avg_value * 0.40 +
            corr * 0.20 +
            (1 - avg_risk) * 0.15
        )

        return {
            "tips": combo,
            "combined_probability": combined_prob,
            "combined_odds": combined_odds,
            "avg_value": avg_value,
            "avg_risk": avg_risk,
            "correlation": corr,
            "final_score": float(final_score)
        }

    # ======================================================================
    # MAIN FUNCTION
    # ======================================================================
    def generate_kombi(self, tips):
        """
        tips: list[dict]
            Pl. TipSelector output

        Visszatér:
            TOP N kombi ajánlás
        """

        if not tips or len(tips) < 2:
            self.logger.warning("[KombiEngine] Not enough tips for kombi.")
            return []

        all_combos = []

        for size in self.kombi_sizes:
            if len(tips) < size:
                continue

            for combo in itertools.combinations(tips, size):
                stats = self._evaluate_kombi(combo)

                # Odds filter
                if stats["combined_odds"] > self.max_odds:
                    continue

                # Risk filter
                if stats["avg_risk"] > self.max_risk:
                    continue

                all_combos.append(stats)

        if not all_combos:
            self.logger.warning("[KombiEngine] No valid kombi found.")
            return []

        # Rangsorolás
        ranked = sorted(all_combos, key=lambda x: x["final_score"], reverse=True)

        return ranked[: self.top_n]
