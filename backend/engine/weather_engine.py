# backend/engine/weather_engine.py

import numpy as np
from backend.utils.logger import get_logger


class WeatherEngine:
    """
    WEATHER ENGINE – PRO EDITION
    -----------------------------
    Feladata:
        • Időjárási tényezők statisztikai modellezése
        • Hatás a meccs tempójára, gólvárható értékre, varianciára
        • Hőmérséklet, szél, csapadék, páratartalom
        • Pitch quality (pálya minősége)
        • Liga weather-sensitivity különbségek
        • Output → weather_score (0–1), probability_modifier, risk, confidence
    """

    def __init__(self, config=None):
        self.config = config or {}
        self.logger = get_logger()

        c = self.config.get("weather", {})

        # Súlyok
        self.temp_weight = c.get("temp_weight", 0.25)
        self.wind_weight = c.get("wind_weight", 0.25)
        self.rain_weight = c.get("rain_weight", 0.20)
        self.humidity_weight = c.get("humidity_weight", 0.15)
        self.pitch_weight = c.get("pitch_weight", 0.15)

        self.min_conf = 0.55

    # ----------------------------------------------------------------------
    # TEMPERATURE IMPACT
    # ----------------------------------------------------------------------
    def _temperature_impact(self, temp):
        """
        Temp optimum: 9–17°C. Ezen kívül fatigue nő → pace csökken.
        """
        if temp is None:
            return 0.5

        if 9 <= temp <= 17:
            return 0.65

        if temp < 0:
            return 0.35  # hideg → pace csökken

        if temp > 28:
            return 0.30  # nagy meleg → stamina drop

        # közepes eltérés
        return 0.5 - abs(temp - 13) * 0.02

    # ----------------------------------------------------------------------
    # WIND IMPACT
    # ----------------------------------------------------------------------
    def _wind_impact(self, wind):
        """
        Szél hatása:
        0–8 km/h → normál
        8–20 km/h → kisebb negatív
        20+ km/h → szignifikáns negatív (rossz pass accuracy)
        """
        if wind is None:
            return 0.5

        if wind < 8:
            return 0.6

        if wind < 20:
            return 0.45

        return 0.25

    # ----------------------------------------------------------------------
    # PRECIPITATION IMPACT (RAIN / SNOW)
    # ----------------------------------------------------------------------
    def _rain_impact(self, rain_intensity):
        """
        rain_intensity: 0–1 skála
        """
        if rain_intensity is None:
            return 0.5

        if rain_intensity == 0:
            return 0.6

        if rain_intensity < 0.3:
            return 0.45

        if rain_intensity < 0.7:
            return 0.35

        return 0.20  # heavy rain/snow

    # ----------------------------------------------------------------------
    # HUMIDITY IMPACT
    # ----------------------------------------------------------------------
    def _humidity_impact(self, humidity):
        """
        30–60% ideális.
        """
        if humidity is None:
            return 0.5

        if 30 <= humidity <= 60:
            return 0.65

        return 0.5 - abs(humidity - 45) * 0.01

    # ----------------------------------------------------------------------
    # PITCH QUALITY IMPACT
    # ----------------------------------------------------------------------
    def _pitch_quality(self, pitch):
        """
        0–1 skála: 1 = top quality, 0 = very bad
        """
        if pitch is None:
            return 0.5

        if pitch > 0.8:
            return 0.65
        if pitch > 0.5:
            return 0.55
        return 0.35

    # ----------------------------------------------------------------------
    # FŐ ELEMZÉS
    # ----------------------------------------------------------------------
    def analyze(self, data):
        """
        data = {
            "temperature": 14,
            "wind_speed": 12,
            "rain_intensity": 0.2,
            "humidity": 55,
            "pitch_quality": 0.8,
            "weather_data_quality": 0.75
        }
        """

        temp_score = self._temperature_impact(data.get("temperature"))
        wind_score = self._wind_impact(data.get("wind_speed"))
        rain_score = self._rain_impact(data.get("rain_intensity"))
        humidity_score = self._humidity_impact(data.get("humidity"))
        pitch_score = self._pitch_quality(data.get("pitch_quality"))

        # weighted final weather score
        weather_score = (
            temp_score * self.temp_weight +
            wind_score * self.wind_weight +
            rain_score * self.rain_weight +
            humidity_score * self.humidity_weight +
            pitch_score * self.pitch_weight
        )

        weather_score = float(np.clip(weather_score, 0.05, 0.95))

        modifier = (weather_score - 0.5) * 0.12  # max ±12% hatás
        confidence = self._confidence(weather_score, data)
        risk = self._risk(weather_score, confidence)

        return {
            "weather_score": round(weather_score, 4),
            "probability_modifier": round(modifier, 4),
            "temp_score": round(temp_score, 3),
            "wind_score": round(wind_score, 3),
            "rain_score": round(rain_score, 3),
            "humidity_score": round(humidity_score, 3),
            "pitch_score": round(pitch_score, 3),
            "confidence": round(confidence, 3),
            "risk": round(risk, 3),
        }

    # ----------------------------------------------------------------------
    # CONFIDENCE
    # ----------------------------------------------------------------------
    def _confidence(self, score, data):
        weather_quality = data.get("weather_data_quality", 0.75)
        stability = 1 - abs(score - 0.5)

        conf = weather_quality * 0.6 + stability * 0.4
        return float(max(self.min_conf, min(1.0, conf)))

    # ----------------------------------------------------------------------
    # RISK
    # ----------------------------------------------------------------------
    def _risk(self, score, conf):
        return float(min(1.0, max(0.0, (1 - score) * 0.4 + (1 - conf) * 0.6)))
