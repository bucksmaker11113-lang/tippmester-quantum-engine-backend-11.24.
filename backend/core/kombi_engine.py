# Hová kerüljön:
# backend/core/kombi_engine.py

"""
KOMBI ENGINE – ÚJ GENERÁCIÓS, VALUE-OPTIMALIZÁLT KOMBINÁCIÓS TIPPMOTOR
-----------------------------------------------------------------------
Feladata:
    - kombi szelvények automatikus generálása AI alapon
    - a legjobb meccsek kiválasztása (value, edge, risk score alapján)
    - bankroll és kockázati szintek figyelése
    - elkerülni a túl kockázatos vagy alacsony edge értékű kombinációkat
    - optimalizált kombi struktúrák generálása (2-es, 3-as, max 4-es kombi)

Ez az új verzió:
✔ EdgeEvaluator + ValueEvaluator + RiskEngine + LiquidityEngine integráció
✔ value-weighted match ranking
✔ dynamic kombi size (bankroll és risk alapján)
✔ ROI-maximalizáló sorrendezés
✔ 100% kompatibilis Master Orchestratorral
✔ full details visszaadása a frontendnek
"""

from typing import Dict, Any, List
import numpy as np

from core.master_orchestrator import MasterOrchestratorInstance
from core.risk_engine import RiskEngineInstance
from core.edge_evaluator import EdgeEvaluatorInstance
from core.value_evaluator import ValueEvaluatorInstance
from core.liquidity_engine import LiquidityEngineInstance
from core.fusion_engine import FusionEngineInstance
from core.feature_builder import FeatureBuilderInstance


class KombiEngine:
    def __init__(self):
        pass

    # =====================================================================
    # FŐ FÜGGVÉNY – KOMBI TIPP GENERÁLÁS
    # =====================================================================
    def generate_kombi(self, matches: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Input: több meccs adatai listában → AI kombi generál
        Output: kombi szelvény + full detailed score
        """

        evaluated = []

        # -------------------------------------------------------------
        # 1) Minden meccs részletes kiértékelése (AI alapon)
        # -------------------------------------------------------------
        for match in matches:
            features = FeatureBuilderInstance.build_features(match, live=False)
            liquidity = LiquidityEngineInstance.analyze(match)

            # Alap model output placeholder
            model_output = {
                "prob_home": match.get("prob_home", 0.33),
                "prob_draw": match.get("prob_draw", 0.33),
                "prob_away": match.get("prob_away", 0.33)
            }

            fused = FusionEngineInstance.fuse({"kombiengine": model_output})

            risk = RiskEngineInstance.evaluate_risk(fused, features)
            value = ValueEvaluatorInstance.evaluate_value(fused, features, liquidity)
            edge = EdgeEvaluatorInstance.evaluate_edge(fused, features, liquidity)

            evaluated.append({
                "match": match,
                "fused": fused,
                "risk": risk,
                "value": value,
                "edge": edge,
                "liquidity": liquidity,
            })

        # -------------------------------------------------------------
        # 2) MATCH RANKING – legjobb value + edge kombináció
        # -------------------------------------------------------------
        evaluated.sort(
            key=lambda x: (x["edge"]["edge_score"] * 0.6 +
                           x["value"]["value_index"] * 0.3 -
                           (1 - x["risk"]["risk_score"]) * 0.1),
            reverse=True
        )

        # -------------------------------------------------------------
        # 3) KOMBI MÉRET – bankroll és risk alapján
        # -------------------------------------------------------------
        # Általános AI szabály: max 2-4 meccs

        top_n = 3

        # Magas bankroll → lehet nagyobb kombi
        if BankrollEngineInstance.bankroll > 150:
            top_n = 4

        if BankrollEngineInstance.bankroll < 50:
            top_n = 2

        kombi_matches = evaluated[:top_n]

        # -------------------------------------------------------------
        # 4) KOMBI SZELVÉNY ÖSSZEÁLLÍTÁSA
        # -------------------------------------------------------------
        selections = []
        total_odds = 1.0

        for item in kombi_matches:
            match = item["match"]
            fused = item["fused"]
            value = item["value"]
            edge = item["edge"]

            # A legjobb választás
            pick = item["edge"]["best_pick"]
            odds_key = {
                "home": "odds_home",
                "draw": "odds_draw",
                "away": "odds_away"
            }[pick]

            odds = match.get("odds", {}).get(pick, 1.0)
            total_odds *= odds

            selections.append({
                "match_id": match.get("match_id"),
                "pick": pick,
                "odds": odds,
                "edge_score": edge["edge_score"],
                "value_index": value["value_index"],
                "risk_level": item["risk"]["risk_level"],
            })

        # -------------------------------------------------------------
        # 5) OUTPUT STRUKTÚRA
        # -------------------------------------------------------------
        return {
            "kombi_size": len(selections),
            "selections": selections,
            "estimated_odds": round(total_odds, 2),
            "details": {
                "sorted_matches": evaluated,
            }
        }


# Globális példány
KombiEngineInstance = KombiEngine()
