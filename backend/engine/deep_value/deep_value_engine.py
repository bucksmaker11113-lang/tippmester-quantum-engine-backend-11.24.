# backend/engine/deep_value/deep_value_engine.py

import os
import torch
import numpy as np
from backend.utils.logger import get_logger
from backend.engine.deep_value.train_value_model import DeepValueNet


class DeepValueEngine:
    """
    DEEP VALUE ENGINE – PRO VERSION
    --------------------------------
    Feladata:
        • meta feature vectorból prediktálni a value_score-t
        • fallback ha nincs elég adat
        • komolyabb confidence + risk modell
        • együttműködés FusionEngine, ValueAnalyzer, TipSelector modulokkal
    """

    def __init__(self, config):
        self.config = config
        self.logger = get_logger()

        self.input_dim = config.get("deep_value", {}).get("input_dim", 128)
        self.model_path = config.get("deep_value", {}).get(
            "model_path", "backend/data/models/deep_value_model.pth"
        )

        self.device = "cpu"

        # model betöltése
        self.model = DeepValueNet(input_dim=self.input_dim)
        self.model.to(self.device)

        if os.path.exists(self.model_path):
            try:
                self.model.load_state_dict(
                    torch.load(self.model_path, map_location=self.device)
                )
                self.logger.info("[DeepValueEngine] Weights loaded.")
            except Exception as e:
                self.logger.error(f"[DeepValueEngine] Load error: {e}")
        else:
            self.logger.warning("[DeepValueEngine] No model weights found – cold start.")

        self.model.eval()

    # ======================================================================
    # FŐ PREDIKCIÓ
    # ======================================================================
    def predict_value(self, meta_vector: np.ndarray):
        """
        meta_vector = MetaInputBuilder által generált végső input vektor
        """

        # Fallback ha hibás dimenzió
        if meta_vector is None or len(meta_vector) != self.input_dim:
            return {
                "value_score": 0.5,
                "confidence": 0.5,
                "risk": 0.5,
                "source": "DeepValueEngine (fallback)"
            }

        x = torch.tensor(meta_vector, dtype=torch.float32).to(self.device)

        try:
            with torch.no_grad():
                val = float(self.model(x).cpu().numpy())
        except:
            val = 0.5

        # Hard clamp (biztonság)
        val = max(0.01, min(0.99, val))

        # Confidence → minél távolabb 0.5-től, annál erősebb jel
        confidence = min(1.0, 0.5 + abs(val - 0.5) * 1.2)
        risk = 1 - confidence

        return {
            "value_score": round(val, 4),
            "confidence": round(confidence, 3),
            "risk": round(risk, 3),
            "source": "DeepValueEngine"
        }
