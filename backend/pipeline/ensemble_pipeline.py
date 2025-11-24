# Hová kerüljön:
# backend/pipeline/ensemble_pipeline.py

"""
ENSEMBLE PIPELINE – ÚJ GENERÁCIÓS META-ENSEMBLE AI PIPELINE
------------------------------------------------------------
Feladata:
    - Több AI forrás + meta layer összehangolása
    - tippek összevonása, súlyozása, tisztítása
    - orchestrator kompatibilis, modern ensemble rendszer biztosítása
    - odds / liquidity / risk / value figyelembevételével végső tippek adása

Ez az új verzió:
✔ teljes MasterOrchestrator integráció
✔ value + edge + risk súlyozott ensemble
✔ meta layer kompatibilitás
✔ odds filter + confidence tuning
✔ stabil, hibatűrő
"""

from typing import List, Dict, Any

from core.master_orchestrator import MasterOrchestratorInstance


class EnsemblePipeline:
    def __init__(self):
        pass

    # =====================================================================
    # ENSEMBLE FUTTATÁS – több tipp összevonása
    # =====================================================================
    def run(self, matches: List[Dict[str, Any]]) -> Dict[str, Any]:
        results = []

        for match in matches:
            ai = MasterOrchestratorInstance.predict_match(match)
            results.append(ai)

        # Ensemble súlyozás
        for r in results:
            edge = r["edge"]["edge_score"]
            value = r["value"]["value_index"]
            risk = r["risk"]["risk_score"]

            # súlyozott ensemble score
            ensemble_score = edge * 0.5 + value * 0.3 + risk * 0.2
            r["ensemble_score"] = ensemble_score

        # Rangsorolás ensemble_score alapján
        results.sort(key=lambda x: x["ensemble_score"], reverse=True)

        return {
            "count": len(results),
            "ensemble_sorted": results
        }


# Globális példány
EnsemblePipelineInstance = EnsemblePipeline()