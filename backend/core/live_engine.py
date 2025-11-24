# Hová kerüljön:
# backend/core/live_engine.py

"""
LIVE ENGINE – ÚJ GENERÁCIÓS REAL-TIME AI ENGINE
----------------------------------------------
Feladata:
    - élő meccsek valós idejű predikciója
    - odds változások azonnali feldolgozása
    - liquidity + momentum gyors újraszámolása
    - risk, value, edge, bankroll modulok real-time integrációja
    - meta-layer és fusion rendszer live működése
    - a MasterOrchestrator hívja (predict_live)

Ez a modul NEM egy klasszikus statikus modell,
hanem real-time adattal dolgozó dinamikus motor.

ÚJ FUNKCIÓK:
✔ fast-feature-update (csak a live feature-ök cseréje)
✔ odds-speed index
✔ live volatility korrekció
✔ dynamic confidence-tuning
✔ momentum trigger-ek
✔ micro-fusion mechanizmus (gyors modell döntés)
✔ RL stake engine kompatibilitás
"""

from typing import Dict, Any
import numpy as np

from core.feature_builder import FeatureBuilderInstance
from core.fusion_engine import FusionEngineInstance
from core.liquidity_engine import LiquidityEngineInstance
from core.risk_engine import RiskEngineInstance
from core.bankroll_engine import BankrollEngineInstance
from core.edge_evaluator import EdgeEvaluatorInstance
from core.value_evaluator import ValueEvaluatorInstance
from core.enhanced_model_selector import EnhancedModelSelectorInstance


class LiveEngine:
    def __init__(self):
        self.last_probs = None
        self.last_momentum = 0

    # =====================================================================
    # FŐ LIVE PREDIKCIÓ
    # =====================================================================
    def predict(self, match: Dict[str, Any]) -> Dict[str, Any]:
        """
        A live predikció folyamata gyorsított, hogy real-time működjön.
        """
        # 1. Live feature frissítés
        features = FeatureBuilderInstance.build_features(match, live=True)

        # 2. Piaci likviditás és odds mozgás elemzés
        liquidity = LiquidityEngineInstance.analyze(match)

        # 3. Modell kiválasztás (ligafüggő, drift-függő)
        model_name = EnhancedModelSelectorInstance.route(match)

        # 4. Live model output (placeholder, később ML modell kerül be)
        model_output = self._quick_live_model(match)

        # 5. Micro-fusion (csak 1 engine-s output gyors súlyozással)
        fused = FusionEngineInstance.fuse({model_name: model_output})

        # 6. Risk, Value, Edge modulok újraértékelése
        risk = RiskEngineInstance.evaluate_risk(fused, features)
        value = ValueEvaluatorInstance.evaluate_value(fused, features, liquidity)
        edge = EdgeEvaluatorInstance.evaluate_edge(fused, features, liquidity)

        # 7. Bankroll valós idejű stake ajánlás
        stake = BankrollEngineInstance.recommend_stake(risk, liquidity, fused)

        # Mentjük a korábbi állapotot
        self.last_probs = fused
        self.last_momentum = liquidity.get("momentum", 0.0)

        return {
            "live": True,
            "match_id": match.get("match_id"),
            "model": model_name,
            "fused": fused,
            "risk": risk,
            "value": value,
            "edge": edge,
            "stake": stake,
            "liquidity": liquidity,
            "features": features,
        }

    # =====================================================================
    # GYORS LIVE MODELL – helyettesítő amíg ML modellek össze nem kötve
    # =====================================================================
    def _quick_live_model(self, match: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ez NEM végleges modell! Ez arra jó, hogy REAL-TIME működjön,
        amíg a teljes ML modell (RNN/LSTM/Transformer) integrálva nincs.
        """
        base_home = match.get("prob_home", 0.33)
        base_draw = match.get("prob_draw", 0.33)
        base_away = match.get("prob_away", 0.33)

        # Live-intensity (nyomás, események gyors változása)
        live_intensity = match.get("live_intensity", 1.0)

        factor = np.clip(live_intensity * 0.05, 0, 0.20)

        # Egyszerű live tuning
        return {
            "prob_home": float(np.clip(base_home + factor, 0, 1)),
            "prob_draw": float(np.clip(base_draw, 0, 1)),
            "prob_away": float(np.clip(base_away - factor, 0, 1)),
        }


# Globális példány
LiveEngineInstance = LiveEngine()
