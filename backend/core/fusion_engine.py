# Hová kerüljön:
# backend/core/fusion_engine.py

"""
FUSION ENGINE – ÚJ GENERÁCIÓS, ADAPTÍV VERZIÓ
---------------------------------------------
Feladata:
    - Több AI-engine outputjának összevonása
    - Súlyozott átlagolás (ROI, pontosság, drift alapján)
    - Rosszul teljesítő engine-ek súlyának automatikus csökkentése
    - Meta-layer (ensemble optimizer) kompatibilitás
    - Live és prematch módban is működik

Ez a modul MOSTANTÓL támogatja:
✔ dinamikus súlyozást engine teljesítmény alapján
✔ fallback-et, ha egy engine hibás outputot ad
✔ meta-layer összehangolást
✔ confidence score számítást
✔ ROI tracking-et
✔ engine drift detektálást
✔ orchestrator kompatibilitást
"""

from typing import Dict, Any, List
import numpy as np


class FusionEngine:
    def __init__(self):
        # Minden engine súlyát folyamatosan frissítjük
        self.engine_weights = {}
        self.engine_roi = {}
        self.engine_drift = {}

    # =====================================================================
    # Fő függvény
    # =====================================================================
    def fuse(self, engine_outputs: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        engine_outputs formátuma:
        {
            "lstm_engine": {"prob_home": 0.52, "prob_draw": 0.25, ...},
            "value_engine": {...},
            "meta_optimizer": {...}
        }
        """

        probs = {"home": [], "draw": [], "away": []}
        weights = []

        for engine_name, out in engine_outputs.items():
            if not out or "prob_home" not in out:
                # hibás engine output kihagyása
                continue

            weight = self._get_engine_weight(engine_name)

            probs["home"].append(out.get("prob_home", 0.0) * weight)
            probs["draw"].append(out.get("prob_draw", 0.0) * weight)
            probs["away"].append(out.get("prob_away", 0.0) * weight)

            weights.append(weight)

        if not weights:
            return {"prob_home": 0.33, "prob_draw": 0.33, "prob_away": 0.33}

        total_weight = sum(weights)

        fused = {
            "prob_home": float(sum(probs["home"]) / total_weight),
            "prob_draw": float(sum(probs["draw"]) / total_weight),
            "prob_away": float(sum(probs["away"]) / total_weight),
            "confidence": float(np.std([sum(probs[k]) for k in ["home", "draw", "away"]]))
        }

        return fused

    # =====================================================================
    # Súlykezelés (ROI alapján adaptív engine súlyok)
    # =====================================================================
    def update_engine_roi(self, engine_name: str, roi: float):
        self.engine_roi[engine_name] = roi
        self._recalculate_weights()

    def _get_engine_weight(self, engine_name: str) -> float:
        return self.engine_weights.get(engine_name, 1.0)

    def _recalculate_weights(self):
        if not self.engine_roi:
            return

        # Normalizált ROI súlyok
        roi_values = list(self.engine_roi.values())
        min_roi = min(roi_values)
        max_roi = max(roi_values)

        # Ha minden ROI azonos
        if max_roi - min_roi < 1e-9:
            for k in self.engine_roi:
                self.engine_weights[k] = 1.0
            return

        for engine, roi in self.engine_roi.items():
            # Skálázás 0.5–2.0 közé
            w = 0.5 + 1.5 * ((roi - min_roi) / (max_roi - min_roi))
            self.engine_weights[engine] = w

    # =====================================================================
    # Drift detektálás
    # =====================================================================
    def update_drift(self, engine: str, error_rate: float):
        self.engine_drift[engine] = error_rate
        # ha driftes → büntetni kell
        if error_rate > 0.2:
            self.engine_weights[engine] = max(0.3, self.engine_weights.get(engine, 1.0) * 0.7)

    # =====================================================================
    # Meta-layer kompatibilitás
    # =====================================================================
    def apply_meta_layer(self, fused: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
        """
        meta-layer optimalizálás:
        - meta súlyok hozzáadása
        - confidence tuning
        """

        if not meta:
            return fused

        fused = fused.copy()

        fused["prob_home"] = float((fused["prob_home"] + meta.get("boost_home", 0)) / 1.1)
        fused["prob_draw"] = float((fused["prob_draw"] + meta.get("boost_draw", 0)) / 1.1)
        fused["prob_away"] = float((fused["prob_away"] + meta.get("boost_away", 0)) / 1.1)

        fused["confidence"] *= meta.get("confidence_factor", 1.0)

        return fused


# Globális példány
FusionEngineInstance = FusionEngine()
