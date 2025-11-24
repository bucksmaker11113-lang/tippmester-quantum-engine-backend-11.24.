# backend/core/daily_training_workflow.py

import datetime
import sqlite3
import traceback

from backend.core.label_generator import LabelGenerator
from backend.core.training_pipeline import TrainingPipeline
from backend.engine.deep_value.train_value_model import DeepValueTrainer
from backend.utils.logger import get_logger


class DailyTrainingWorkflow:
    """
    DAILY TRAINING WORKFLOW – PRO VERSION
    -------------------------------------
    Feladata:
        1) Napi eredmények betöltése
        2) Label-ek generálása (LabelGenerator)
        3) Training sample mentése (SQLite)
        4) TrainingPipeline futtatása
        5) DeepValue modell újratanítása
        6) Logolt, hibatűrő működés
    """

    def __init__(self, config=None, results_loader=None):
        """
        config:
            {
                "training_db": "data/training.sqlite",
                "training_table": "samples",
                ...
            }

        results_loader:
            Külső függvény vagy objektum:
            results_loader.load_daily_results(date) → list(dict)
        """

        self.config = config or {}
        self.logger = get_logger()

        self.db_path = self.config.get("training_db", "data/training.sqlite")
        self.table = self.config.get("training_table", "samples")

        self.results_loader = results_loader

        self.label_gen = LabelGenerator(config)
        self.pipeline = TrainingPipeline(config)
        self.trainer = DeepValueTrainer(config)

        self._ensure_db_structure()

    # ======================================================================
    # DB INITIALIZATION
    # ======================================================================
    def _ensure_db_structure(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.table} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    match_id TEXT,
                    date TEXT,
                    input_features TEXT,
                    label REAL,
                    created_at TEXT
                )
            """)

            conn.commit()
            conn.close()

            self.logger.info("[DailyTrainingWorkflow] Training DB ready.")

        except Exception as e:
            self.logger.error("DB init error:")
            self.logger.error(str(e))

    # ======================================================================
    # SAVE SAMPLE TO DB
    # ======================================================================
    def _save_sample(self, match_id, features, label):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                f"INSERT INTO {self.table} (match_id, date, input_features, label, created_at) VALUES (?, ?, ?, ?, ?)",
                (
                    match_id,
                    str(datetime.date.today()),
                    str(features),
                    float(label),
                    str(datetime.datetime.utcnow())
                )
            )

            conn.commit()
            conn.close()

        except Exception as e:
            self.logger.error(f"DB insert error for {match_id}: {e}")

    # ===================================================
