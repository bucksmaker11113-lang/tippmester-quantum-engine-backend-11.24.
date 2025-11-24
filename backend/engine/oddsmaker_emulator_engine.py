# backend/engine/oddsmaker_emulator_engine.py

import numpy as np
from backend.utils.logger import get_logger

class OddsmakerEmulatorEngine:
    """
    ODDSMAKER EMULATOR ENGINE – PRO EDITION
    ---------------------------------------
    Feladata:
        • Fogadóirodák odds-generátor algoritmusának AI emulációja
        • Bookmaker baseline model replikáció
        • Margin adaptáció előrejelzése
        • Expected odds from booki model
        • Value mismatch → saját probability vs booki implied probability
    """

    def __init__(self, config):
        self.config = config
        self.logger = get_logger()

        # scaling paraméterek
        self.margin_scaling = config.get("odds_emulator", {}).get("margin_scaling", 0.10)
        self.sharp_adjustment_scaling = config.get("odds_emulator", {}).get("sharp_adjustment_scaling", 0.20)
        self.volatility_scaling = config.get("odds_emulator", {}).get("volatility_scaling", 0.15)

        # fallback
        self.fallback_prob = 0.54
        self.min_conf = config.get("odds_emulator", {}).get("min_confidence", 0.58)

    # ----------------------------------------------------------------------
    # PUBLIC PREDICTION
    # ----------------------------------------------------------------------
    def predict(self, match_data):
        outputs = {}

        for match_id, data in match_data.items():

            try:
                prob = self._emulator_core(data)
            except Exception as e:
                self.logger.error(f"[OddsmakerEmulator] Hiba → fallback: {e}")
                prob = self.fallback_prob

            prob = float(max(0.01, min(0.99, prob)))
            conf = self._confidence(prob, data)
            risk = self._risk(prob, conf)

            outputs[match_id] = {
                "probability": round(prob, 4),
                "confidence": round(conf, 3),
                "risk": round(risk, 3),
                "meta": {
                    "margin_scaling": self.margin_scaling,
                    "sharp_adjustment_scaling": self.sharp_adjustment_scaling
                },
                "source": "OddsmakerEmulator"
            }

        return outputs

    # ----------------------------------------------------------------------
    # CORE: ODDSMAKER EMULATION LOGIC
    # ----------------------------------------------------------------------
    def _emulator_core(self, data):
        """
        Várt input:
            • odds_open
            • odds_now
            • book_margin
            • sharp_influx
            • market_volatility
            • hidden_margin_factor
        """

        # Bookmaker alapadatok
        odds_open = data.get("odds_open", 2.00)
        odds_now = data.get("odds_now", 2.00)
        margin = data.get("book_margin", 0.06)               # 6% margin
        hidden_margin = data.get("hidden_margin_factor", 0.01)
        volatility = data.get("market_volatility", 0.05)
        sharp_influx = data.get("sharp_influx", 0.50)        # 0–1

        # Bookmaker implied probability (valószínűség az odds alapján)
        implied_now = 1 / odds_now if odds_now > 0 else 0.5
        implied_open = 1 / odds_open if odds_open > 0 else 0.5

        # Margin hatás
        margin_effect = margin * self.margin_scaling
        hidden_effect = hidden_margin * (self.margin_scaling * 1.5)

        # Sharp money hatás (iroda ilyenkor korrigálja a modellt)
        sharp_effect = (sharp_influx - 0.5) * self.sharp_adjustment_scaling

        # Volatility → booki model drift
        volatility_effect = volatility * self.volatility_scaling

        # Combined offset
        book_adjustment = (
            margin_effect +
            hidden_effect +
            sharp_effect +
            volatility_effect
        )

        # Bookmaker AI által kalkulált probability
        book_model_prob = implied_now + book_adjustment

        # SAFE RANGE
        book_model_prob = float(max(0.01, min(0.99, book_model_prob)))

        return book_model_prob

    # ----------------------------------------------------------------------
    # CONFIDENCE
    # ----------------------------------------------------------------------
    def _confidence(self, prob, data):
        model_quality = data.get("odds_data_quality", 0.80)
        stability = 1 - abs(prob - 0.5)

        conf = model_quality * 0.6 + stability * 0.4
        return float(max(self.min_conf, min(1.0, conf)))

    # ----------------------------------------------------------------------
    # RISK
    # ----------------------------------------------------------------------
    def _risk(self, prob, conf):
        return float(min(1.0, max(0.0,
            (1 - prob) * 0.45 + (1 - conf) * 0.55
        )))
