# backend/pipeline/ensemble_pipeline.py

from backend.core.fusion_engine import FusionEngine
from backend.core.bayesian_updater import BayesianUpdater
from backend.core.bias_engine import BiasEngine
from backend.core.value_analyzer import ValueAnalyzer
from backend.engine.deep_value_engine import DeepValueEngine
from backend.core.feature_builder import FeatureBuilder

class EnsemblePipeline:
    """
    A teljes predikciós rendszer:
        1) quantumsynth (felsőbb modell hívja)
        2) fusion layer
        3) bayesian update
        4) bias correction
        5) value analyzer (klasszikus)
        6) deep value engine (deep learning)
    """

    def __init__(self, config):
        self.config = config
        self.fusion = FusionEngine(config)
        self.bayes = BayesianUpdater(config)
        self.bias = BiasEngine(config)
        self.value = ValueAnalyzer(config)
        self.deep = DeepValueEngine(config)
        self.builder = FeatureBuilder(config)

    def run(self, model_outputs, raw_odds):
        """
        model_outputs = {
            "mc3": {...},
            "poisson": {...},
            ...
        }
        raw_odds = odds data
        """

        # 1) Fusion layer (Layer 2)
        fused = self.fusion.combine(model_outputs)

        # 2) Bayesian refinement (Layer 3)
        posterior = self.bayes.update(fused)

        # 3) Bias correction (Layer 4)
        corrected = self.bias.apply(posterior)

        # 4) Value analyzer (Layer 5)
        for m_id in corrected:
            corrected[m_id]["odds"] = raw_odds.get(m_id, {})
        value_data = self.value.evaluate(corrected)

        # 5) Deep value engine (Layer 6)
        final = {}
        fv_map = {}

        # feature input
        for match_id, data in value_data.items():
            fv = self.builder.build_feature_vector(model_outputs)
            fv_map[match_id] = {"features": fv}

        deep_pred = self.deep.predict(fv_map)

        # merge
        for match_id in value_data:
            final[match_id] = {
                **value_data[match_id],
                "deep_value": deep_pred[match_id]["value_score"],
                "deep_conf": deep_pred[match_id]["confidence"]
            }

        return final
