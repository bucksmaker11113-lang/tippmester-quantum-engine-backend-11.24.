# backend/reporting/prop_report_integrator.py

class PropReportIntegrator:
    """
    PROP REPORT INTEGRATOR
    ----------------------
    Feladat:
        - A prop tippeket a napi riport formátumába illeszti
        - Minden prop tipphez egységes mezők tartoznak
        - BankrollUpdatert kompatibilissé teszi prop piacokkal
    """

    def __init__(self, config=None):
        self.config = config or {}

    # ---------------------------------------------------------
    # PROP TIPPEK FORMÁLÁSA RIPORTHOZ
    # ---------------------------------------------------------
    def format_prop_tip(self, match_info, prop_tip):
        """
        match_info:
            - match_id
            - home
            - away

        prop_tip:
            - market
            - type (totals, handicap, btts, cards, corners, player_prop)
            - prob
            - value
            - odds
            - confidence
            - risk
            - stake
        """

        return {
            "match_id": match_info["match_id"],
            "match": f"{match_info['home']} - {match_info['away']}",
            "market": prop_tip["market"],
            "market_category": prop_tip["type"],
            "tip_type": "prop",

            "probability": prop_tip.get("prob", 0),
            "value_score": prop_tip.get("value", 0),
            "odds": prop_tip.get("odds", 1.0),
            "confidence": prop_tip.get("confidence", 0.0),

            "risk": prop_tip.get("risk", 0.0),
            "stake": prop_tip.get("stake", 0.0),

            # később → actual result scraper
            "result": "pending"
        }

    # ---------------------------------------------------------
    # PROP TIPPEK HOZZÁADÁSA A RIORTLISTÁHOZ
    # ---------------------------------------------------------
    def integrate(self, tip_list, prop_tips, match_info):
        """
        tip_list → meglévő single + kombi tippek
        prop_tips → PropEngine által generált lista
        match_info → csapatnevek, match_id
        """

        for p in prop_tips:
            formatted = self.format_prop_tip(match_info, p)
            tip_list.append(formatted)

        return tip_list
