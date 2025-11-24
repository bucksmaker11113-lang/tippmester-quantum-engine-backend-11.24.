# backend/core/bias_engine.py

import numpy as np
from backend.utils.logger import get_logger


class BiasEngine:
    """
    BIAS ENGINE – PRO VERSION
    --------------------------
    Feladata:
        • odds drift alapú torzítás
        • market pressure / public money torzítás
        • model deviation (szórás alapú)
        • form / anomaly detection korrekció
        • volatility súlyozás
        • több bias összevont, súlyozott korrigálása
    """

    def __init__(self, config=None):
        self.config = config or {}
        self.logger = get_logger()

        # konfigurálható bias súlyok (0–1)
        self.weights = self.config.get("bias_weights", {
            "drift": 0.30,
            "market": 0.25,
            "model_dev": 0.25,
            "form": 0.20,
        })

        # scaling factor for corrections
        self.max_correction = self.config.get("max_correction", 0.15)

    # ======================================================================
    # BIAS COMPONENT #1 – ODDS DRIFT BIAS
    # ======================================================================
    def _drift_bias(self, drift):
        """
        drift: odds drift (pl.: -0.20 → 20% odds csökkenés)
        """
        return float(np.clip(drift, -0.3, 0.3))

    # ======================================================================
    # BIAS COMPONENT #2 – MARKET PRESSURE (public money)
    # ======================================================================
    def _market_bias(self, public_money):
        """
        public_money: 0–1 (piaci pénz nagysága)
        """
        return float(np.clip(public_money - 0.5, -0.5, 0.5))

    # ======================================================================
    # BIAS COMPONENT #3 – MODEL DEVIATION (ensemble szórás)
    # ======================================================================
    def _model_dev_bias(self, model_std):
        """
        model_std: 0–0.25 tipikus tartomány
        """
        return float(np.clip(model_std * 2.0, -0.5, 0.5))

    # ======================================================================
    # BIAS COMPONENT #4 – FORM / ANOMALY detection
    # ======================================================================
    def _form_bias(self, form_score):
        """
        form_score: -1–+1 range
        """
        return float(np.clip(form_score * 0.4, -0.4, 0.4))

    # ======================================================================
    # BIAS AGGREGATION
    # ======================================================================
    def _aggregate_bias(self, components):
        """
        components = { "drift": ..., "market": ..., ... }
        """

        total = 0.0
        for k, v in components.items():
            w = self.weights.get(k, 0)
            total += w * v

        # clamp final correction
        return float(np.clip(total, -self.max_correction, self.max_correction))

    # ======================================================================
    # FŐ FUNKCIÓ – BIAS KORREKCIÓ A BAYES OUTPUTON
    # ======================================================================
    def apply_bias(self, bayes_output, meta_data):
        """
        bayes_output:
            {
                match_id: {
                    "probability": float,
                    ...
                }
            }

        meta_data:
            {
                match_id: {
                    "drift": ...,
                    "public_money": ...,
                    "model_std": ...,
                    "form_score": ...,
                }
            }

        Visszatér:
            {
                match_id: {
                    "probability": korrigált érték,
                    "bias_components": {...},
                    "source": "BiasEngine"
                }
            }
        """

        corrected = {}

        for match_id, pred in bayes_output.items():

            try:
                base_prob = float(pred.get("probability", 0.5))
                meta = meta_data.get(match_id, {})
            except:
                continue

            # ---- bias komponensek ----
            drift_b = self._drift_bias(meta.get("drift", 0))
            market_b = self._market_bias(meta.get("public_money", 0.5))
            dev_b = self._model_dev_bias(meta.get("model_std", 0.05))
            form_b = self._form_bias(meta.get("form_score", 0.0))

            components = {
                "drift": drift_b,
                "market": market_b,
                "model_dev": dev_b,
                "form": form_b,
            }

            # teljes bias korrekció
            correction = self._aggregate_bias(components)

            final_prob = np.clip(base_prob + correction, 0.01, 0.99)

            corrected[match_id] = {
                "probability": float(final_prob),
                "bias_components": components,
                "correction": float(correction),
                "source": "BiasEngine"
            }

        return corrected
