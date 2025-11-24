# backend/system/scheduler.py

import time
import threading
import traceback
from datetime import datetime
from backend.system.system_flow import SystemFlow
from backend.system.monitoring_system import MonitoringSystem
from backend.utils.logger import get_logger


class Scheduler:
    """
    PRO SCHEDULER / INTERNAL CRON ENGINE
    ------------------------------------
    Funkciók:
        ✓ napi predikció 10:00
        ✓ napi tanulás 23:59
        ✓ watchdog monitor loop
        ✓ hiba esetén fallback mód
        ✓ logolás
    """

    def __init__(self, config):
        self.config = config
        self.logger = get_logger()
        self.flow = SystemFlow(config)
        self.monitor = MonitoringSystem(config)

        self.running = True

        # időpontok
        self.prediction_time = config.get("schedule_pred_time", "10:00")
        self.training_time = config.get("schedule_train_time", "23:59")

    # -------------------------------------------------------------
    # IDŐ ELLENŐRZÉSE
    # -------------------------------------------------------------
    def _now_str(self):
        return datetime.now().strftime("%H:%M")

    # -------------------------------------------------------------
    # PREDIKCIÓ FUTTATÁSA
    # -------------------------------------------------------------
    def _run_prediction(self):
        try:
            self.logger.info("[SCHEDULER] Running daily prediction...")

            self.monitor.start_timer()

            result = self.flow.run_daily_prediction()

            self.monitor.end_timer("daily_prediction")

            if not self.monitor.check_ensemble(result.get("predictions")):
                self.logger.warning("[SCHEDULER] Prediction failed → fallback")

        except Exception as e:
            self.monitor.register_error("scheduler_prediction", e)

    # -------------------------------------------------------------
    # NAPI TANULÁS FUTTATÁSA
    # -------------------------------------------------------------
    def _run_training(self):
        try:
            self.logger.info("[SCHEDULER] Running daily training...")

            self.monitor.start_timer()

            ok = self.flow.run_daily_retrain()

            self.monitor.end_timer("daily_training")

            if not ok:
                self.monitor.register_error("scheduler_training", "training failed")

        except Exception as e:
            self.monitor.register_error("scheduler_training", e)

    # -------------------------------------------------------------
    # MAIN LOOP (külön threadben fut)
    # -------------------------------------------------------------
    def _loop(self):
        self.logger.info("[SCHEDULER] STARTED.")

        while self.running:

            try:
                now = self._now_str()

                # 1) napi predikció
                if now == self.prediction_time:
                    self._run_prediction()
                    time.sleep(60)

                # 2) napi training
                if now == self.training_time:
                    self._run_training()
                    time.sleep(60)

                # 3) watchdog
                if self.monitor.fallback_active:
                    self.logger.warning("[SCHEDULER] FALLBACK ACTIVE — SAFE MODE")
                    time.sleep(5)
                else:
                    time.sleep(1)

            except Exception as e:
                self.monitor.register_error("scheduler_loop", e)
                time.sleep(2)

    # -------------------------------------------------------------
    # START
    # -------------------------------------------------------------
    def start(self):
        thread = threading.Thread(target=self._loop)
        thread.daemon = True
        thread.start()
        return thread

    # -------------------------------------------------------------
    # STOP
    # -------------------------------------------------------------
    def stop(self):
        self.running = False
        self.logger.info("[SCHEDULER] STOPPED.")
