# backend/core/training_pipeline.py

import os
import sqlite3
import numpy as np
from datetime import datetime
from backend.utils.logger import get_logger


class TrainingPipeline:
    """
    TRAINING PIPELINE – PRO VERSION
    --------------------------------
    Feladata:
        • Training dataset gyűjtése SQLite-ba
        • Features + meta input + label + EV + profit tárolása
        • Modell újratanítás előkészítése
        • Mini-batch export CSV/NumPy formátumban
    """

    def __init__(self, config=None):
        self.config = config or {}
        self.logger = get_logger()

        path = self.config.get("training", {}).get("db_path", "training.db")
        self.db_path = path

        self._init_db()

    # ===================================================================
    #  DATABASE INITIALIZATION
    # ===================================================================
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        # Main table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS training_samples (
                match_id TEXT PRIMARY KEY,
                features BLOB,
                meta_features BLOB,
                label REAL,
                ev REAL,
                profit REAL,
                created_at TEXT
            )
        """)

        conn.commit()
        conn.close()

        self.logger.info("[TrainingPipeline] Database initialized.")

    # ===================================================================
    #  SAVE ONE SAMPLE
    # ===================================================================
    def save_sample(self, match_id, features, meta_features, label, ev, profit):
        """
        features      → FeatureBuilder output (numpy vector)
        meta_features → MetaInputBuilder output (numpy vector)
        label         → LabelGenerator output
        ev            → expected value
        profit        → actual profit
        """

        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        cur.execute("""
            INSERT OR REPLACE INTO training_samples
            (match_id, features, meta_features, label, ev, profit, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            match_id,
            features.tobytes(),
            meta_features.tobytes(),
            float(label),
            float(ev),
            float(profit),
            datetime.utcnow().isoformat()
        ))

        conn.commit()
        conn.close()

        self.logger.info(f"[TrainingPipeline] Sample saved → {match_id}")

    # =========================================
