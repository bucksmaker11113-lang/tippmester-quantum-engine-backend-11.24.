# backend/pipeline/odds_filter.py

class OddsFilter:
    """
    ODDS FILTER ENGINE
    ------------------
    1.60 alatti odds csak akkor mehet át, ha:
        - prob > 0.78
        - confidence > 0.70
        - deep_value > 0.55
        - risk < 0.38
        - fair_value_edge > +0.07
        - expected_closing > current_odds
    """

    def __init__(self, config=None):
        self.config = config or {}

        self.min_odds = 1.60
        self.min_prob = 0.78
        self.min_conf = 0.70
        self.min_deep_value = 0.55
        self.max_risk = 0.38
        self.min_ev_edge = 0.07   # +7%

    # -----------------------------------------------------------
    # FŐ LOGIKA
    # -----------------------------------------------------------
    def allow_tip(self, tip):
        odds = tip["odds"]
        prob = tip["probability"]
        conf = tip["confidence"]
        deep_val = tip.get("deep_value", 0)
        risk = tip.get("risk", 0)
        fair_odds = tip.get("fair_odds", odds)
        closing_estimate = tip.get("expected_closing_line", odds)

        # 1) Ha 1.60 vagy felette → ENGEDÉLYEZETT (ha value van)
        if odds >= self.min_odds:
            return True

        # 2) 1.60 alatti → szigorú bizonyítás
        # -----------------------------------------------------

        # 2/A) Probability
        if prob < self.min_prob:
            return False

        # 2/B) Confidence
        if conf < self.min_conf:
            return False

        # 2/C) Deep Value
        if deep_val < self.min_deep_value:
            return False

        # 2/D) Risk
        if risk > self.max_risk:
            return False

        # 2/E) Fair odds edge
        # fair_value_edge = (fair_odds / odds) - 1
        fair_edge = (fair_odds / odds) - 1
        if fair_edge < self.min_ev_edge:
            return False

        # 2/F) Closing line expectation
        if closing_estimate <= odds:
            return False

        # Ha minden feltétel teljesül → átmehet
        return True
