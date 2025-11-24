import numpy as np

class AICoachExplainer:
    """
    AI COACH EXPLAINER ENGINE
    --------------------------
    Cél:
      - A tippekhez magyarázatot adni.
      - A modellek feature-importance értékeiből emberi nyelvű indoklást generál.
      - Nem módosítja a predikciót, csak értelmezi.
    """

    def explain(self, features: dict, importance: dict, prediction: float):
        """
        features: { feature_name: value }
        importance: { feature_name: importance_score }
        prediction: model kimenet (0-1 vagy odds)
        """
        # fontossági sorrend
        sorted_features = sorted(
            importance.items(), key=lambda x: x[1], reverse=True
        )

        explanation_parts = []
        explanation_parts.append(
            f"A rendszer {prediction:.2f} valószínűséget számolt."
        )
        explanation_parts.append("A legfontosabb tényezők:")

        for feature, score in sorted_features[:5]:
            val = features.get(feature, None)
            explanation_parts.append(
                f" • {feature}: érték={val}, fontosság={score:.3f}"
            )

        return "\n".join(explanation_parts)

    def short_summary(self, prediction: float):
        """
        Gyors verbális összefoglaló.
        """
        if prediction > 0.7:
            return "Magas esélyt számolt a modell."
        if prediction > 0.5:
            return "Közepes esélyt lát a modell."
        return "Alacsony valószínűséget jelez a modell."
