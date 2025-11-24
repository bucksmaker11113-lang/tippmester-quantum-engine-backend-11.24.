# backend/engine/anomaly_engine.py
# Javított, optimalizált Anomaly Engine
# - Match data quality check
# - Statistical outlier detection
# - Pattern inconsistency scan
# - CPU–light, kvant modellekhez kompatibilis

import numpy as np

class AnomalyEngine:
    def __init__(self, z_threshold: float = 2.8):
        self.z_threshold = z_threshold

    def detect(self, match_data: dict) -> dict:
        """
        Detects anomalies in match features.
        Example anomalies:
        - abnormal odds drift
        - extreme goal expectancy
        - inconsistent team strength metrics
        """
        anomalies = []

        # --- Odds drift anomaly ---
        if "opening_odds" in match_data and "current_odds" in match_data:
            try:
                opening = float(match_data["opening_odds"])
                current = float(match_data["current_odds"])
                drift = abs(current - opening)

                if drift > opening * 0.25:  # 25% odds shift
                    anomalies.append("high_odds_drift")
            except:
                pass

        # --- Statistical features anomaly ---
        numeric_fields = []
        for key, val in match_data.items():
            if isinstance(val, (int, float)):
                numeric_fields.append(val)

        if len(numeric_fields) >= 3:
            arr = np.array(numeric_fields)
            z_scores = np.abs((arr - np.mean(arr)) / (np.std(arr) + 1e-9))

            if np.max(z_scores) > self.z_threshold:
                anomalies.append("statistical_outlier")

        # --- Team strength consistency ---
        if "home_strength" in match_data and "away_strength" in match_data:
            hs = match_data["home_strength"]
            as_ = match_data["away_strength"]

            if abs(hs - as_) > 50:  # unrealistic rating gap
                anomalies.append("team_strength_gap")

        return {
            "anomalies": anomalies,
            "is_anomalous": len(anomalies) > 0
        }
