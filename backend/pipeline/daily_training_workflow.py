# backend/pipelines/daily_training_workflow.py
# Napi automatikus újratanulás és adatfrissítés
# Profibb sportfogadási rendszerekben a modellek napi frissítése alapelv
# - Feature update
# - Model retrain
# - Odds drift figyelés előkészítve
# - Minimal CPU terheléshez optimalizálva

import datetime
from backend.core.model_registry import ModelRegistry
from backend.engine.feature_builder import FeatureBuilder
from backend.engine.model_trainer import ModelTrainer


class DailyTrainingWorkflow:
    def __init__(self):
        self.registry = ModelRegistry()
        self.feature_builder = FeatureBuilder()
        self.trainer = ModelTrainer()

    def run_daily_retrain(self, historical_dataset: list):
        """
        Napi automatikus retrain.
        A dataset külső forrásból érkezik (cron/script/API).
        """
        print(f"[TRAINING] Retraining models on {datetime.date.today()}")

        # 1) Feature készítés
        features, labels = self.feature_builder.build_training_dataset(historical_dataset)

        # 2) Model retrain
        model = self.trainer.train(features, labels)

        # 3) Model registry update
        self.registry.save_model(model)

        print("[TRAINING] Daily retrain completed.")
        return True
