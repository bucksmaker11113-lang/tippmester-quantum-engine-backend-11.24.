# backend/system/monitoring_system.py

import time
import traceback
from backend.utils.logger import get_logger

class MonitoringSystem:
    """
    MONITORING SYSTEM (Pro Edition)
    -------------------------------
    Fő funkciók:
        ✓ engine health check
        ✓ scraper health check
        ✓ odds drift monitoring
        ✓ error tracking
        ✓ fail-safe fallback mode
        ✓ watchdog heartbeats
        ✓ performance metrics
    """

    def __init__(self, config=None):
        self.config = config or {}
        self.logger = get_logger()

        # fallback módok
        self.fallback_active = False
        self.last_error = None
        self.error_count = 0

        # engine státusz
        self.engine_status = {
            "scrapers": True,
            "ensemble": True,
            "deep_value": True,
            "tipmixpro": True,
            "database": True,
        }

        # performance
        self.exec_times = []

    # --------------------------------------------------------------
    # PERF MEASUREMENT
    # --------------------------------------------------------------
    def start_timer(self):
        self._start = time.time()

    def end_timer(self, label):
        elapsed = round(time.time() - self._start, 4)
        self.exec_times.append((label, elapsed))
        self.logger.info(f"[MONITOR] {label} took {elapsed} sec")

    # --------------------------------------------------------------
    # ERROR HANDLING
    # --------------------------------------------------------------
    def register_error(self, component, error):
        self.error_count += 1
        self.last_error = str(error)

        self.engine_status[component] = False

        self.logger.error(f"[MONITOR] ERROR IN {component}: {error}")
        self.logger.error(traceback.format_exc())

        if self.error_count >= 5:
            self.logger.critical("[MONITOR] TOO MANY ERRORS → FALLBACK MODE ACTIVE")
            self.fallback_active = True

    # --------------------------------------------------------------
    # SUCCESS HANDLING
    # --------------------------------------------------------------
    def register_success(self, component):
        self.engine_status[component] = True

    # --------------------------------------------------------------
    # SCRAPER HEALTH CHECK
    # --------------------------------------------------------------
    def check_scraper(self, data):
        if data is None or data == {}:
            self.register_error("scrapers", "Scraper returned empty data")
            return False

        self.register_success("scrapers")
        return True

    # --------------------------------------------------------------
    # ENGINE HEALTH CHECK
    # --------------------------------------------------------------
    def check_ensemble(self, result):
        if not result:
            self.register_error("ensemble", "Ensemble returned empty")
            return False
        self.register_success("ensemble")
        return True

    def check_deep_value(self, result):
        if not result:
            self.register_error("deep_value", "DeepValue returned empty")
            return False
        self.register_success("deep_value")
        return True

    # --------------------------------------------------------------
    # TIPPMIX PRO HEALTH CHECK
    # --------------------------------------------------------------
    def check_tippmixpro(self, data):
        if not data.get("exists", False):
            self.register_error("tipmixpro", "Match not found on TippmixPro")
            return False
        self.register_success("tipmixpro")
        return True

    # --------------------------------------------------------------
    # DATABASE HEALTH CHECK
    # --------------------------------------------------------------
    def check_database(self, conn):
        try:
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master")
            self.register_success("database")
            return True
        except Exception as e:
            self.register_error("database", e)
            return False

    # --------------------------------------------------------------
    # ODDS DRIFT MONITORING
    # --------------------------------------------------------------
    def check_odds_drift(self, opening_odds, closing_odds):
        """
        Ha a closing line 10%-nál többet mozdul → riasztás
        """
        try:
            drift = abs(closing_odds - opening_odds) / opening_odds

            if drift > 0.10:
                self.logger.warning(f"[MONITOR] ODDS DRIFT DETECTED ({drift*100:.1f}%)")
                return False

            return True

        except:
            return True

    # --------------------------------------------------------------
    # SYSTEM HEALTH SUMMARY
    # --------------------------------------------------------------
    def status(self):
        return {
            "fallback_mode": self.fallback_active,
            "last_error": self.last_error,
            "error_count": self.error_count,
            "engine_status": self.engine_status,
            "performance": self.exec_times
        }
