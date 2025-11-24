# backend/engine/game_state_projection_engine.py

import numpy as np
from backend.utils.logger import get_logger

class GameStateProjectionEngine:
    """
    GAME STATE PROJECTION ENGINE – HYBRID LIVE AI EDITION
    -----------------------------------------------------
    Feladata:
        • Következő 5 perc eseményeinek előrejelzése
        • Live gólvalószínűség (next 5 min)
        • Momentum váltás előrejelzés
        • Pressing intensity változás előrejelzés
        • Dangerous attack detection
        • Live odds rövidtávú mozgás előrejelzés
        
        HYBRID MODE:
            - LIGHT: ha csak alapadat érhető el
            - PRO: ha van live event feed, xThreat, momentum graph

        Output:
            "probability" = következő 5 percben a jobb csapat javára történik pozitív esemény
    """

    def __init__(self, config):
        self.config = config
        self.logger = get_logger()

        # scaling
        self.xg_scaling = config.get("game_state", {}).get("xg_scaling", 0.22)
        self.momentum_scaling = config.get("game_state", {}).get("momentum_scaling", 0.28)
        self.attack_scaling = config.get("game_state", {}).get("attack_scaling", 0.25)

        self.pro_scaling = config.get("game_state", {}).get("pro_scaling", 0.40)
        self.live_event_scaling = config.get("game_state", {}).get("live_event_scaling", 0.35)

        # fallback
        self.fallback_prob = 0.55
        self.min_conf = config.get("game_state", {}).get("min_confidence", 0.60)

    # ----------------------------------------------------------------------
    # MAIN PREDICTOR
    # ----------------------------------------------------------------------
    def predict(self, match_data):
        outputs = {}

        for match_id, data in match_data.items():
            try:
                if self._has_pro_data(data):
                    prob = self._pro_mode(data)
                    mode = "PRO"
                else:
                    prob = self._light_mode(data)
                    mode = "LIGHT"
            except Exception as e:
                self.logger.error(f"[GameState] ERROR → fallback: {e}")
                prob = self.fallback_prob
                mode = "FALLBACK"

            prob = float(max(0.01, min(0.99, prob)))

            conf = self._confidence(prob, data)
            risk = self._risk(prob, conf)

            outputs[match_id] = {
                "probability": round(prob, 4),  # next 5 minutes advantage probability
                "confidence": round(conf, 3),
                "risk": round(risk, 3),
                "meta": {"mode": mode},
                "source": "GameStateProjection"
            }

        return outputs

    # ----------------------------------------------------------------------
    # CHECK IF PRO MODE CAN BE USED
    # ----------------------------------------------------------------------
    def _has_pro_data(self, data):
        required = [
            "xThreat", "momentum_graph", "dangerous_attacks",
            "pressing_intensity", "live_events"
        ]
        return all(k in data for k in required)

    # ----------------------------------------------------------------------
    # LIGHT MODE — simple, fast, cheap
    # ----------------------------------------------------------------------
    def _light_mode(self, data):
        xg = data.get("xg_last10", 0.1)              # last 10 mins xG
        momentum = data.get("momentum", 0.5)         # 0–1
        attacks = data.get("dangerous_attacks", 2)   # numeric count last 10 min

        prob_shift = (
            xg * self.xg_scaling +
            (momentum - 0.5) * self.momentum_scaling +
            attacks * 0.03
        )

        prob = 0.5 + prob_shift
        return prob

    # ----------------------------------------------------------------------
    # PRO MODE — deep live match engine
    # ----------------------------------------------------------------------
    def _pro_mode(self, data):
        xThreat = data.get("xThreat", 0.02)  # expected threat metric
        momentum_graph = data.get("momentum_graph", [0.5])
        dangerous_attacks = data.get("dangerous_attacks", 2)
        pressing = data.get("pressing_intensity", 0.5)
        live_events = data.get("live_events", [])

        # MOMENTUM TREND
        momentum_trend = np.mean(momentum_graph[-5:]) if len(momentum_graph) >= 5 else np.mean(momentum_graph)

        # LIVE EVENTS → shots, corners, big chances raise the probability
        event_score = self._live_event_score(live_events)

        prob_shift = (
            xThreat * self.pro_scaling +
            (momentum_trend - 0.5) * self.momentum_scaling +
            dangerous_attacks * 0.04 +
            (pressing - 0.5) * 0.10 +
            event_score * self.live_event_scaling
        )

        prob = 0.5 + prob_shift
        return prob

    # ----------------------------------------------------------------------
    # LIVE EVENT ANALYZER
    # ----------------------------------------------------------------------
    def _live_event_score(self, events):
        score = 0
        for ev in events:
            if ev == "SHOT":
                score += 0.05
            elif ev == "BIG_CHANCE":
                score += 0.12
            elif ev == "CORNER":
                score += 0.03
            elif ev == "FREEKICK":
                score += 0.02
            elif ev == "TURNOVER_HIGH":
                score += 0.07
            elif ev == "PRESSING_TRIGGER":
                score += 0.04
        return score

    # ----------------------------------------------------------------------
    # CONFIDENCE
    # ----------------------------------------------------------------------
    def _confidence(self, prob, data):
        live_quality = data.get("live_data_quality", 0.80)
        stability = 1 - abs(prob - 0.5)

        conf = live_quality * 0.6 + stability * 0.4
        return float(max(self.min_conf, min(1.0, conf)))

    # ----------------------------------------------------------------------
    # RISK
    # ----------------------------------------------------------------------
    def _risk(self, prob, conf):
        return float(min(1.0, max(0.0,
            (1 - conf) * 0.6 + (1 - prob) * 0.4
        )))
