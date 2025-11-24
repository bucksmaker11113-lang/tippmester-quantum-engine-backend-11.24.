# backend/core/label_generator.py

import numpy as np


class LabelGenerator:
    """
    LABEL GENERATOR – PRO VERSION
    ------------------------------
    Kimenet: 0–1 közötti tanító címke DeepValue és Ensemble modellekhez.

    A címke 3 komponensből áll össze:

        1) base_label    → meccs bejött-e (0/1)
        2) ev_label      → expected value normalizált értéke
        3) profit_label  → tényleges profit normalizálva

    A teljes címke:
        label = base*w1 + ev*w2 + profit*w3

    Mindezt clamppeljük: [0,1]
    """

    def __init__(self, config=None):
        cfg = config or {}
        lg = cfg.get("label", {})

        # Súlyok
        self.w_base = lg.get("base_weight", 0.40)
        self.w_ev = lg.get("ev_weight", 0.35)
        self.w_profit = lg.get("profit_weight", 0.25)

        # EV normálási határok
        self.ev_scale = lg.get("ev_scale", 0.20)

        # Profit skála faktor
        self.profit_scale = lg.get("profit_scale", 1.5)

    # ======================================================================
    # Fő függvény → egyetlen minta labeljének kiszámítása
    # ======================================================================
    def compute_label(self, result, ev, profit):
        """
        result → 1 ha jött a tipp, 0 ha elment
        ev → expected value (pl +0.12)
        profit → tényleges profit euróban

        Mindhárom darabnyi információ → egyetlen ML-címkévé áll össze.
        """

        # --- 1) base label ---
        base_label = float(result)

        # --- 2) EV normalizálása ---
        ev_norm = np.clip(ev / self.ev_scale, -1, 1)
        ev_label = (ev_norm + 1) / 2

        # --- 3) Profit normalizálása ---
        # profit lehet: -tét, +nyeremény
        profit_norm = np.tanh(profit * self.profit_scale)
        profit_label = (profit_norm + 1) / 2

        # --- 4) Súlyozott összeg ---
        label = (
            base_label * self.w_base +
            ev_label * self.w_ev +
            profit_label * self.w_profit
        )

        # --- 5) clamp: [0,1] ---
        return float(np.clip(label, 0.0, 1.0))

    # ======================================================================
    # Napi eredményekből label-ek generálása
    # ======================================================================
    def generate_labels(self, results):
        """
        results = [
            {
                "match_id": "...",
                "result": 1/0,
                "ev": 0.12,
                "profit": +3.5,
                "features": {...}
            },
            ...
        ]

        Visszatér:
            {
                match_id: {
                    "label": ...,
                    "features": ...
                }
            }
        """

        out = {}

        for item in results:
            match_id = item["match_id"]
            result = float(item.get("result", 0))
            ev = float(item.get("ev", 0.0))
            profit = float(item.get("profit", 0.0))
            features = item.get("features", {})

            label = self.compute_label(result, ev, profit)

            out[match_id] = {
                "label": label,
                "features": features
            }

        return out
