# backend/engine/data_quality_engine.py

import numpy as np
from backend.utils.logger import get_logger


class DataQualityEngine:
    """
    DATA QUALITY ENGINE – PRO EDITION
    ----------------------------------
    Feladata:
        • Több engine kimenetének megbízhatósági értékelése
        • Outlier detektálás
        • Missing / incomplete engine output felismerése
        • Drift-probability-inconsistency korrekció
        • Trend stabilitás vizsgálat
        • Engine-szintű weight penalty
        • FusionEngine számára teljes quality_score visszaadás
    """

    def __init__(self, config=None):
        self.config = config or {}
        self.logger = get_logger()

        c = self.config.get("data_quality", {})

        self.outlier_threshold = c.get("outlier_threshold", 3.0)    # z-score
        self.min_quality = c.get("min_quality", 0.40)
        self.base_quality = c.get("base_quality", 0.80)
        self.consistency_penalty = c.get("consistency_penalty", 0.20)
        self.missing_penalty = c.get("missing_penalty", 0.15)
        self.volatility_penalty = c.get("volatility_penalty", 0.10)

    # ==========================================================================
    # OUTLIER DETECTION (z-score)
    # ==========================================================================
    def _outlier_score(self, values):
        """
        values = engine-ek probability vagy score értékei
        """
        if len(values) < 3:
            return 0.0

        mean = np.mean(values)
        std = np.std(values)

        if std == 0:
            return 0.0

        z_scores = [(v - mean) / std for v in values]
        max_z = max(abs(z) for z in z_scores)

        return float(min(1.0, max_z / self.outlier_threshold))

    # ==========================================================================
    # CONSISTENCY CHECK
    # ==========================================================================
    def _consistency_score(self, meta):
        """
        meta = {
            "probability": ...,
            "drift": ...,
            "expected_closing": ...
        }
        """

        prob = meta.get("probability")
        drift = meta.get("drift")
        closing = meta.get("expected_closing")

        if prob is None or drift is None or closing is None:
            return 0.0

        # példák:
        # ha drift pozitív, de probability növekedése kicsi → inkonzisztens
        expected_prob_shift = drift * 1.4
        actual_prob_shift = prob - 0.5

        diff = abs(actual_prob_shift - expected_prob_shift)

        return float(min(1.0, diff * 2.0))

    # ==========================================================================
    # MISSING CHECK
    # ==========================================================================
    def _missing_score(self, engine_outputs):
        """
        engine_outputs: dict of engine_name -> output dict
        """
        missing = 0
        total = len(engine_outputs)

        for name, out in engine_outputs.items():
            if out is None:
                missing += 1
            elif not isinstance(out, dict):
                missing += 1

        if total == 0:
            return 1.0

        ratio = missing / total
        return float(min(1.0, ratio))

    # ==========================================================================
    # STABILITY CHECK
    # ==========================================================================
    def _stability_score(self, metric_history):
        """
        metric_history = pl. trend probability history, drift history, xG trend
        """
        if not metric_history or len(metric_history) < 3:
            return 0.0

        volatility = np.std(metric_history)

        return float(min(1.0, volatility / 0.20))  # 20% volatility = max

    # ==========================================================================
    # FŐ ELEMZŐ METÓDUS
    # ==========================================================================
    def analyze(self, engine_outputs, meta=None):
        """
        engine_outputs = {
            "TrendEngine": {"trend_probability": 0.61, ...},
            "AnomalyEngine": {"anomaly_score": 0.12, ...},
            ...
        }

        meta = {
            "probability": ...,
            "drift": ...,
            "expected_closing": ...,
            "history": {
                "trend": [...],
                "drift": [...],
                "probability": [...]
            }
        }
        """

        meta = meta or {}

        # ======================================================================
        # 1) OUTLIER DETECTION
        # ======================================================================
        prob_values = []

        for engine, out in engine_outputs.items():
            if isinstance(out, dict):
                for key in out:
                    if "prob" in key and isinstance(out[key], (int, float)):
                        prob_values.append(out[key])

        outlier = self._outlier_score(prob_values)

        # ======================================================================
        # 2) CONSISTENCY CHECK
        # ======================================================================
        consistency = self._consistency_score(meta)

        # ======================================================================
        # 3) MISSING ENGINE CHECK
        # ======================================================================
        missing = self._missing_score(engine_outputs)

        # ======================================================================
        # 4) STABILITY
        # ======================================================================
        hist = meta.get("history", {})

        volatility_trend = self._stability_score(hist.get("trend", []))
        volatility_prob = self._stability_score(hist.get("probability", []))
        volatility_drift = self._stability_score(hist.get("drift", []))

        volatility = float(np.mean([volatility_trend, volatility_prob, volatility_drift]))

        # ======================================================================
        # QUALITY = BASE - penalties
        # ======================================================================

        quality = self.base_quality
        quality -= outlier * 0.25
        quality -= consistency * self.consistency_penalty
        quality -= missing * self.missing_penalty
        quality -= volatility * self.volatility_penalty

        quality = float(np.clip(quality, self.min_quality, 1.0))

        # confidence = quality
        confidence = quality

        risk = 1 - confidence

        return {
            "quality_score": round(quality, 4),
            "outlier_score": round(outlier, 4),
            "consistency_score": round(consistency, 4),
            "missing_score": round(missing, 4),
            "volatility": round(volatility, 4),
            "confidence": round(confidence, 3),
            "risk": round(risk, 3),
            "engines_checked": list(engine_outputs.keys())
        }
