# backend/engine/ai_coach_explainer.py

from backend.utils.logger import get_logger


class AICoachExplainer:
    """
    AI COACH EXPLAINER – PRO VERSION
    --------------------------------
    Feladata:
        • Emberi, magyar nyelvű tippmagyarázat generálása
        • Value, EV, probability értelmezése
        • Sharp money & piaci mozgások kezelése
        • CLV (closing line value) elemzés
        • Trend / anomaly / weather / momentum integráció
        • Prop market (corners, cards, shots, etc.) magyarázat
        • Kombi tippekhez összevont logika
        • Live szituációk magyarázata
        • Stake & risk interpretáció
    """

    def __init__(self, config=None):
        self.config = config or {}
        self.logger = get_logger()

    # ==========================================================================
    # SEGÉD FÜGGVÉNYEK – SZÖVEG GENERÁLÁSA
    # ==========================================================================

    def _value_block(self, p, ev, vscore, odds):
        msg = (
            f"A modell a választott kimenetel valószínűségét {p*100:.1f}%-ra értékeli, "
            f"ami magasabb, mint amit az odds sugall. A value-score {vscore:.2f}, "
            "ami pozitív várható értékre utal. "
            f"A TippmixPro által kínált {odds:.2f}-es odds miatt statisztikailag "
            "kedvező szituáció áll fenn."
        )
        return msg

    def _sharp_block(self, sharp):
        if sharp is True:
            return (
                "A piac irányából sharp money jelenik meg, ami azt jelzi, hogy "
                "professzionális fogadók is ugyanabba az irányba mozognak."
            )
        elif sharp is False:
            return "A piaci aktivitás normál, sharp money nem mutatható ki."
        return ""

    def _clv_block(self, clv):
        if clv is None:
            return ""
        if clv > 0.02:
            return (
                f"A closing line value (CLV) +{clv:.2f}, "
                "ami azt mutatja, hogy a piac később a mi irányunkba mozdult."
            )
        elif clv < -0.02:
            return (
                f"A closing line value {clv:.2f}, "
                "tehát a záró odds romlott, ez némi óvatosságot indokol."
            )
        return "A CLV semleges, nincs jelentős elmozdulás az oddsokban."

    def _trend_block(self, trend_score):
        if trend_score is None:
            return ""
        if trend_score > 0.6:
            return "A formamutatók és hosszútávú trendek erősen támogatják a választást."
        if trend_score > 0.45:
            return "A formatrendek összességében kedvezőek."
        return "A trendszámok alapján közepesen stabil a választás."

    def _anomaly_block(self, anomaly):
        if anomaly is None or anomaly == 0:
            return ""
        return (
            "Az adatelemzés enyhe anomáliát mutat a piaci viselkedésben, "
            "ami potenciális rejtett értéket jelezhet."
        )

    def _weather_block(self, weather):
        if not weather:
            return ""
        try:
            if weather.get("severity", 0) > 0.6:
                return "Az időjárási körülmények extrémek, ez befolyásolhatja a meccs tempóját."
            if weather.get("severity", 0) > 0.3:
                return "A mérsékelt időjárási tényezők kisebb mértékben hatnak a játékra."
        except:
            pass
        return ""

    def _prop_market_block(self, category):
        if not category:
            return ""

        if "corners" in category:
            return "A sarokszög piacot leginkább a támadási intenzitás és tempó befolyásolja."
        if "cards" in category:
            return "A lapok várható száma a csapatok agresszivitásától és a bírói stílustól függ."
        if "shots" in category or "goal" in category:
            return "A lövésszám és gólpiac erősen korrelál az xG és támadóaktivitással."
        if "possession" in category:
            return "A labdabirtoklás piaca elsősorban taktikai mintákból becsülhető."

        return "A specális (prop) piacnál a statisztikai mintázatok és matchup tényezők dominálnak."

    def _risk_block(self, risk):
        if risk < 0.35:
            return "A tipp kockázati besorolása alacsony, stabil választás."
        if risk < 0.55:
            return "A tipp mérsékelt kockázatú."
        return "A tipp a szokásosnál magasabb kockázatot hordoz."

    def _live_block(self, live_data):
        if not live_data:
            return ""
        if live_data.get("momentum") > 1.2:
            return "Az élő adatok alapján a momentum erősen támogatja a választott oldalt."
        if live_data.get("danger_zone") is True:
            return "A meccsen veszélyzóna áll fenn (nagy nyomás, helyzetek), ami befolyásolhatja a kimenetet."
        return "Az élő adatok nem mutatnak extrém kilengést."

    # ==========================================================================
    # FŐ MAGYARÁZAT GENERÁLÓ
    # ==========================================================================

    def explain(self, data: dict):
        """
        data = {
            "probability": 0.61,
            "ev": 0.13,
            "value_score": 0.72,
            "odds": 1.72,
            "market_category": "corners",
            "sharp": True/False,
            "clv": 0.04,
            "trend": 0.58,
            "risk": 0.41,
            "anomaly": 1,
            "weather": { "severity": 0.5 },
            "live": { "momentum": 1.4, "danger_zone": False },
            "tip_type": "single" | "kombi" | "prop" | "live"
        }
        """

        p = data.get("probability", 0.5)
        ev = data.get("ev", 0)
        v = data.get("value_score", 0)
        o = data.get("odds", 1.0)

        parts = []

        # alap
        parts.append(self._value_block(p, ev, v, o))

        # sharp money
        parts.append(self._sharp_block(data.get("sharp")))

        # CLV
        parts.append(self._clv_block(data.get("clv")))

        # sport modellek (trend, anomaly, weather)
        parts.append(self._trend_block(data.get("trend")))
        parts.append(self._anomaly_block(data.get("anomaly")))
        parts.append(self._weather_block(data.get("weather")))

        # live jelzések
        if data.get("tip_type") == "live":
            parts.append(self._live_block(data.get("live")))

        # prop piac
        if data.get("tip_type") == "prop":
            parts.append(self._prop_market_block(data.get("market_category")))

        # risk
        parts.append(self._risk_block(data.get("risk", 0.5)))

        # végső összegzés
        parts.append(
            "Összességében a statisztikai modellek, a piaci mozgások és a value értékek "
            "együttesen támogatják a tippet."
        )

        # tiszta stringként vissza
        return " ".join([p for p in parts if p])
