# backend/scraper/odds_aggregator.py

import requests
import numpy as np
from bs4 import BeautifulSoup
from backend.utils.logger import get_logger


class OddsAggregator:
    """
    ODDS AGGREGATOR (multi-bookmaker scraping)
    -----------------------------------------
    Források:
        ✓ bet365
        ✓ bwin
        ✓ unibet
        ✓ pinnacle
        ✓ williamhill
        ✓ 1xbet
        ✓ marathonbet
        ✓ betfair (exchange price)
        ✓ oddsportal fallback (HTML)

    API nincs → HTML scraping + normalizálás.

    Visszaad:
        {
            match_id: {
                "1": avg,
                "X": avg,
                "2": avg,
                "sources": {
                    "bet365": {...},
                    "bwin": {...},
                    ...
                }
            }
        }
    """

    def __init__(self):
        self.logger = get_logger()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        })

    # ---------------------------------------------------------
    # PUBLIC INTERFACE
    # ---------------------------------------------------------
    def get_aggregated_odds(self, home, away):
        """
        Lekéri több bukitól az oddsot és aggregált értéket ad.
        """

        sources = {}

        # 1) több bukméker próbálása
        for name, func in [
            ("bet365", self._scrape_bet365),
            ("bwin", self._scrape_bwin),
            ("unibet", self._scrape_unibet),
            ("pinnacle", self._scrape_pinnacle),
            ("whill", self._scrape_whill),
            ("1xbet", self._scrape_1xbet),
            ("marathonbet", self._scrape_marathon),
            ("betfair", self._scrape_betfair_exchange),
            ("oddsportal", self._scrape_oddsportal)
        ]:
            try:
                data = func(home, away)
                if data:
                    sources[name] = data
            except:
                pass

        if not sources:
            self.logger.error("OddsAggregator: NO DATA FOUND!")
            return {}

        # 2) aggregálás
        return self._aggregate(sources)

    # ---------------------------------------------------------
    # AGGREGÁLÁS
    # ---------------------------------------------------------
    def _aggregate(self, sources):
        """
        Átlag + margin normalizálás.
        """

        def collect(key):
            arr = []
            for s in sources.values():
                if key in s:
                    arr.append(s[key])
            return arr

        o1 = collect("1")
        ox = collect("X")
        o2 = collect("2")

        # ha hiányzik bármelyik: fallback
        if not o1 or not o2:
            return {}

        # odds átlag
        avg1 = float(np.mean(o1))
        avgx = float(np.mean(ox)) if ox else None
        avg2 = float(np.mean(o2))

        # margin-normalizálás (fair odds)
        fair = self._remove_margin(avg1, avgx, avg2)

        return {
            "1": fair["1"],
            "X": fair["X"],
            "2": fair["2"],
            "sources": sources
        }

    # ---------------------------------------------------------
    # MARGIN REMOVAL (fair odds)
    # ---------------------------------------------------------
    def _remove_margin(self, o1, ox, o2):
        """
        Odds → probability → normalizálás → vissza odds.
        """

        p1 = 1 / o1
        px = 1 / ox if ox else 0
        p2 = 1 / o2

        s = p1 + px + p2

        p1 /= s
        px /= s if ox else 0
        p2 /= s

        fair = {
            "1": round(1 / p1, 4),
            "X": round(1 / px, 4) if ox else None,
            "2": round(1 / p2, 4)
        }
        return fair

    # ---------------------------------------------------------
    # BUKMÉKER SCRAPEREK
    # ---------------------------------------------------------
    # MIND STUB/PLACEHOLDER – később konkrét HTML struktúra alapján befejezhető

    def _scrape_bet365(self, home, away):
        return None

    def _scrape_bwin(self, home, away):
        return None

    def _scrape_unibet(self, home, away):
        return None

    def _scrape_pinnacle(self, home, away):
        return None

    def _scrape_whill(self, home, away):
        return None

    def _scrape_1xbet(self, home, away):
        return None

    def _scrape_marathon(self, home, away):
        return None

    def _scrape_betfair_exchange(self, home, away):
        return None

    # Fallback: OddsPortal HTML
    def _scrape_oddsportal(self, home, away):
        try:
            query = f"{home}-{away}".lower().replace(" ", "-")
            url = f"https://www.oddsportal.com/search/results/{query}/"

            r = self.session.get(url, timeout=5)
            if r.status_code != 200:
                return None

            soup = BeautifulSoup(r.text, "html.parser")

            odds = soup.text.lower()
            # egyszerű fallback parser
            m1 = re.findall(r"1\s+([0-9]+\.[0-9]+)", odds)
            mx = re.findall(r"x\s+([0-9]+\.[0-9]+)", odds)
            m2 = re.findall(r"2\s+([0-9]+\.[0-9]+)", odds)

            if not m1 or not m2:
                return None

            return {
                "1": float(m1[0]),
                "X": float(mx[0]) if mx else None,
                "2": float(m2[0])
            }

        except:
            return None
