# backend/core/tip_selector.py

import numpy as np
from backend.utils.logger import get_logger


class TipSelector:
    """
    TIP SELECTOR – PRO VERSION
    --------------------------
    Feladata:
        • Single tippek kiválasztása (napi 4)
        • Kombi tippek jelöltjeinek összegyűjtése
        • Live tippek szelekciója külön logikával
        • Prop tippek kiszűrése (külön piac)
        • Risk, value, reliability, probability alapú döntés
        • TippmixPro availability figyelembevétele
        • Odds limit és risk limit kezelése
    """

    def __init__(self, config=None):
        self.config = config or {}

        sel = self.config.get("selector", {})

        # Single tipp limitek
        self.max_singles = sel.get("max_singles", 4)
        self.min_value = sel.get("min_value", 0.05)
        self.max_risk = sel.get("max_risk", 0.65)
        self.min_reliability = sel.get("min_reliability", 0.40)

        # TippmixPro kötelező?
        self.require_tmx = sel.get("require_tmx", True)

        # Live tip limit
        self.max_live = sel.get("max_live", 3)

        # Prop tip limit
        self.max_prop = sel.get("max_prop", 3)

        self.logger = get_logger()

    # ======================================================================
    # HELPER: TIPP VALIDÁLÁSA
    # ======================================================================
    def _is_valid_tip(self, f_out, match_data):
        """Single tip validáció"""

        p = f_out.get("probability", 0.50)
        v = f_out.get("value", f_out.get("value_score", 0.0))
        r = f_out.get("risk", 0.5)
        rel = f_out.get("reliability", 0.5)

        # TippmixPro elérhetőség
        if self.require_tmx and not match_data.get("tmx_available", False):
            return False

        # Value határ
        if v < self.min_value:
            return False

        # Risk határ
        if r > self.max_risk:
            return False
