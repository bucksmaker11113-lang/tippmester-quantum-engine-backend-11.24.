# backend/core/master_data_loader.py

import datetime
from backend.utils.logger import get_logger


class MasterDataLoader:
    """
    MASTER DATA LOADER – PRO VERSION
    ---------------------------------
    Feladata:
        • TippmixPro odds betöltése
        • Nemzetközi odds betöltése
        • FlashScore és SofaScore adat összehangolása
        • Match-azonosítás (team normalization + date check)
        • FusionEngine input adatmodell előkészítése
        • Missing adatok kezelése fallback-ekkel
    """

    def __init__(self, config, tmx_scraper, intl_scraper, flash_scraper, sofa_scraper):
        self.config = config
        self.logger = get_logger()

        self.tmx = tmx_scraper
        self.intl = intl_scraper
        self.flash = flash_scraper
        self.sofa = sofa_scraper

    # ============================================================
    #  Team normalization
    # ============================================================
    def _normalize_team(self, name: str):
        name = name.lower()
        replace = {
            "fc": "",
            "sc": "",
            "cf": "",
            " " : "",
            "." : "",
            "-" : "",
        }
        for k,v in replace.items():
            name = name.replace(k,v)
        return name

    # ============================================================
    #  MATCH FINDER (Intl → TippmixPro)
    # ============================================================
    def _find_tmx_match(self, match):
        """Bet365/Pinnacle match → TippmixPro equivalent"""

        home = self._normalize_team(match["home"])
        away = self._normalize_team(match["away"])

        tmx_matches = self.tmx.get_today_matches()

        for m in tmx_matches:
            h = self._normalize_team(m["home"])
            a = self._normalize_team(m["away"])

            if h == home and a == away:
                return m

        return None

    # ============================================================
    #  Load all data for ONE match
    # ============================================================
    def load_match_data(self, intl_match):
        """
        intl_match:
            {
                "match_id": "...",
                "home": "...",
                "away": "...",
                "league": "...",
                "date": "...",
            }
        """

        match_id = intl_match["match_id"]

        # ---------------------------
        # TippmixPro matching
        # ---------------------------
        tmx_match = self._find_tmx_match(intl_match)

        # ---------------------------
        # Odds loading
        # ---------------------------
        intl_odds = self.intl.get_odds(match_id)

        if tmx_match:
            tmx_odds = self.tmx.get_odds(tmx_match["tmx_id"])
        else:
            tmx_odds = {"1": None, "X": None, "2": None}

        # ---------------------------
        # Scraper-based live stats
        # ---------------------------
        try:
            flash_stats = self.flash.get_stats(match_id)
        except:
            flash_stats = {}

        try:
            sofa_stats = self.sofa.get_stats(match_id)
        except:
            sofa_stats = {}

        # ---------------------------
        # FINAL INPUT STRUCTURE FOR FUSION ENGINE
        # ---------------------------
        return {
            "match_id": match_id,
            "home": intl_match["home"],
            "away": intl_match["away"],
            "league": intl_match.get("league"),
            "date": intl_match.get("date"),

            "international_odds": intl_odds,
            "tippmixpro_odds": tmx_odds,

            "flashscore": flash_stats,
            "sofascore": sofa_stats,

            "tmx_available": tmx_match is not None,
            "tmx_id": tmx_match["tmx_id"] if tmx_match else None
        }
