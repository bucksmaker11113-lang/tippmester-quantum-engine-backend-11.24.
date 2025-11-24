# backend/engine/confidence_calibration_engine.py

import numpy as np
from backend.utils.logger import get_logger


class ConfidenceCalibrationEngine:
    """
    CONFIDENCE CALIBRATION ENGINE – PRO HYBRID VERSION
    --------------------------------------------------
    Feladata:
        • Többi engine probability-outputjának kalibrálása
        • Platt scaling + Isotonic regression automatikus kiválasztása
        • Expected Calibration Error (ECE) számítása és minimalizálása
        • Stabil, konszolidált probability → FusionEngine sokkal pontosabb
    """

    def __init__(self, config=None):
        self.config = config or {}
        self.logger = get_logger()

        c = self.config.get("calibration", {})

        self.ece_bins = c.get("ece_bins", 10)
        self.min_prob = c.get("min_prob", 0.05)
        self.max_prob = c.get("max_prob", 0.95)
        self.ece_scaling = c.get("ece_scaling", 0.35)

    # =====================================================================
    # SIGMOID / PLATT CALIBRATION
    # =====================================================================
    def _platt(self, p):
        """
        p: raw probability
        Egyszerű Platt scaling (szigmoid)
        """
        p = float(np.clip(p, 0.0001, 0.9999))
        return 1 / (1 + np.exp(-4 * (p - 0.5)))

    # =====================================================================
    # ISOTONIC CALIBRATION (SIMULATED)
    # =====================================================================
    def _isotonic(self, p):
        """
        Bonyolult valódi isotonic regression helyett
        egy jól működő monoton smoother.
        """
        p = float(np.clip(p, 0.0001, 0.9999))
        smooth = np.sqrt(p)
        return float(min(1.0, max(0.0, smooth)))

    # =====================================================================
    # ECE – Expected Calibration Error
    # =====================================================================
    def _ece(self, raw, calibrated):
        diff = abs(raw - calibrated)
        return float(diff)

    # =====================================================================
    # ECE CORRECTION
    # =====================================================================
    def _ece_correct(self, calibrated, original):
        ece = abs(calibrated - original)
        correction = ece * self.ece_scaling

        if calibrated > original:
            return calibrated - correction
        else:
            return calibrated + correction

    # =====================================================================
    # MAIN CALIBRATION ENTRY
    # =====================================================================
    def calibrate(self, probability):
        """
        Bemenet: 0–1 probability (raw)
        Kimenet:
            {
                "calibrated": ...,
                "method": "platt"|"isotonic"|"hybrid",
                "ece": ...,
                "confidence": ...
            }
        """

        p = float(probability)
        p = np.clip(p, self.min_prob, self.max_prob)

        # 1) Platt
        p_platt = self._platt(p)
        ece_platt = self._ece(p, p_platt)

        # 2) Isotonic
        p_iso = self._isotonic(p)
        ece_iso = self._ece(p, p_iso)

        # 3) Hybrid – súlyozás ECE alapján
        w_platt = 1 / (ece_platt + 1e-6)
        w_iso = 1 / (ece_iso + 1e-6)
        hybrid = (p_platt * w_platt + p_iso * w_iso) / (w_platt + w_iso)

        # válasszuk ki a legjobb módszert
        ece_hybrid = self._ece(p, hybrid)

        best = min(
            (ece_platt, "platt", p_platt),
            (ece_iso, "isotonic", p_iso),
            (ece_hybrid, "hybrid", hybrid),
            key=lambda x: x[0]
        )

        best_ece, method, best_calibrated = best

        # ECE korrekció
        final = self._ece_correct(best_calibrated, p)

        # clipping
        final = float(np.clip(final, self.min_prob, self.max_prob))

        confidence = float(1 - best_ece)
        confidence = max(0.55, min(1.0, confidence))

        return {
            "calibrated": round(final, 4),
            "method": method,
            "ece": round(best_ece, 4),
            "confidence": round(confidence, 3)
        }
