# backend/system/system_flow.py

from backend.scraper.result_scraper import ResultScraper
from backend.scraper.tippmixpro_scraper import TippmixProScraper
from backend.pipeline.ensemble_pipeline import EnsemblePipeline
from backend.pipeline.tip_pipeline import TipPipeline
from backend.core.training_pipeline import TrainingPipeline
from backend.core.daily_training_workflow import DailyTrainingWorkflow
from backend.utils.logger import get_logger

class SystemFlow:
    """
    A rendszer teljes napi menete, end-to-end.
    Ez hívja az összes modult:
        - adat letöltés
        - odds aggregáció
        - ensemble AI
        - value AI (deep)
        - tipp generálás
        - training data mentés
        - daily retrain
    """

    def __init__(self, config):
        self.logger = get_logger()
        self.config = config

        self.scraper = ResultScraper()
        self.tmp = TippmixProScraper()
        self.ensemble = EnsemblePipeline(config)
        self.tip = TipPipeline(config)
        self.train_pipe = TrainingPipeline()
        self.daily = DailyTrainingWorkflow(config)

    # --------------------------------------------------------------------
    # 1) napi odds + mérkőzés adat letöltés — (STUB, később készítjük)
    # --------------------------------------------------------------------
    def fetch_daily_matches(self):
        """
        Visszaad:
            {
                match_id: {
                    "home": "...",
                    "away": "...",
                    "date": "...",
                    "odds": {...}
                },
                ...
            }
        """
        self.logger.warning("SystemFlow: fetch_daily_matches() STUB - később implementáljuk.")
        return {}

    # --------------------------------------------------------------------
    # 2) AI futtatása a napi meccslistára
    # --------------------------------------------------------------------
    def run_daily_prediction(self):
        matches = self.fetch_daily_matches()
        if not matches:
            self.logger.warning("Nincs napi mérkőzés adat. STOP.")
            return {}

        # Engine outputok (később betöltve)
        model_outputs = self._get_engine_outputs(matches)

        # Ensemble pipeline
        final_pred = self.ensemble.run(model_outputs, self._extract_odds(matches))

        # Tipp generálás
        tips = {
            "single": self.tip.single(final_pred),
            "kombi": self.tip.kombi(final_pred)
        }

        return {
            "predictions": final_pred,
            "tips": tips
        }

    # --------------------------------------------------------------------
    # 3) engine output STUB – később implementáljuk
    # --------------------------------------------------------------------
    def _get_engine_outputs(self, matches):
        return {
            "mc3": {},
            "lstm": {},
            "gnn": {},
            "poisson": {},
            "rl": {},
            "gameflow": {},
            "injury": {},
            "weather": {},
            "market": {},
            "anomaly": {},
            "scorepredict": {},
            "temporary": {},
            "odds_engine": {},
            "arbitrage": {}
        }

    # --------------------------------------------------------------------
    # 4) Odds kinyerése
    # --------------------------------------------------------------------
    def _extract_odds(self, matches):
        odds_map = {}
        for m_id, data in matches.items():
            odds_map[m_id] = data.get("odds", {})
        return odds_map

    # --------------------------------------------------------------------
    # 5) Napi tippmix ellenőrzés
    # --------------------------------------------------------------------
    def filter_for_tippmix(self, tips):
        filtered = []
        for m_id, p in tips:
            ok = self.tmp.exists_on_tippmix(
                p.get("home"), p.get("away"), p.get("date")
            )
            if ok:
                filtered.append((m_id, p))
        return filtered

    # --------------------------------------------------------------------
    # 6) Training data előkészítése – STUB
    # --------------------------------------------------------------------
    def prepare_training_data(self, predictions):
        self.logger.warning("prepare_training_data() később implementáljuk.")

    # --------------------------------------------------------------------
    # 7) Napi retrain indítása
    # --------------------------------------------------------------------
    def run_daily_retrain(self):
        self.daily.run_daily_training()
