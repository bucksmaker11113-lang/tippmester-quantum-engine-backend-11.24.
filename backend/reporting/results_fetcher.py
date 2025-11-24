# backend/reporting/results_fetcher.py

import requests
from bs4 import BeautifulSoup
from backend.utils.logger import get_logger

class ResultsFetcher:
    """
    EREDMÉNY LEKÉRDEZŐ ENGINE
    -------------------------
    Scraping alapú:
        - SofaScore
        - FlashScore
        - LiveScore
    """

    def __init__(self):
        self.logger = get_logger()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0"
        })

    # -----------------------------------------------------------
    # SOFASCORE SCRAPER (STUB)
    # -----------------------------------------------------------
    def fetch(self, home, away):
        """
        Visszaadja:
            {
                "result": "win/loss/push",
                "score": "1-2"
            }
        """

        # STUB — később specifikus HTML alapján rakjuk össze
        return {
            "result": "win",
            "score": "2-1"
        }
