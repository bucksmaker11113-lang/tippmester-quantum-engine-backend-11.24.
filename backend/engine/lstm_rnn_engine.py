# backend/engine/lstm_rnn_engine.py

import numpy as np
from backend.utils.logger import get_logger

class LSTM_RNN_Engine:
    """
    LSTM / RNN Engine – Compact PRO Version
    ---------------------------------------
    Modern, pipeline-kompatibilis idősoros predikciós motor.

    Fő funkciók:
        • form/xG/goal idősor feldolgozás
        • opcionális betanított modell betöltés (.h5 vagy .pt)
        • fallback predikció modell nélkül
        • normalizált probability output
        • confidence + risk számítás
        • meta adatok FusionEngine-hez
    """

    def __init__(self, config):
        self.config = config
        self.logger = get_logger()

        # modell betöltés
        self.model = self._load_model()

        # fallback paraméterek
        self.fallback_center = config.get("lstm", {}).get("fallback_center", 0.57)
        self.fallback_spread = config.get("lstm", {}).get("fallback_spread", 0.12)

        # scaling faktor
        self.scaling = config.get("lstm", {}).get("scaling", 1.10)

        self.min_conf = config.get("lstm", {}).get("min_confidence", 0.58)

    # --------------------------------------------------------
    # MODEL BETÖLTÉSE (HA VAN)
    # --------------------------------------------------------
    def _load_model(self):
        try:
            path = self.config.get("lstm", {}).get("model_path")
            if not path:
                return None

            if path.endswith(".h5"):
                from tensorflow.keras.models import load_model
                model = load_model(path)
                self.logger.info("[LSTM] Keras modell betöltve.")
                return model

            if path.endswith(".pt"):
                import torch
                model = torch.load(path, map_location="cpu")
                model.eval()
                self.logger.info("[LSTM] PyTorch modell betöltve.")
                return model

        except Exception as e:
            self.logger.error(f"[LSTM] Modell betöltése sikertelen: {e}")

        return None

    # --------------------------------------------------------
    # FŐ PREDIKCIÓ
    # --------------------------------------------------------
    def predict(self, match_data):
        outputs = {}

        for match_id, data in match_data.items():

            seq = self._prepare_sequence(data)

            try:
                if self.model:
                    prob = self._predict_model(seq)
                else:
                    prob = self._fallback_pred(data)
            except:
                prob = self._fallback_pred(data)

            # normalizálás
            prob = self._normalize(prob)

            # metrics
            conf = self._confidence(prob, data)
            risk = self._risk(prob, conf)

            outputs[match_id] = {
                "probability": round(prob, 4),
                "confidence": round(conf, 3),
                "risk": round(risk, 3),
                "meta": {
                    "sequence_len": len(seq),
                    "model_loaded": self.model is not None
                },
                "source": "LSTM_RNN"
            }

        return outputs

    # --------------------------------------------------------
    # SEQUENCE PREP
    # --------------------------------------------------------
    def _prepare_sequence(self, data):
        # előre formázott idősorok
        seq = [
            data.get("form_sequence", [0.5] * 10),
            data.get("xg_sequence", [1.0] * 10),
            data.get("goals_sequence", [1.0] * 10)
        ]

        # összeolvasztjuk egyetlen idősortömbbé
        merged = []
        for i in range(10):
            point = [
                seq[0][i],
                seq[1][i],
                seq[2][i]
            ]
            merged.append(point)

        return np.array(merged, dtype=float)

    # --------------------------------------------------------
    # MODELL FUTTATÁSA
    # --------------------------------------------------------
    def _predict_model(self, seq):
        try:
            if hasattr(self.model, "predict"):  # KERAS
                p = float(self.model.predict(seq.reshape(1, seq.shape[0], seq.shape[1]))[0][0])
                return p
            else:  # PYTORCH
                import torch
                tens = torch.tensor(seq, dtype=torch.float32).unsqueeze(0)
                p = float(self.model(tens).detach().numpy()[0][0])
                return p
        except:
            return self.fallback_center

    # --------------------------------------------------------
    # FALLBACK PREDIKCIÓ
    # --------------------------------------------------------
    def _fallback_pred(self, data):
        base = self.fallback_center
        noise = np.random.uniform(-self.fallback_spread, self.fallback_spread) * 0.25
        return base + noise

    # --------------------------------------------------------
    # NORMALIZÁLÁS
    # --------------------------------------------------------
    def _normalize(self, p):
        p *= self.scaling
        return float(max(0.01, min(0.99, p)))

    # --------------------------------------------------------
    # CONFIDENCE
    # --------------------------------------------------------
    def _confidence(self, prob, data):
        quality = data.get("data_quality", 0.8)
        conf = prob * 0.5 + quality * 0.5
        return float(max(self.min_conf, min(1.0, conf)))

    # --------------------------------------------------------
    # RISK
    # --------------------------------------------------------
    def _risk(self, prob, conf):
        return float(min(1.0, max(0.0, (1 - prob) * 0.6 + (1 - conf) * 0.4)))
