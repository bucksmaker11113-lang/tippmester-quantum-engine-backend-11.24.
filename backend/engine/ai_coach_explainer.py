# backend/engine/ai_coach_explainer.py
# Magyarázó modul a tippekhez
# - Egyszerű, gyors, CPU-barát
# - Készen áll későbbi NLP alapú magyarázó modell fogadására

class AICoachExplainer:
    def __init__(self):
        pass

    def explain(self, tip_data: dict) -> str:
        """
        Gyors, magyarázó szöveg generálása a tipphez.
        Tényleges NLP modell később integrálható.
        """
        match = tip_data.get("match", "Unknown match")
        pick = tip_data.get("pick", "N/A")
        odds = tip_data.get("odds", "-")
        confidence = tip_data.get("confidence", 0.5)

        # Egyszerű szabályalapú magyarázat
        if confidence > 0.7:
            tone = "erős statisztikai jelzések alapján"
        elif confidence > 0.55:
            tone = "kiegyensúlyozott adatok alapján"
        else:
            tone = "bizonytalan statisztikai alapokon"

        explanation = (
            f"A(z) {match} mérkőzésre adott tipped: {pick}. "
            f"A döntést {tone} készítettem elő, ahol az odds {odds}."
        )

        return explanation
