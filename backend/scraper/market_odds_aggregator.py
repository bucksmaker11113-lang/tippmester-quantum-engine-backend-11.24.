# backend/scraper/market_odds_aggregator.py

import requests
from bs4 import BeautifulSoup
import random

class MarketOddsAggregator:
    """
    MARKET ODDS AGGREGATOR
    ----------------------
    Liquid piacok oddsainak letapogatása:
        - Totals (O/U 2.5)
        - Totals (O/U 3.5)
        - Asian Handicap (+1.5, +1.0, -1.5 stb.)
        - BTTS (Yes/No)
        - Cards + Corners
        - Player Props (basic: shots, goals)
    """

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Mozilla/5.0"})

    # ----------------------------------------------------
    # FŐ LETAPOGATÓ (STUB, KÉSŐBB IGAZI SCRAPERREL BŐVÜL)
    # ----------------------------------------------------
    def get_markets(self, home, away):
        # MOST: random “liquid odds” → később scrapers
        return {
            "totals": {
                "over25": round(random.uniform(1.70, 2.20), 2),
                "under25": round(random.uniform(1.70, 2.20), 2),
                "over35": round(random.uniform(2.30, 3.20), 2),
                "under35": round(random.uniform(1.30, 1.70), 2)
            },
            "handicap": {
                "+1.5": round(random.uniform(1.20, 1.65), 2),
                "-1.5": round(random.uniform(2.30, 3.50), 2),
                "+0.5": round(random.uniform(1.55, 1.95), 2),
                "-0.5": round(random.uniform(1.80, 2.40), 2),
            },
            "btts": {
                "yes": round(random.uniform(1.75, 2.10), 2),
                "no": round(random.uniform(1.75, 2.20), 2)
            },
            "cards": {
                "over45": round(random.uniform(1.70, 2.30), 2),
                "under45": round(random.uniform(1.60, 2.10), 2),
            },
            "corners": {
                "over95": round(random.uniform(1.65, 2.20), 2),
                "under95": round(random.uniform(1.65, 2.20), 2),
            },
            "player_props": {
                "home_shots": round(random.uniform(2.50, 5.50), 2),
                "away_shots": round(random.uniform(2.50, 5.50), 2)
            }
        }
