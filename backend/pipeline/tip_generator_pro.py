# backend/pipeline/tip_generator_pro.py

from backend.core.bankroll_engine import BankrollEngine
from backend.core.risk_engine import RiskEngine
from backend.scraper.tippmixpro_scraper import TippmixProScraper


class TipGeneratorPro:
    """
    TIPPGENERATOR PRO v2
    ---------------------
    Több-lépcsős tippgyártó rendszer:
        - DeepValue AI
        - Value Score
        - Risk Engine
        - Bankroll Engine
        - TippmixPro availability
        - Prioritási pontszám
        - Single | Kombi | Live tippek
    """

    def __init__(self, config):
        self.config = config
        self.bankroll_engine = BankrollEngine(config)
        self.risk_engine = RiskEngine(config)
        self.tippmixpro = TippmixProScraper()

        self.max_single = 4
        self.max_kombi = 3

    # ---------------------------------------------------------------
    # PRIORITY SCORE (Deep + Value + Conf + Risk)
    # ---------------------------------------------------------------
    def _priority(self, p):
        """
        0–100 pont közötti priorizálás.
        """
        deep = p.get("deep_value", 0)
        value = p.get("value_score", 0)
        conf = p.get("confidence", 0)
        risk = p.get("risk", 0.5)

        # minél kisebb kockázat annál jobb
        risk_adj = (1 - risk)

        score = (
            deep * 40 +
            value * 25 +
            conf * 25 +
            risk_adj * 10
        )

        return round(score, 1)

    # ---------------------------------------------------------------
    # TippmixPro ellenőrzés
    # ---------------------------------------------------------------
    def _tippmix_filter(self, match_info):
        home = match_info.get("home")
        away = match_info.get("away")

        res = self.tippmixpro.check_match(home, away)
        if not res["exists"]:
            return False, {}, False

        return True, res["odds"], res["available"]

    # ---------------------------------------------------------------
    # SINGLE TIPP GENERÁLÁS
    # ---------------------------------------------------------------
    def generate_single(self, predictions, bankroll):
        tips = []

        for m_id, p in predictions.items():

            # TippmixPro check
            exists, tmp_odds, available = self._tippmix_filter(p)
            if not exists or not available:
                continue

            # Priorizálás
            prio = self._priority(p)
            if prio < 55:  
                continue

            # Kockázat számítás
            risk = self.risk_engine.compute_risk({
                "prob": p["probability"],
                "value_score": p["value_score"],
                "public_money": p.get("public", 0),
                "volatility": p.get("volatility", 0),
                "injury_risk": p.get("injury_risk", 0),
                "weather_risk": p.get("weather_risk", 0),
                "market_shift": p.get("market_shift", 0)
            })

            # Tét
            stake = self.bankroll_engine.stake(
                bankroll=bankroll,
                prob=p["probability"],
                odds=tmp_odds.get("1", p.get("odds", {"1":2.0}).get("1")),
                deep_value=p["deep_value"]
            )

            tips.append({
                "match_id": m_id,
                "priority": prio,
                "odds": tmp_odds,
                "risk": round(risk, 3),
                "stake": stake,
                "data": p
            })

        # Prioritási sorrend
        tips = sorted(tips, key=lambda x: x["priority"], reverse=True)

        return tips[: self.max_single]

    # ---------------------------------------------------------------
    # KOMBI TIPPEK
    # ---------------------------------------------------------------
    def generate_kombi(self, predictions):
        arr = []

        for m_id, p in predictions.items():
            prio = self._priority(p)
            if prio < 45:
                continue

            if p["value_score"] < 0.25:
                continue

            arr.append({
                "match_id": m_id,
                "priority": prio,
                "data": p
            })

        # 3 legjobb kombi
        arr = sorted(arr, key=lambda x: x["priority"], reverse=True)

        return arr[: self.max_kombi]

    # ---------------------------------------------------------------
    # LIVE TIPPEK
    # ---------------------------------------------------------------
    def generate_live(self, live_data, bankroll):

        tips = []
        for m_id, p in live_data.items():

            if p["game_chance"] < 0.72:
                continue

            stake = self.bankroll_engine.stake(
                bankroll=bankroll,
                prob=p.get("live_xg", 0.5),
                odds=2.0,
                deep_value=p["game_chance"]
            )

            tips.append({
                "match_id": m_id,
                "live_score": p["game_chance"],
                "stake": stake,
                "data": p
            })

        return tips
