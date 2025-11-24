# backend/pipelines/master_pipeline.py
# Új, optimalizált pipeline logika sportfogadási AI-hoz
# - Stabil sorrend: FeatureBuilder → ModelPredictor → BayesianUpdater → OddsEngine → TipGenerator
# - CPU-optimalizált, cache-elhető
# - Felkészítve kvant modulokra

from backend.engine.feature_builder import FeatureBuilder
from backend.engine.model_predictor import ModelPredictor
from backend.engine.bayesian_updater import BayesianUpdater
from backend.engine.fusion_engine import FusionEngine
from backend.engine.value_evaluator import ValueEvaluator


class MasterPipeline:
    def __init__(self):
        self.feature_builder = FeatureBuilder()
        self.model_predictor = ModelPredictor()
        self.bayesian_updater = BayesianUpdater()
        self.fusion = FusionEngine()
        self.value_eval = ValueEvaluator()

    def run(self, raw_match_data: dict):
        """
        A tippek generálásának fő pipeline-ja.
        Ez a sorrend bizonyult a legerősebbnek:
        1. Feature builder → model input
        2. Model predictor → raw probabilities
        3. Bayesian update → stabilizált valószínűségek
        4. Value evaluator → valós érték / market edge
        5. Fusion engine → végleges tippek összevonása
        """

        # 1) Feature engineering
        features = self.feature_builder.build(raw_match_data)

        # 2) Model prediction
        base_probs = self.model_predictor.predict(features)

        # 3) Bayesian calibration
        calibrated = self.bayesian_updater.update(base_probs, raw_match_data)

        # 4) Value / odds evaluation
        value_data = self.value_eval.evaluate(calibrated, raw_match_data)

        # 5) Final fusion into tip output
        final_tip = self.fusion.fuse(value_data, raw_match_data)

        return final_tip
