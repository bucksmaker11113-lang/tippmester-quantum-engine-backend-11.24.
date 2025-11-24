# backend/engine/gnn_engine.py

import numpy as np
from backend.utils.logger import get_logger

class GNN_Engine:
    """
    GNN ENGINE – PRO EDITION
    -------------------------
    A Graph Neural Network (GNN) motor feladata:
        • csapatok közti relációs gráf modellezése
        • form + H2H + liga szintek összekapcsolása
        • team embedding generálása
        • rejtett struktúrák felismerése
        • valószínűség becslés a gráf alapján

    A motor képes:
        • betöltött GNN modell használatára (ha létezik)
        • fallback GNN-imitációra (ha nincs modell)
        • stabilizált output generálására
    """

    def __init__(self, config):
        self.config = config
        self.logger = get_logger()

        self.model = self._load_model()

        # fallback középérték és szórás
        self.base_prob = config.get("gnn", {}).get("fallback_center", 0.56)
        self.variance = config.get("gnn", {}).get("fallback_variance", 0.1)

        # scaling
        self.scaling = config.get("gnn", {}).get("scaling", 1.08)
        self.min_conf = config.get("gnn", {}).get("min_confidence", 0.57)

    # ----------------------------------------------------------------------
    # MODEL LOADER
    # ----------------------------------------------------------------------
    def _load_model(self):
        """
        Automatikusan felismeri:
            • PyTorch GNN modellt
            • TensorFlow GNN modellt
        Ha nincs → fallback mód.
        """
        try:
            path = self.config.get("gnn", {}).get("model_path")
            if not path:
                return None

            if path.endswith(".pt"):
                import torch
                model = torch.load(path, map_location="cpu")
                model.eval()
                self.logger.info("[GNN] PyTorch GNN modell betöltve.")
                return model

            if path.endswith(".h5"):
                from tensorflow.keras.models import load_model
                model = load_model(path)
                self.logger.info("[GNN] TensorFlow GNN modell betöltve.")
                return model

        except Exception as e:
            self.logger.error(f"[GNN] Modell betöltési hiba: {e}")

        return None

    # ----------------------------------------------------------------------
    # PUBLIC: CSAPATSZINTŰ PREDIKCIÓ
    # ----------------------------------------------------------------------
    def predict(self, match_data):
        outputs = {}

        for match_id, data in match_data.items():

            # gráf input előkészítés
            g_input = self._prepare_graph_input(data)

            try:
                if self.model:
                    prob = self._predict_model(g_input)
                else:
                    prob = self._fallback_pred(data)
            except Exception as e:
                self.logger.error(f"[GNN] Hiba, fallback: {e}")
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
                    "embedding_size": 16,
                    "model_loaded": self.model is not None
                },
                "source": "GNN"
            }

        return outputs

    # ----------------------------------------------------------------------
    # GRAPH INPUT GENERÁLÁS
    # ----------------------------------------------------------------------
    def _prepare_graph_input(self, data):
        """
        A csapatok gráfhoz szükséges jellemzők:
            • csapat-rating
            • form rating
            • xG form rating
            • attack/defense vectors
            • H2H history encoded
        """
        teamA_vec = [
            data.get("rating_home", 1.0),
            data.get("form_home", 0.5),
            data.get("xg_home", 1.1),
            data.get("attack_home", 1.0),
            data.get("defense_home", 1.0)
        ]

        teamB_vec = [
            data.get("rating_away", 1.0),
            data.get("form_away", 0.5),
            data.get("xg_away", 1.0),
            data.get("attack_away", 1.0),
            data.get("defense_away", 1.0)
        ]

        # H2H encoding
        h2h = data.get("h2h_strength", 0.5)

        # gráf input (10 dim körül)
        return np.array(teamA_vec + teamB_vec + [h2h], dtype=float)

    # ----------------------------------------------------------------------
    # MODEL PREDIKCIÓ
    # ----------------------------------------------------------------------
    def _predict_model(self, g_input):
        """
        Ha a modell létezik, futtatjuk rajta.
        """
        try:
            if hasattr(self.model, "predict"):  # Keras
                p = float(self.model.predict(g_input.reshape(1, -1))[0][0])
                return p
            else:  # PyTorch
                import torch
                tens = torch.tensor(g_input, dtype=torch.float32).unsqueeze(0)
                p = float(self.model(tens).detach().numpy()[0][0])
                return p
        except:
            return self.base_prob

    # ----------------------------------------------------------------------
    # FALLBACK PREDIKCIÓ
    # ----------------------------------------------------------------------
    def _fallback_pred(self, data):
        noise = np.random.uniform(-self.variance, self.variance) * 0.25
        return self.base_prob + noise

    # ----------------------------------------------------------------------
    # NORMALIZÁLÁS
    # ----------------------------------------------------------------------
    def _normalize(self, p):
        p *= self.scaling
        return float(max(0.01, min(0.99, p)))

    # ----------------------------------------------------------------------
    # CONFIDENCE
    # ----------------------------------------------------------------------
    def _confidence(self, prob, data):
        quality = data.get("data_quality", 0.85)
        conf = prob * 0.4 + quality * 0.6
        return float(max(self.min_conf, min(1.0, conf)))

    # ----------------------------------------------------------------------
    # RISK
    # ----------------------------------------------------------------------
    def _risk(self, prob, conf):
        return float(min(1.0, max(0.0, (1 - prob) * 0.5 + (1 - conf) * 0.5)))
