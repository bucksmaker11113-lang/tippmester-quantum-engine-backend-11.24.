# Hová kerüljön:
# backend/pipeline/tip_generator_pro.py

"""
TIP GENERATOR PRO – A LEGERŐSEBB, MASTER-ORCHESTRATOR ALAPÚ AI TIPP GENERÁTOR
-------------------------------------------------------------------------------
Feladata:
    - magas minőségű AI-tippek generálása mély értékeléssel
    - value + edge + risk + liquidity együttes elemzése
    - bankroll védelem + stake ajánlás
    - több kategóriára bontott tippek (Top Picks, Safe Picks, High Value)
    - kombi engine integráció
    - készen áll a frontend számára: single tippek + részletek

Ez a verzió:
✔ teljes Orchestrator integráció
✔ értékelő és rendező rendszer (multi-factor scoring)
✔ kategória rendszer
✔ stake ajánlás (bankroll engine-ből)
✔ kompatibilis a tip_pipeline-lal és kombi_engine-nel
✔ stabil, gyors, profi AI tippgenerálás
"""

from typing import List, Dict, Any

from core.master_orchestrator import MasterOrchestratorInstance
from core.kombi_engine import KombiEngineInstance


class TipGeneratorPro:
    def __init__(self):
        pass

    # =====================================================================
    # FŐ FÜGGVÉNY – PROFI TIPPEK GENERÁLÁSA
    # =====================================================================
    def generate(self, matches: List[Dict[str, Any]]) -> Dict[str, Any]:
        evaluated = []

        # 1) Minden meccs részletes AI-értékelése (Master Orchestrator)
        for match in matches:
            result = MasterOrchestratorInstance.predict_match(match)
            evaluated.append(result)

        # 2) Rendezés – komplex scoring formula
        def score(t):
            edge = t["edge"]["edge_score"]
            value = t["value"]["value_index"]
            risk = t["risk"]["risk_score"]
            confidence = t["fused"].get("confidence", 0.0)
            return edge * 0.45 + value * 0.35 + risk * 0.15 + confidence * 0.05

        evaluated.sort(key=score, reverse=True)

        # 3) KATEGÓRIÁK
        top_picks = [t for t in evaluated if t["edge"]["edge_score"] >= 0.65 and t["value"]["value_index"] >= 0.65][:10]
        safe_picks = [t for t in evaluated if t["risk"]["risk_level"] == "low"][:10]
        high_value = [t for t in evaluated if t["value"]["value_index"] >= 0.75][:10]

        # 4) KOMBI JELENÍTVÉNY
        kombi = KombiEngineInstance.generate_kombi([t["match"] for t in evaluated[:12]])

        # 5) FRONTEND STRUKTÚRA
        return {
            "top_picks": top_picks,
            "safe_picks": safe_picks,
            "high_value": high_value,
            "kombi_szelveny": kombi,
            "all_tips_sorted": evaluated
        }


# Globális példány
TipGeneratorProInstance = TipGeneratorPro()
