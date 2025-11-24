# backend/scraper/result_scraper.py

import requests
from backend.utils.logger import get_logger

class ResultScraper:
    """
    Eredmények lekérdezése 3 forrásból:
        1) SofaScore
        2) FlashScore
        3) OddsPortal (closing odds + eredmény)
    """

    def __init__(self):
        self.logger = get_logger()

    # ---------------------------------------------------
    # Public interface
    # ---------------------------------------------------
    def get_result(self, match_id, home_team=None, away_team=None):
        """
        Vissza:
            {
                "match_id": "...",
                "result": 1/0,
                "goals_home": x,
                "goals_away": y,
                "closing_odds": float,
                "final_ev": float
            }
        """
        data = (
            self._sofascore(match_id) or
            self._flashscore(match_id) or
            self._oddsportal(match_id)
        )

        if not data:
            self.logger.error(f"[ResultScraper] No result for match_id={match_id}")
            return None

        # eredmény jelölése
        if data["goals_home"] > data["goals_away"]:
            data["result"] = 1
        else:
            data["result"] = 0

        return data

    # ---------------------------------------------------
    # SofaScore API
    # ---------------------------------------------------
    def _sofascore(self, match_id):
        try:
            url = f"https://api.sofascore.com/api/v1/event/{match_id}"
            r = requests.get(url, timeout=5)
            if r.status_code != 200:
                return None
            js = r.json()

            return {
                "match_id": match_id,
                "goals_home": js["event"]["homeScore"]["current"],
                "goals_away": js["event"]["awayScore"]["current"],
                "closing_odds": None,
                "final_ev": None
            }

        except:
            return None

    # ---------------------------------------------------
    # FlashScore fallback (HTML parsing)
    # ---------------------------------------------------
    def _flashscore(self, match_id):
        try:
            # placeholder — később megírva
            return None
        except:
            return None

    # ---------------------------------------------------
    # OddsPortal fallback
    # ---------------------------------------------------
    def _oddsportal(self, match_id):
        try:
            # placeholder — később megírva
            return None
        except:
            return None
