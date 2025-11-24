# backend/engine/fusion_engine.py
# Profi Fusion Engine – a különböző AI modulok eredményeinek összevonására
# Kvant tippmodellekben ez végzi a végső tipp összerakását.
# - anomaly, bias, bayesian, value, model predictor eredmények integrálása
# - stabil, skálázható, CPU-barát

from backend.engine.anomaly_engine import AnomalyEngine
from backend.engine.bias_engine import BiasEngine
from backend.engine.ai_coach_explainer import AICoachExplainer


class FusionEngine:
    def __init__(self):
        self.anomaly = AnomalyEngine()
        self.bias = BiasEngine()
        self.explainer = AICoachExplainer()

    def fuse(self, value_data: dict, match_data: dict) -> dict:
        """
        Final tip assembly:
        - raw probabilities + bias corrected probabilities
        - anomaly flags
        - AI explanation
        - expected value (EV)
        - final recommended pick
        """

        base_probs = value_data.get("base_probabilities", {})
        ev = value_data.get("expected_value", {})
        odds = value_data.get("odds", {})

        # 1) Bias correction
        corrected_probs = self.bias.correct(base_probs, match_data)

        # 2) Detect anomalies
        anomaly_info = self.anomaly.detect(match_data)

        # 3) Choose best pick based on EV (expected value)
        if ev:
            best_pick = max(ev, key=ev.get)
            best_ev = ev.get(best_pick, 0)
            selected_odds = odds.get(best_pick, None)
        else:
            # fallback: highest probability
            best_pick = max(corrected_probs, key=corrected_probs.get)
            best_ev = 0
            selected_odds = odds.get(best_pick, None)

        # 4) AI explanation
        explanation = self.explainer.explain({
            "match": match_data.get("match"),
            "pick": best_pick,
            "odds": selected_odds,
            "confidence": corrected_probs.get(best_pick, 0)
        })

        # 5) Final output
        return {
            "match": match_data.get("match"),
            "pick": best_pick,
            "odds": selected_odds,
            "confidence": corrected_probs,
            "expected_value": best_ev,
            "anomalies": anomaly_info,
            "explanation": explanation
        }
