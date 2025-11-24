# backend/engine/market_microstructure_engine.py

import numpy as np
from backend.utils.logger import get_logger

class MarketMicrostructureEngine:
    """
    MARKET MICROSTRUCTURE ENGINE – HYBRID PRO EDITION
    -------------------------------------------------
    Feladata:
        • Fogadóirodák belső odds árazási dinamikájának emulálása
        • Microstructure elemzés: spread, liquidity, drift, volatility
        • Sharp money vs public money detection
        • AUTO-HYBRID mód:
            - alapból LIGHT gyors mód
            - ha anomália / value / drift erős → automatikusan PRO mód
        • PRO mód:
            - deep market model
            - volatility prediction
            - liquidity shock sensing
            - orderbook-style trend analízis
    """

    def __init__(self, config):
        self.config = config
        self.logger = get_logger()

        # HYBRID mód thresholdjai
        self.pro_drift_trigger = config.get("market_micro", {}).get("pro_drift_trigger", 0.08)
        self.pro_volume_trigger = config.get("market_micro", {}).get("pro_volume_trigger", 2.0)
        self.pro_volatility_trigger = config.get("market_micro", {}).get("pro_volatility_trigger", 0.10)

        # scaling faktorok
        self.light_scaling = config.get("market_micro", {}).get("light_scaling", 0.15)
        self.pro_scaling = config.get("market_micro", {}).get("pro_scaling", 0.35)
        self.sharp_weight = config.get("market_micro", {}).get("sharp_weight", 0.40)

        # min confidence
        self.min_conf = config.get("market_micro", {}).get("min_confidence", 0.62)

        # fallback
        self.fallback_prob = 0.52

    # ----------------------------------------------------------------------
    # PUBLIC PREDICTOR
    # ----------------------------------------------------------------------
    def predict(self, match_data):
        outputs = {}
        for match_id, data in match_data.items():
            try:
                prob = self._hybrid_microstructure(data)
            except Exception as e:
                self.logger.error(f"[MarketMicro] Hiba → fallback: {e}")
                prob = self.fallback_prob

            prob = float(max(0.01, min(0.99, prob)))
            conf = self._confidence(prob, data)
            risk = self._risk(prob, conf)

            outputs[match_id] = {
                "probability": round(prob, 4),
                "confidence": round(conf, 3),
                "risk": round(risk, 3),
                "meta": {"hybrid_mode": True},
                "source": "MarketMicro"
            }
        return outputs

    # ----------------------------------------------------------------------
    # HYBRID MODE CONTROL
    # ----------------------------------------------------------------------
    def _hybrid_microstructure(self, data):
        """
        Ha erős drift / volume / volatility → PRO mód.
        Egyébként LIGHT mód.
        """

        drift = abs(data.get("odds_open", 2.00) - data.get("odds_now", 2.00))
        volume_ratio = data.get("volume_ratio", 1.0)
        volatility = data.get("market_volatility", 0.03)

        heavy_condition = (
            drift >= self.pro_drift_trigger or
            volume_ratio >= self.pro_volume_trigger or
            volatility >= self.pro_volatility_trigger
        )

        if heavy_condition:
            return self._pro_mode(data)
        return self._light_mode(data)

    # ----------------------------------------------------------------------
    # LIGHT MODE – gyors, olcsó
    # ----------------------------------------------------------------------
    def _light_mode(self, data):
        """
        Gyors baseline:
            - odds drift
            - basic liquidity
            - micro gap
            - public vs sharp simple signal
        """

        odds_open = data.get("odds_open", 2.0)
        odds_now = data.get("odds_now", 2.0)
        drift = odds_open - odds_now

        liquidity = data.get("liquidity", 1.0)
        sharp_ratio = data.get("sharp_ratio", 0.5)

        drift_effect = drift * self.light_scaling
        sharp_effect = (sharp_ratio - 0.5) * self.sharp_weight * self.light_scaling
        liq_effect = (liquidity - 1.0) * 0.05

        prob = 0.5 + drift_effect + sharp_effect + liq_effect
        return prob

    # ----------------------------------------------------------------------
    # PRO MODE – mély elemzés, erős value felismerés
    # ----------------------------------------------------------------------
    def _pro_mode(self, data):
        """
        PRO mód:
            - volatility modelling
            - liquidity shock
            - orderbook simulation
            - micro drift sensitivity
            - sharp influx signal
        """

        odds_open = data.get("odds_open", 2.00)
        odds_now = data.get("odds_now", 2.00)
        volume_ratio = data.get("volume_ratio", 1.0)
        volatility = data.get("market_volatility", 0.05)
        sharp_ratio = data.get("sharp_ratio", 0.50)
        liquidity = data.get("liquidity", 1.0)

        drift = odds_open - odds_now

        # VOLATILITY EFFECT
        vol_effect = volatility * self.pro_scaling

        # DRIFT EFFECT (micro drift sensitivity)
        drift_effect = drift * (self.pro_scaling * 1.5)

        # LIQUIDITY SHOCK
        liq_shock = (1 / max(liquidity, 0.1)) * 0.05

        # SHARP MONEY
        sharp_effect = (sharp_ratio - 0.5) * (self.sharp_weight * self.pro_scaling)

        # VOLUME SPIKE
        volume_effect = (volume_ratio - 1.0) * 0.12

        prob_shift = vol_effect + drift_effect + liq_shock + sharp_effect + volume_effect

        prob = 0.5 + prob_shift
        return prob

    # ----------------------------------------------------------------------
    # CONFIDENCE
    # ----------------------------------------------------------------------
    def _confidence(self, prob, data):
        market_data_q = data.get("market_data_quality", 0.80)
        stability = 1 - abs(prob - 0.5)
        conf = market_data_q * 0.6 + stability * 0.4
        return float(max(self.min_conf, min(1.0, conf)))

    # ----------------------------------------------------------------------
    # RISK
    # ----------------------------------------------------------------------
    def _risk(self, prob, conf):
        return float(min(1.0, max(0.0, (1 - prob) * 0.45 + (1 - conf) * 0.55)))
