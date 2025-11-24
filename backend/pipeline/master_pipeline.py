# Hová kerüljön:
# backend/pipeline/master_pipeline.py

"""
MASTER PIPELINE – A TELJES TIPPMESTER AI RENDSZER FŐ CSŐVEZETÉKE
-----------------------------------------------------------------
Feladata:
    - A teljes predikciós rendszer irányítása (prematch + live előkészítés)
    - Átfogó pipeline: odds filter → orchestrator → ensemble → pro generator → kombi
    - A régi master_pipeline.py teljes kiváltása
    - Tökéletes kompatibilitás a modern AI motorokkal

Ez az új verzió:
✔ teljes MasterOrchestrator integráció
✔ OddsFilter → stabil input
✔ EnsemblePipeline → multi-lens AI értékelés
✔ TipPipeline → általános tippek
✔ TipGeneratorPro → profi, kategorizált tippek
✔ KombiEngine → optimális kombi szelvény
✔ frontendre exportálható struktúra
"""

from typing import List, Dict, Any

from pipeline.odds_filter import OddsFilterInstance
from pipeline.ensemble_pipeline import EnsemblePipelineInstance
from pipeline.tip_pipeline import TipPipelineInstance
from pipeline.tip_generator_pro import TipGeneratorProInstance
from core.kombi_engine import KombiEngineInstance
from core.master_orchestrator import MasterOrchestratorInstance


class MasterPipeline:
    def __init__(self):
        pass

    # =====================================================================
    # FŐ PREDIKCIÓS PIPELINE (PREMATCH)
    # =====================================================================
    def run(self, matches: List[Dict[str, Any]]) -> Dict[str, Any]:
        print("[MASTER] Pipeline indul…")

        # -------------------------------------------------------------
        # 1) OddsFilter → stabil odds adatok
        # -------------------------------------------------------------
        filtered_matches = []
        for m in matches:
            filtered = OddsFilterInstance.filter_odds(m)
            m["safe_odds"] = filtered["safe_odds"]
            m["volatility"] = filtered["volatility"]
            m["momentum"] = filtered["momentum"]
            filtered_matches.append(m)

        # -------------------------------------------------------------
        # 2) Master Orchestrator → teljes AI output
        # -------------------------------------------------------------
        orchestrated = [MasterOrchestratorInstance.predict_match(m) for m in filtered_matches]

        # -------------------------------------------------------------
        # 3) EnsemblePipeline → súlyozott rangsor
        # -------------------------------------------------------------
        ensemble = EnsemblePipelineInstance.run(filtered_matches)

        # -------------------------------------------------------------
        # 4) TipPipeline → top prematch tippek
        # -------------------------------------------------------------
        tip_pipeline = TipPipelineInstance.generate_tips(filtered_matches)

        # -------------------------------------------------------------
        # 5) TipGeneratorPro → profi tippek
        # -------------------------------------------------------------
        pro = TipGeneratorProInstance.generate(filtered_matches)

        # -------------------------------------------------------------
        # 6) Kombi szelvény → optimalizált kombi
        # -------------------------------------------------------------
        kombi = KombiEngineInstance.generate_kombi(filtered_matches)

        return {
            "orchestrator": orchestrated,
            "ensemble": ensemble,
            "pipeline": tip_pipeline,
            "pro": pro,
            "kombi": kombi,
        }


# Globális példány
MasterPipelineInstance = MasterPipeline()
