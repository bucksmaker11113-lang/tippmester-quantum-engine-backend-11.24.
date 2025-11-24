# Hová kerüljön:
# backend/pipeline/tip_pipeline.py

"""
TIP PIPELINE – ÚJ GENERÁCIÓS, MASTER-ORCHESTRATOR ALAPÚ TIPP GENERÁLÓ
-----------------------------------------------------------------------
Feladata:
    - prematch tippek generálása a teljes AI rendszer felhasználásával
    - orchestrator hívása meccsenként
    - value/edge/risk alapú rendezés
    - top-tippek kiválasztása a frontendnek

Ez az új verzió:
✔ MasterOrchestrator integráció
✔ teljes AI output használata
✔ tip ranking (edge + value + risk együttesen)
✔ full-detail válasz a frontendnek
✔ kompatibilis kombi engine-nel és live engine-nel
"""

from typing import List, Dict, Any

from core.master_orchestrator import MasterOrchestratorInstance


class TipPipeline:
    def __init__(self):
        pass

    # =====================================================================
    # FŐ FÜGGVÉNY – PREMATCH TIPPEK GENERÁLÁSA
    # =====================================================================
    def generate_tips(self, matches: List[Dict[str, Any]]) -> Dict[str, Any]:
        evaluated = []

        # 1) MasterOrchestrator-rel minden meccs AI-értékelése
        for match in matches:
            result = MasterOrchestratorInstance.predict_match(match)
            evaluated.append(result)

        # 2) Rangsorolás – edge + value + risk kombinációja
        evaluated.sort(
            key=lambda x: (
                x["edge"]["edge_score"] * 0.5 +
                x["value"]["value_index"] * 0.35 +
                x["risk"]["risk_score"] * 0.15
            ),
            reverse=True
        )

        # 3) TOP 10 tipp kiválasztása
        top_tips = evaluated[:10]

        # 4) Frontend-kompatibilis struktúra
        return {
            "count": len(top_tips),
            "tips": top_tips,
            "sorted_all": evaluated
        }


# Globális példány
TipPipelineInstance = TipPipeline()
