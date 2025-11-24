# backend/pipeline/master_pipeline.py

from backend.scraper.odds_aggregator import OddsAggregator
from backend.scraper.market_odds_aggregator import MarketOddsAggregator
from backend.scraper.tippmixpro_scraper import TippmixProScraper

from backend.pipeline.model_runner import ModelRunner

from backend.engine.quantum_synth_engine import QuantumSynthEngine
from backend.engine.fusion_engine import FusionEngine
from backend.engine.bayesian_updater import BayesianUpdater
from backend.engine.bias_engine import BiasEngine
from backend.engine.value_analyzer import ValueAnalyzer

from backend.engine.prop_engine import PropEngine
from backend.engine.prop_tip_selector import PropTipSelector

from backend.pipeline.odds_filter import OddsFilter
from backend.engine.kombi_optimizer import KombiOptimizer

from backend.engine.closing_line_predictor import ClosingLinePredictor
from backend.engine.sharp_money_tracker import SharpMoneyTracker

from backend.engine.rl_stake_engine import RLStakeEngine
from backend.engine.ai_coach_explainer import AICoachExplainer

from backend.reporting.daily_report_builder import DailyReportBuilder
from backend.analysis.historical_roi_analyzer import HistoricalROIAnalyzer

import datetime


class MasterPipeline:

    def __init__(self, config):
        self.config = config

        # Scrapers
        self.odds = OddsAggregator()
        self.markets = MarketOddsAggregator()
        self.tippmix = TippmixProScraper()

        # Models
        self.runner = ModelRunner(config)

        # Ensemble
        self.qse = QuantumSynthEngine(config)
        self.fusion = FusionEngine(config)
        self.bayes = BayesianUpdater(config)
        self.bias = BiasEngine(config)
        self.value = ValueAnalyzer(config)

        # Props
        self.prop_engine = PropEngine(config)
        self.prop_selector = PropTipSelector(config)

        # Filters
        self.odds_filter = OddsFilter(config)
        self.kombi_optimizer = KombiOptimizer(config)

        # Advanced engines
        self.clp = ClosingLinePredictor(config)
        self.sharp = SharpMoneyTracker(config)
        self.rl_stake = RLStakeEngine(config)
        self.explainer = AICoachExplainer(config)

        # Reporting
        self.report = DailyReportBuilder(config)
        self.roi = HistoricalROIAnalyzer(config)

    # ---------------------------------------------------------
    # FŐ NAPI WORKFLOW
    # ---------------------------------------------------------
    def run_daily(self):

        today = datetime.date.today().isoformat()

        # 1) Odds letöltése
        matches = self.odds.get_all_matches()

        daily_tips = []
        bankroll_start = float(self.config.get("bankroll", 1000))

        for match in matches:

            # 2) Model outputok
            model_outputs = self.runner.run_all(match)

            # 3) Ensemble rétegek
            q = self.qse.combine(model_outputs)
            f = self.fusion.combine(model_outputs)
            b = self.bayes.update(f)
            bc = self.bias.apply(b)
            val = self.value.evaluate(bc)

            # 4) Prop piacok
            market_odds = self.markets.get_markets(match["home"], match["away"])
            prop_raw = self.prop_engine.compute_prop_values(market_odds, match["stats"])
            prop_tips = self.prop_selector.select(prop_raw)

            # 5) TippmixPro availability
            if not self.tippmix.is_available(match):
                continue

            # 6) Odds filter (1.60 alatti szűrés)
            if not self.odds_filter.allow_tip(val[match["id"]]):
                continue

            tip = val[match["id"]]

            # 7) Closing line + sharp integration
            odds_history = self.odds.get_odds_history(match["id"])
            clp_res = self.clp.predict_closing_line(tip["odds"], odds_history)
            sharp = self.sharp.analyze(odds_history)

            tip["expected_closing_line"] = clp_res["expected_closing"]
            tip["clv"] = self.clp.clv(tip["odds"], clp_res["expected_closing"])
            tip["sharp_money"] = sharp["sharp_strength"]
            tip["volatility"] = sharp["volatility"]
            tip["momentum"] = sharp["momentum"]

            # 8) Stake számítás
            stake_data = self.rl_stake.compute_stake(bankroll_start, tip, self.roi.streaks())
            tip["stake"] = stake_data["stake_amount"]

            # 9) Coach magyarázat
            tip["explanation"] = self.explainer.generate_explanation(tip)

            daily_tips.append(tip)

        # 10) Kombi tipp generálása
        kombi = self.kombi_optimizer.optimize(daily_tips)

        # 11) Jelentés mentése
        bankroll_end = bankroll_start  # (itt később eredményfrissítés)
        self.report.save(today, daily_tips, kombi, bankroll_start, bankroll_end)

        # 12) ROI update
        self.roi.record_day(today, bankroll_start, bankroll_end, daily_tips)

        return {
            "date": today,
            "tips": daily_tips,
            "kombi": kombi
        }
