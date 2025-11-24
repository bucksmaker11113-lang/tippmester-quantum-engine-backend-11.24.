import numpy as np
import pandas as pd

class AnomalyEngine:
    """
    ANOMÁLIA DETEKTOR ENGINE
    -------------------------
    Cél:
      - odds, ROI, feature értékek anomália vizsgálata
      - statisztikai threshold + Z-score alapú detektálás
      - ML modulok (RF / NN) felé küldi a tisztított adatot
    """

    def __init__(self, z_threshold=3.0):
        self.z_threshold = z_threshold

    def detect(self, series):
        """
        Bemenet: Pandas Series vagy lista
        Kimenet: anomáliák indexei és értékei
        """
        if not isinstance(series, pd.Series):
            series = pd.Series(series)

        mean = series.mean()
        std = series.std()

        if std == 0 or np.isnan(std):
            return []

        z_scores = (series - mean) / std
        anomalies = series[abs(z_scores) > self.z_threshold]

        return anomalies.to_dict()

    def is_anomaly(self, value, series):
        """
        Egyetlen értékre vizsgálja, anomália-e.
        """
        if not isinstance(series, pd.Series):
            series = pd.Series(series)

        mean = series.mean()
        std = series.std()

        if std == 0:
            return False

        z = abs((value - mean) / std)
        return z > self.z_threshold
