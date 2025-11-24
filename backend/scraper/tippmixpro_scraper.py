# backend/scraper/tippmixpro_scraper.py

import re
import requests
from bs4 import BeautifulSoup
from backend.utils.logger import get_logger


class TippmixProScraper:
    """
    ÉLES TippmixPro Scraper
    ------------------------
    Funkciói:
        ✓ meccskeresés (home + away alapján)
        ✓ esemény link kinyerése
        ✓ odds kiolvasása
        ✓ fogadhatóság ellenőrzése
        ✓ piacok beolvasása
    """

    BASE_URL = "https://www.tippmixpro.hu"

    def __init__(self):
        self.logger = get_logger()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        })

    # ---------------------------------------------------------------
    # 1) Meccskeresés (home_team, away_team)
    # ---------------------------------------------------------------
    def search_match(self, home_team, away_team):
        """
        TippmixPro search oldal HTML szűréssel.
        Visszaadja az esemény linkjét, ha megtalálja.
        """

        q = f"{home_team} {away_team}"
        url = f"{self.BASE_URL}/fogadasi-ajanlat?searchText={q}"

        self.logger.info(f"[TippmixPro] Keresés: {q}")

        try:
            r = self.session.get(url, timeout=5)
            if r.status_code != 200:
                return None

            soup = BeautifulSoup(r.text, "html.parser")

            # eseménykártyák keresése (vannak rejtett div-ek)
            cards = soup.find_all("div", class_="match-item")

            for c in cards:
                text = c.get_text(" ", strip=True).lower()

                if (home_team.lower() in text) and (away_team.lower() in text):
                    # esemény link kinyerése
                    link = c.find("a", href=True)
                    if link:
                        event_url = self.BASE_URL + link["href"]
                        return event_url

            return None

        except Exception as e:
            self.logger.error(f"[TippmixPro] search_match ERROR: {e}")
            return None

    # ---------------------------------------------------------------
    # 2) Esemény oddsok kinyerése
    # ---------------------------------------------------------------
    def get_odds(self, event_url):
        """
        Esemény oldalról kinyeri az 1X2 és egyéb oddsokat.
        """
        try:
            r = self.session.get(event_url, timeout=5)
            if r.status_code != 200:
                return {}

            soup = BeautifulSoup(r.text, "html.parser")

            odds_map = {}

            # klasszikus 1X2 piac keresése
            market_blocks = soup.find_all("div", class_="market")
            for m in market_blocks:
                title = m.find("div", class_="market-title")
                if not title:
                    continue

                title_text = title.get_text(strip=True).lower()

                if "1x2" in title_text or "végeredmény" in title_text:
                    buttons = m.find_all("button")
                    for b in buttons:
                        label = b.find("span", class_="label")
                        value = b.find("span", class_="value")
                        if label and value:
                            odds_map[label.get_text(strip=True)] = float(value.get_text(strip=True))

            return odds_map

        except Exception as e:
            self.logger.error(f"[TippmixPro] get_odds ERROR: {e}")
            return {}

    # ---------------------------------------------------------------
    # 3) Fogadhatóság ellenőrzése
    # ---------------------------------------------------------------
    def is_available(self, event_url):
        """
        Ellenőrzi, hogy az esemény fogadható-e.
        """
        try:
            r = self.session.get(event_url, timeout=5)
            if r.status_code != 200:
                return False

            soup = BeautifulSoup(r.text, "html.parser")

            if soup.find(text=re.compile("Nincs fogadási lehetőség", re.IGNORECASE)):
                return False

            # ha vannak odds gombok
            if soup.find("button", {"class": "odd-button"}):
                return True

            return False

        except:
            return False

    # ---------------------------------------------------------------
    # 4) FŐ METÓDUS – meccs teljes ellenőrzése
    # ---------------------------------------------------------------
    def check_match(self, home_team, away_team):
        """
        Komplett ellenőrzés:
            ✓ meccs keresése
            ✓ odds beolvasása
            ✓ fogadhatóság vizsgálata
        """
        event_url = self.search_match(home_team, away_team)
        if not event_url:
            return {
                "exists": False,
                "odds": {},
                "available": False
            }

        odds = self.get_odds(event_url)
        available = self.is_available(event_url)

        return {
            "exists": True,
            "event_url": event_url,
            "odds": odds,
            "available": available
        }
