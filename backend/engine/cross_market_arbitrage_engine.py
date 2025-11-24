# backend/engine/cross_market_arbitrage_engine.py

import numpy as np
from backend.utils.logger import get_logger

class CrossMarketArbitrageEngine:
    """
    CROSS MARKET ARBITRAGE ENGINE – PRO EDITION
    --------------------------------------------
    Feladata:
        • Több fogadóiroda oddsainak összehasonlítása
        • Price mismatch keresés (value spot)
        • Arbitrage detektálás 1x2 és több kimeneten is
        • Margin hibák feltérképezése
        • Lassú irodák késlekedésének kihasználása
        • Risk-free arbitrage jelzése
    """

    def __init__(self, config):
        self.config = config
        self.logger = get_logger()

        # scaling a value/különbség számításhoz
        self.mismatch_scaling = config.get("cross_market", {}).get("mismatch_scaling", 0.20)
        self.arb_threshold = config.get("cross_market", {}).get("arb_threshold", 1.00)  # arbitrage when sum < 1.00

        # confidence
        self.min_conf = config.get("cross_market", {}).get("min_confidence", 0.60)

        # fallback
        self.fallback_prob = 0.55

    # ----------------------------------------------------------------------
    # PUBLIC: fő hívás
    # ----------------------------------------------------------------------
    def predict(self, match_data):
        outputs = {}

        for match_id, data in match_data.items():
            try:
                prob = self._arb_core(match_id, data)
            except Exception as e:
                self.logger.error(f"[CrossMarketARB] Hiba → fallback: {e}")
                prob = self.fallback_prob

            prob = float(max(0.01, min(0.99, prob)))
            conf = self._confidence(prob)
            risk = self._risk(prob, conf)

            outputs[match_id] = {
                "probability": round(prob, 4),
                "confidence": round(conf, 3),
                "risk": round(risk, 3),
                "meta": {"arb_engine": True},
                "source": "CrossMarketArb"
            }

        return outputs

    # ----------------------------------------------------------------------
    # MAGFÜGGVÉNY – arbitrage / mismatch detection
    # ----------------------------------------------------------------------
    def _arb_core(self, match_id, data):
        """
        Várt input (példa):
            {
                "markets": {
                    "1": { "pinnacle": 2.10, "bet365": 2.05, "bwin": 2.00 },
                    "X": { "pinnacle": 3.30, "bet365": 3.25, "bwin": 3.20 },
                    "2": { "pinnacle": 3.40, "bet365": 3.30, "bwin": 3.25 }
                }
            }
        """

        markets = data.get("markets", {})

        if not markets:
            return self.fallback_prob

        # 1) Implied probability összeg → arbitrage detektálás
        arb_sum = 0
        for outcome, prices in markets.items():
            best_odds = max(prices.values())
            arb_sum += 1 / best_odds

        # Arbitrage értékelése
        arb_detected = arb_sum < self.arb_threshold

        # 2) Mismatch erősség
        mismatch_score = self._calculate_mismatch(markets)

        # 3) Végső valószínűség
        if arb_detected:
            # Arb-spot → nagy value → 0.75-0.85 probability tartomány
            prob = 0.75 + mismatch_score * 0.15
        else:
            # Normál mismatch → 0.5 ± eltérés
            prob = 0.5 + mismatch_score * self.mismatch_scaling

        return float(prob)

    # ----------------------------------------------------------------------
    # PIACI MISMATCH SZÁMÍTÁS
    # ----------------------------------------------------------------------
    def _calculate_mismatch(self, markets):
        diffs = []

        for outcome, prices in markets.items():
            # irodák szerinti max és min oddsok különbsége
            odds_values = list(prices.values())
            diff = max(odds_values) - min(odds_values)
            diffs.append(diff)

        if not diffs:
            return 0

        # Normalizálás 0.0 – 0.5 tartományra
        mismatch_score = min(0.5, np.mean(diffs) / 5.0)
        return mismatch_score

    # ----------------------------------------------------------------------
    # CONFIDENCE
    # ----------------------------------------------------------------------
    def _confidence(self, prob):
        stability = 1 - abs(prob - 0.5)
        conf = max(self.min_conf, min(1.0, stability))
        return float(conf)

    # ----------------------------------------------------------------------
    # RISK
    # ----------------------------------------------------------------------
    def _risk(self, prob, conf):
        # arbitrage esetén nagyon alacsony risk
        if prob >= 0.75:
            return 0.10

        return float(min(1.0, max(0.0,
            (1 - prob) * 0.5 + (1 - conf) * 0.5
        )))
