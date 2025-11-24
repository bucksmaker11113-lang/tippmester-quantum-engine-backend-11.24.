# backend/pipeline/tip_pipeline.py

class TipPipeline:
    """
    Tipp generátor:
        - Single
        - Kombi
        - Live

    A DeepValue + ValueAnalyzer + Confidence alapján.
    """

    def __init__(self, config):
        self.config = config

    def single(self, predictions):
        # min EV, min deep value
        tips = []
        for m_id, p in predictions.items():
            if p["ev"] > 0.05 and p["deep_value"] > 0.55:
                tips.append((m_id, p))
        return tips[:4]  # napi 4 single

    def kombi(self, predictions):
        # 3 value pick = 1 kombi
        arr = []
        for m_id, p in predictions.items():
            if p["value_score"] > 0.3 and p["confidence"] > 0.6:
                arr.append((m_id, p))
        return arr[:3]

    def live(self, live_data):
        # GameFlow + ScorePredictor + DeepValue alapján
        tips = []
        for m_id, p in live_data.items():
            if p["game_chance"] > 0.7 and p["deep_value"] > 0.6:
                tips.append((m_id, p))
        return tips
