# Hová kerüljön:
# backend/core/master_orchestrator.py

"""
MASTER ORCHESTRATOR – A TELJES AI RENDSZER KÖZPONTI VEZÉRLŐJE
-------------------------------------------------------------
Ez a modul a teljes tippmester AI rendszer *agya*.
Feladata:
    ✔ összekötni az összes engine-t (Fusion, Risk, Liquidity, Value, Edge, Bankroll)
    ✔ futtatni a live és prematch predikciókat
    ✔ hívni a tip-pipeline modulokat
    ✔ egységes AI-outputot adni a frontendnek
    ✔ integrálni a RL Stake Engine-t
    ✔ model selectorral kiválasztani a megfelelő modellt
    ✔ orchestrálni a daily training workflow-t
    ✔ scheduler-rel együtt dolgozni
"""

from typing import Dict, Any

# Core engine-ek
from core.feature_builder import FeatureBuilderInstance
from core.fusion_engine import FusionEngineInstance
from core.risk_engine import RiskEngineInstance
from core.liquidity_engine import LiquidityEngineInstance
from core.bankroll_engine import BankrollEngineInstance
from core.edge_evaluator import EdgeEvaluatorInstance
from core.value_evaluator import ValueEvaluatorInstance
from core.enhanced_model_selector import EnhancedModelSelectorInstance

# Pipeline modulok (később frissítjük)
# from pipeline.tip_pipeline import TipPipeline
# from pipeline.tip_generator_pro import TipGeneratorPro


class MasterOrchestrator:
    def __init__(self):
        self.initialized = False

    # =====================================================================
    # RENDSZER BETÖLTÉS
    # =====================================================================
    async def initialize_all(self):
        print("[ORCH] FeatureBuilder kész.")
        print("[ORCH] FusionEngine kész.")
        print("[ORCH] RiskEngine kész.")
        print("[ORCH] LiquidityEngine kész.")
        print("[ORCH] BankrollEngine kész.")
        print("[ORCH] EdgeEvaluator kész.")
        print("[ORCH] ValueEvaluator kész.")
        print("[ORCH] ModelSelector kész.")

        self.initialized = True

    # =====================================================================
    # PREMATCH PREDIKCIÓ – fő AI workflow
    # =====================================================================
    def predict_match(self, match: Dict[str, Any]) -> Dict[str, Any]:
        features = FeatureBuilderInstance.build_features(match, live=False)
        liquidity = LiquidityEngineInstance.analyze(match)

        # Modell kiválasztása
        model_name = EnhancedModelSelectorInstance.route(match)

        # Fusion engine-nek kell a predikció – itt placeholder outputot generálunk
        # (a tényleges modellek később bekötésre kerülnek)
        model_output = {
            "prob_home": match.get("prob_home", 0.33),
            "prob_draw": match.get("prob_draw", 0.33),
            "prob_away": match.get("prob_away", 0.33)
        }

        fused = FusionEngineInstance.fuse({model_name: model_output})

        risk = RiskEngineInstance.evaluate_risk(fused, features)
        value = ValueEvaluatorInstance.evaluate_value(fused, features, liquidity)
        edge = EdgeEvaluatorInstance.evaluate_edge(fused, features, liquidity)

        # Bankroll ajánlás
        stake = BankrollEngineInstance.recommend_stake(risk, liquidity, fused)

        return {
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
    # LIVE PREDIKCIÓ – real-time workflow
    # =====================================================================
    def predict_live(self, match: Dict[str, Any]) -> Dict[str, Any]:
        features = FeatureBuilderInstance.build_features(match, live=True)
        liquidity = LiquidityEngineInstance.analyze(match)

        model_name = EnhancedModelSelectorInstance.route(match)

        # Placeholder live predikció – később LiveEngine kerül ide
        model_output = {
            "prob_home": match.get("prob_home", 0.33),
            "prob_draw": match.get("prob_draw", 0.33),
            "prob_away": match.get("prob_away", 0.33)
        }

        fused = FusionEngineInstance.fuse({model_name: model_output})

        risk = RiskEngineInstance.evaluate_risk(fused, features)
        value = ValueEvaluatorInstance.evaluate_value(fused, features, liquidity)
        edge = EdgeEvaluatorInstance.evaluate_edge(fused, features, liquidity)
        stake = BankrollEngineInstance.recommend_stake(risk, liquidity, fused)

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
    # NAPI PIPELINE FUTTATÁS
    # =====================================================================
    def run_daily_pipeline(self):
        print("[ORCH] Napi pipeline futtatása…")
        # Ide kötjük be később:
        # TipPipeline().run()
        # TipGeneratorPro().run()

    # =====================================================================
    # MODELL RE-TRAIN
    # =====================================================================
    def retrain_models(self):
        print("[ORCH] Modellek újratanítása… (placeholder)")


# Globális elérhetőség
MasterOrchestratorInstance = MasterOrchestrator()
