# backend/engine/quantum_synth_engine.py

import numpy as np
from backend.utils.logger import get_logger

class QuantumSynthEngine:
    """
    QUANTUM SYNTH ENGINE – CORE BASE MODEL
    --------------------------------------
    Ez a Tippmester Quantum központi kvantum prediktora.
    Feladata:
        • valószínűség becslés kvantumus szintézissel
        • meta-alapú valószínűség normalizálás
        • risk és confidence számítás
        • stabil, fallback-biztos output
        • ensemble friendly (FusionEngine kompatibilis)
    """

    def __init__(self, config):
        self.config = config
        self.logger = get_logger()

        # kvantum zaj- és instabilitás csillapítás
        self.noise_reduction = config.get("quantum", {}).get("noise_reduction", 0.75)

        # scaling faktor a valószínűségek kisimításához
        self.scaling = config.get("quantum", {}).get("scaling", 1.15)

        # minimum confidence baseline
        self.min_conf = config.get("quantum", {}).get("min_confidence", 0.55)

        # fallback probability
        self.fallback_prob = 0.50

    # ----------------------------------------------------------------------
    # PUBLIC – Fő futtatás
    # ----------------------------------------------------------------------
    def predict(self, match_data):
        """
        Bemenet: match_data → összevont adatcsomag pipeline-ból
        Kimenet:
            {
                match_id: {
                    "probability": ...,
                    "confidence": ...,
                    "risk": ...,
                    "meta": {...},
                    "source": "QuantumSynth"
                }
            }
        """

        outputs = {}

        for match_id, data in match_data.items():

            try:
                prob = self._quantum_core(match_id, data)
            except Exception as e:
                self.logger.error(f"[Quantum] Hiba, fallback: {e}")
                prob = self.fallback_prob

            # normalizálás
            prob = self._normalize(prob)

            # confidence + risk számítás
            confidence = self._confidence(prob, data)
            risk = self._risk(prob, confidence)

            outputs[match_id] = {
                "probability": round(prob, 4),
                "confidence": round(confidence, 3),
                "risk": round(risk, 3),
                "meta": {
                    "scaling": self.scaling,
                    "noise_reduction": self.noise_reduction
                },
                "source": "QuantumSynth"
            }

        return outputs

    # ----------------------------------------------------------------------
    # KVANTUM MAG (probability generátor)
    # ----------------------------------------------------------------------
    def _quantum_core(self, match_id, data):
        """
        A kvantum mag fő prediktív logikája.
        Ez egy speciális kvantum-szintetizált súlyozott becslés.
        """

        # Ha a data üres → fallback
        if not data:
            return self.fallback_prob

        # Fő bemeneti komponensek
        form = data.get("form_factor", 0.5)
        xg = data.get("xg_ratio", 0.5)
        elo = data.get("elo_winprob", 0.5)
        momentum = data.get("momentum_pre", 0.5)
        h2h = data.get("h2h_strength", 0.5)

        # kvantum-szintézis súlyok
        weights = {
            "form": 0.22,
            "xg": 0.28,
            "elo": 0.25,
            "momentum": 0.15,
            "h2h": 0.10
        }

        # súlyozott kvantum kombináció
        base = (
            form * weights["form"] +
            xg * weights["xg"] +
            elo * weights["elo"] +
            momentum * weights["momentum"] +
            h2h * weights["h2h"]
        )

        # kvantum fluktuáció simuláció
        noise = np.random.uniform(-0.05, 0.05) * (1 - self.noise_reduction)

        return base + noise

    # ----------------------------------------------------------------------
    # NORMALIZÁLÁS
    # ----------------------------------------------------------------------
    def _normalize(self, prob):
        """
        Skálázás és korrekció, hogy stabil 0.01–0.99 között maradjon.
        """
        prob *= self.scaling
        prob = max(0.01, min(0.99, prob))
        return float(prob)

    # ----------------------------------------------------------------------
    # CONFIDENCE
    # ----------------------------------------------------------------------
    def _confidence(self, prob, data):
        """
        Confidence a kvantum mag stabilitása + input minősége alapján.
        """
        quality = data.get("data_quality", 0.8)
        conf = prob * 0.6 + quality * 0.4

        return float(max(self.min_conf, min(1.0, conf)))

    # ----------------------------------------------------------------------
    # RISK
    # ----------------------------------------------------------------------
    def _risk(self, prob, confidence):
        """
        Minél alacsonyabb a confidence, annál nagyobb a risk.
        """
        risk = (1 - prob) * 0.5 + (1 - confidence) * 0.5
        return float(max(0.0, min(1.0, risk)))
