# backend/core/meta_input_builder.py

import numpy as np
from backend.utils.logger import get_logger


class MetaInputBuilder:
    """
    META INPUT BUILDER – PRO VERSION
    ---------------------------------
    Feladata:
        • FusionEngine + összes engine output → meta-feature input
        • MTX / International odds különbségek
        • Drift, volatility, bias, reliability egyesítése
        • Liga, sportág, idő kontextus beépítése
        • Végső ML-barát vektor előállítása (128–256 dim.)
    """

    def __init__(self, config=None):
        self.config = config or {}
        self.logger = get_logger()

        self.output_dim = self.config.get("meta", {}).get("input_dim", 128)

    # ---------------------------------------------------------------------
    # Normalizáló helper
    # ---------------------------------------------------------------------
    def _norm(self, x, lo, hi):
        try:
            return float((x - lo) / (hi - lo))
        except:
            return 0.5

    # ---------------------------------------------------------------------
    # TippmixPro odds különbség
    # ----------------
