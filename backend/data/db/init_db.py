# backend/data/db/init_db.py

import sqlite3
import os

DB_PATH = "backend/data/db/training.db"

def init_db():
    # létrehozzuk a mappát, ha nincs
    os.makedirs("backend/data/db", exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # --- 1) matches table ---
    cur.execute("""
        CREATE TABLE IF NOT EXISTS matches (
            match_id TEXT PRIMARY KEY,
            league TEXT,
            team_home TEXT,
            team_away TEXT,
            date TEXT,
            result INTEGER,
            closing_odds REAL,
            predicted_probability REAL,
            predicted_value REAL,
            created_at TEXT
        );
    """)

    # --- 2) engine_features table ---
    cur.execute("""
        CREATE TABLE IF NOT EXISTS engine_features (
            match_id TEXT,
            features BLOB,
            created_at TEXT,
            PRIMARY KEY (match_id)
        );
    """)

    # --- 3) training_labels table ---
    cur.execute("""
        CREATE TABLE IF NOT EXISTS training_labels (
            match_id TEXT,
            label_value REAL,
            profit REAL,
            final_ev REAL,
            created_at TEXT,
            PRIMARY KEY (match_id)
        );
    """)

    conn.commit()
    conn.close()
    print("SQLite training.db created successfully.")


if __name__ == "__main__":
    init_db()
