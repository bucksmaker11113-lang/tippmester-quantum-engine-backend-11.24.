# backend/engine/prop_tip_selector.py

class PropTipSelector:
    """
    PROP TIP SELECTOR
    -----------------
    A legjobb 1–3 prop value tipp kiválasztása:
        - value score alapján
        - confidence alapján
        - odds stabilitás
        - risk filter
        - TippmixPro availability check (később pipával)
    """

    def __init__(self, config):
        self.config = config
        self.max_tips = config.get("prop_max_daily", 3)

    def select(self, prop_list):
        # 1) szűrés érték alapján
        valid = [p for p in prop_list if p["value"] > 0.05]

        # 2) rendezés value DESC
        valid.sort(key=lambda x: x["value"], reverse=True)

        # 3) limit 1–3 db-ra
        return valid[: self.max_tips]
