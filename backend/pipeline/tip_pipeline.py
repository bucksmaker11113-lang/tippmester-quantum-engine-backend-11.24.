# backend/pipelines/tip_pipeline.py
# Optimalizált Tipp Pipeline
# - MasterPipeline használata
# - Input normalizálás
# - Egységes tippszolgáltatás Single/Kombi/Live esetén

from backend.pipelines.master_pipeline import MasterPipeline


class TipPipeline:
    def __init__(self):
        self.master = MasterPipeline()

    def generate_single_tip(self, match_data: dict):
        """
        Egyetlen meccs tipppipeline-ja.
        """
        return self.master.run(match_data)

    def generate_kombi_tips(self, matches: list):
        """
        Kombi tipp (több meccs) pipeline.
        Az egyes tippek összevonása FusionEngine által.
        """
        output = []
        for m in matches:
            tip = self.master.run(m)
            output.append(tip)
        return output

    def generate_live_tip(self, live_data: dict):
        """
        Élő meccs predikció.
        Később: hozzáadható odds drift engine.
        """
        return self.master.run(live_data)
