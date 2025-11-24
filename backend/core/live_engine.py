# backend/core/live_engine.py

import numpy as np
import time
from backend.utils.logger import get_logger

class LiveEngine:
    """
    QUANTUM LIVE ENGINE – PRO EDITION
    ---------------------------------
    Integrált valós idejű élő motor:
        • Odds Drift Engine
        • FlashScore Momentum Engine
        • SofaScore xG / pressure / attack engine
        • Danger-Zone detection (VAR, piros lap, nagy momentum kitörés)
        • Live Value Engine
        • AI Decision Layer

    A rendszer SCRAPER MÓDBAN működik – nincs API!
    """

    def __init__(self, config, flash_scraper, sofa_scraper):
        self.config = config
        self.flash = flash_scraper      # FlashScore scraper objektum
        self.sofa = sofa_scraper        # SofaScore scraper objektum
        self.logger = get_logger()

        # odds drift határok
        self.max_drift = config.get("live", {}).get("max_drift_percent", 0.25)
        self.min_drift = config.get("live", {}).get("min_drift_percent", 0.05)

        # momentum spike threshold
        self.momentum_spike = config.get("live", {}).get("momentum_spike", 1.5)

        # xG spike threshold
        self.xg_spike = config.get("live", {}).get("xg_spike", 0.20)

        # danger-zone rules
        self.danger_attack_threshold = config.get("live", {}).get("danger_attacks", 65)

    # -------------------------------------------------------------------------
    # FŐ FUNKCIÓ: Élő tipp generálás egy meccsre
    # -------------------------------------------------------------------------
    def analyze_live_match(self, match_id):
        """
        Return:
            {
                "match_id": ...,
                "live_tip": True/False,
                "reason": "...",
                "live_probability": ...,
                "live_value": ...,
                "confidence": ...,
                "meta": {...}
            }
        """

        self.logger.info(f"[LiveEngine] Élő elemzés indul: {match_id}")

        # 1) Odds drift detektálása
        drift_data = self._odds_drift(match_id)

        # 2) FlashScore momentum lekérés
        flash_data = self.flash.get_live_stats(match_id)
        momentum_score = self._momentum_engine(flash_data)

        # 3) SofaScore xG és pressure lekérés
        sofa_data = self.sofa.get_live_stats(match_id)
        xg_momentum = self._xg_engine(sofa_data)

        # 4) Danger-Zone detektálás
        danger_zone = self._danger_zone(flash_data, sofa_data)

        # 5) Live probability becslés (AI-súlyozott)
        live_prob = self._estimate_live_prob(
            drift_data,
            momentum_score,
            xg_momentum,
            danger_zone
        )

        # 6) Live odds lekérése
        live_odds = drift_data.get("current_odds", 2.0)

        # 7) Live value számítás
        live_value = live_prob * live_odds - (1 - live_prob)

        # 8) AI decision layer
        decision, reason, confidence = self._ai_decision(
            live_prob, live_value, momentum_score, xg_momentum, danger_zone
        )

        return {
            "match_id": match_id,
            "live_tip": decision,
            "reason": reason,
            "live_probability": round(live_prob, 4),
            "live_value": round(live_value, 4),
            "confidence": round(confidence, 3),
            "meta": {
                "drift": drift_data,
                "momentum": momentum_score,
                "xg_momentum": xg_momentum,
                "danger_zone": danger_zone,
                "live_odds": live_odds
            }
        }

    # -------------------------------------------------------------------------
    # ODDS DRIFT ENGINE
    # -------------------------------------------------------------------------
    def _odds_drift(self, match_id):
        """
        Odds drift: a legfontosabb élő tipp indikátor.

        Visszatérés:
            {
                "previous_odds": ...,
                "current_odds": ...,
                "drift_percent": ...
            }
        """

        try:
            prev, current = self.flash.get_live_odds(match_id)
        except:
            prev, current = 2.0, 2.0

        if prev == 0:
            prev = 1.0

        drift = (prev - current) / prev

        return {
            "previous_odds": prev,
            "current_odds": current,
            "drift_percent": round(drift, 4)
        }

    # -------------------------------------------------------------------------
    # FLASHScore MOMENTUM ENGINE
    # -------------------------------------------------------------------------
    def _momentum_engine(self, flash_data):
        """
        FlashScore élő momentum grafikon adatai:
            • dangerous attacks
            • total attacks
            • shot map
            • attack ratio
        """

        if not flash_data:
            return 0.0

        try:
            da = flash_data["dangerous_attacks"]
            att = flash_data["attacks"]
            shots = flash_data["shots_on_goal"]

            momentum = (da * 0.6 + att * 0.3 + shots * 0.1) / 100

        except:
            momentum = 0.0

        return float(max(0.0, min(3.0, momentum)))

    # -------------------------------------------------------------------------
    # SOFAScore xG ENGINE
    # -------------------------------------------------------------------------
    def _xg_engine(self, sofa_data):
        """
        xG momentum:
            xG_per_min változás
            shot quality
            pressure index
        """

        if not sofa_data:
            return 0.0

        try:
            xg_now = sofa_data["xg_now"]
            xg_prev = sofa_data["xg_prev"]

            xg_delta = xg_now - xg_prev

            pressure = sofa_data.get("pressure_index", 0)
            shot_quality = sofa_data.get("shot_quality", 0)

            xg_score = xg_delta * 2 + pressure * 0.3 + shot_quality * 0.2

            return float(max(0.0, min(3.0, xg_score)))

        except:
            return 0.0

    # -------------------------------------------------------------------------
    # DANGER-ZONE ENGINE (VAR, PIROS LAP, MASSIVE MOMENTUM)
    # -------------------------------------------------------------------------
    def _danger_zone(self, flash_data, sofa_data):
        danger = False

        try:
            if flash_data.get("red_cards", 0) > 0:
                danger = True

            if sofa_data.get("var_check", False):
                danger = True

            if flash_data.get("dangerous_attacks", 0) > self.danger_attack_threshold:
                danger = True

        except:
            pass

        return danger

    # -------------------------------------------------------------------------
    # LIVE PROBABILITY BECSLÉSE
    # -------------------------------------------------------------------------
    def _estimate_live_prob(self, drift_data, momentum, xg, danger):
        drift = drift_data.get("drift_percent", 0.0)

        base = 0.50 + drift * 0.8
        base += momentum * 0.15
        base += xg * 0.10

        if danger:
            base -= 0.12  # óvatosabb becslés veszélyben

        return float(max(0.05, min(0.95, base)))

    # -------------------------------------------------------------------------
    # AI DECISION LAYER
    # -------------------------------------------------------------------------
    def _ai_decision(self, live_prob, live_value, momentum, xg, danger):
        """
        Eldönti, hogy adunk-e élő tippet.
        """

        confidence = (
            live_prob * 0.4 +
            max(0, live_value) * 0.3 +
            momentum * 0.2 +
            xg * 0.1
        )

        # veszély esetén csökkentjük
        if danger:
            confidence *= 0.7

        # döntési logika:
        if confidence > 0.65 and live_value > 0.05:
            return True, "Erős live jelzés (value + momentum + drift)", confidence

        if live_value < 0:
            return False, "Nincs value élőben", confidence

        if momentum < 0.5:
            return False, "Gyenge momentum", confidence

        return False, "Nem elég erős jel", confidence
