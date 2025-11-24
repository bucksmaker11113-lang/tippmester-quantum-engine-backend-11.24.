# backend/reporting/bankroll_updater.py

class BankrollUpdater:
    """
    BANKROLL UPDATER
    ----------------
    Feladata:
        - tippek eredményének elszámolása
        - bankroll frissítése
        - kombi tippek elszámolása
        - prop fogadások kezelése
    """

    def __init__(self, config):
        self.config = config

    # -----------------------------------------------------------
    # FŐ FÜGGVÉNY
    # -----------------------------------------------------------
    def update_bankroll(self, bankroll, tips, results):
        """
        bankroll: kiinduló bankroll
        tips: tipp lista
        results: API/scraper által visszaadott eredmények
        """
        current = bankroll

        for tip in tips:

            match_id = tip["match_id"]
            res = results.get(match_id, {})

            if not res:
                continue

            outcome = res.get("result")
            odds = tip["odds"]
            stake = tip["stake"]

            # WIN
            if outcome == "win":
                profit = round(stake * (odds - 1), 2)
                current += profit
                res["profit"] = profit

            # LOSS
            elif outcome == "loss":
                current -= stake
                res["profit"] = -stake

            # PUSH (Asian handicap)
            elif outcome == "push":
                res["profit"] = 0

        return round(current, 2)
