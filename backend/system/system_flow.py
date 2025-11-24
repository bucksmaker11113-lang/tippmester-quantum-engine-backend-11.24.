# Hová kerüljön:
# backend/system/system_flow.py

"""
SYSTEM FLOW – MEGÚJÍTOTT RENDSZERFOLYAM / AI WORKFLOW VEZÉRLÉS
-----------------------------------------------------------------
Feladata:
    - napi AI futások ütemezése (pipeline + pro-generator + kombi)
    - orchestrator vezérlése
    - tippek mentése / export / loggolás
    - időzített folyamatok indítása schedulerből

Ez az új verzió:
✔ MasterOrchestrator integráció
✔ új pipeline modulok használata (tip_pipeline, tip_generator_pro)
✔ hibatűrés és loggolás
✔ kompatibilis schedulerrel
✔ JSON output generálás tippekhez
"""

import json
import datetime
from typing import List, Dict, Any

from pipeline.tip_pipeline import TipPipelineInstance
from pipeline.tip_generator_pro import TipGeneratorProInstance
from core.kombi_engine import KombiEngineInstance
from core.master_orchestrator import MasterOrchestratorInstance


class SystemFlow:
    def __init__(self):
        self.last_run = None

    # =====================================================================
    # NAPI AI FUTÁS
    # =====================================================================
    def run_daily_ai(self, matches: List[Dict[str, Any]]) -> Dict[str, Any]:
        print("[SYSTEM] Napi AI tipp-generálás indult…")

        # 1) TipPipeline – általános tippek
        pipeline_output = TipPipelineInstance.generate_tips(matches)

        # 2) TipGeneratorPro – profi tippek + kombi szelvény
        pro_output = TipGeneratorProInstance.generate(matches)

        # 3) KombiEngine – külön is futtatható
        kombi_output = KombiEngineInstance.generate_kombi(matches[:10])

        # 4) Időbélyeg
        timestamp = datetime.datetime.utcnow().isoformat()
        self.last_run = timestamp

        # 5) Aggregált output
        output = {
            "timestamp": timestamp,
            "pipeline": pipeline_output,
            "pro": pro_output,
            "kombi": kombi_output
        }

        return output

    # =====================================================================
    # TIPPEK EXPORTÁLÁSA JSON FORMÁBAN
    # =====================================================================
    def export_tips(self, results: Dict[str, Any], path: str) -> None:
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"[SYSTEM] Tippek exportálva → {path}")
        except Exception as e:
            print("[SYSTEM] Export hiba:", e)

    # =====================================================================
    # GYORS TEST FUTTATÁS (manual)
    # =====================================================================
    def test_run(self) -> Dict[str, Any]:
        print("[SYSTEM] Test run…")
        sample_match = {
            "match_id": "TEST123",
            "home_team": "Team A",
            "away_team": "Team B",
            "odds": {"home": 2.1, "draw": 3.3, "away": 3.5},
            "form_home": [1, 0, 1, 1],
            "form_away": [0, 1, 0, 0],
            "prob_home": 0.52,
            "prob_draw": 0.24,
            "prob_away": 0.24,
        }

        return self.run_daily_ai([sample_match])


# Globális példány
SystemFlowInstance = SystemFlow()
