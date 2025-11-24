# backend/engine/ocr_engine.py

import re
import cv2
import numpy as np
from backend.utils.logger import get_logger
import pytesseract
from difflib import get_close_matches


class OCREngine:
    """
    OCR ENGINE
    ----------
    Feladata:
        ✓ Csapatnevek kinyerése screenshotból
        ✓ Oddsok felismerése (1.85 / 2.40 / 3.10 stb.)
        ✓ Kép előfeldolgozás (thresh, blur, gray)
        ✓ Fuzzy matching (pl. Lverpool -> Liverpool)
        ✓ Output normalizálása
    """

    def __init__(self, config=None):
        self.config = config or {}
        self.logger = get_logger()

        # ismert csapatnevek betöltése
        self.team_list = self._load_team_list()

    # ---------------------------------------------------------
    # 1) Csapatlista betöltése
    # ---------------------------------------------------------
    def _load_team_list(self):
        try:
            # később CSV-ből vagy API-ból is jöhet
            return [
                "Liverpool", "Arsenal", "Chelsea", "Manchester City",
                "Manchester United", "Tottenham", "Barcelona", "Real Madrid",
                "Bayern", "PSG", "Juventus", "Inter", "Milan"
            ]
        except:
            return []

    # ---------------------------------------------------------
    # 2) Kép -> Szöveg (OCR)
    # ---------------------------------------------------------
    def extract_text(self, image_bytes):
        """
        image_bytes → raw file (PNG, JPG stb.)
        Vissza → nyers OCR szöveg
        """

        np_arr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        # előfeldolgozás - erősen növeli a minőséget
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.medianBlur(gray, 3)
        thresh = cv2.threshold(gray, 140, 255, cv2.THRESH_BINARY)[1]

        text = pytesseract.image_to_string(thresh, lang="eng")

        self.logger.info("OCR RAW TEXT:")
        self.logger.info(text)

        return text

    # ---------------------------------------------------------
    # 3) Csapatnév felismerés
    # ---------------------------------------------------------
    def extract_teams(self, text):
        """
        OCR-szövegből csapatokat keres fuzzy módon.
        """

        words = re.findall(r"[A-Za-z]+", text)

        found = []

        for w in words:
            matches = get_close_matches(w, self.team_list, n=1, cutoff=0.7)
            if matches:
                found.append(matches[0])

        found = list(dict.fromkeys(found))  # remove duplicates

        if len(found) >= 2:
            return found[:2]

        return found

    # ---------------------------------------------------------
    # 4) Odds felismerés (1.85 | 2.40 | 3.10 stb.)
    # ---------------------------------------------------------
    def extract_odds(self, text):
        """
        Bármely odds mintát felismerünk:
            1.85
            2,40
            3.10
        """

        raw = re.findall(r"\d+[.,]\d+", text)
        clean = [float(x.replace(",", ".")) for x in raw]

        # kiszűrjük a hülyeségeket (1.01 - 20.00)
        odds = [o for o in clean if 1.01 <= o <= 20]

        return odds[:10]

    # ---------------------------------------------------------
    # 5) FŐ FÜGGVÉNY (kép → csapat + odds)
    # ---------------------------------------------------------
    def analyze_image(self, image_bytes):
        text = self.extract_text(image_bytes)

        teams = self.extract_teams(text)
        odds = self.extract_odds(text)

        return {
            "teams": teams,
            "odds": odds,
            "raw_text": text
        }
