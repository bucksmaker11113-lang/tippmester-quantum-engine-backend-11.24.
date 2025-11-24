# Hová kerüljön:
# backend/system/scheduler.py

"""
SCHEDULER – MODERN IDŐZÍTŐ RENDSZER A NAPI AI FUTÁSHOZ
--------------------------------------------------------
Feladata:
    - napi AI workflow automatikus futtatása
    - SystemFlow és MasterOrchestrator integráció
    - időzített JSON export
    - loggolás és hibatűrés

Ez a verzió kompatibilis:
✔ FastAPI backenddel
✔ supervisor / pm2 / cron környezetekkel
✔ manuális és automata futtatással
"""

import time
import datetime
import threading

from system.system_flow import SystemFlowInstance


class Scheduler:
    def __init__(self):
        self.running = False
        self.interval_hours = 24  # napi futás
        self.export_path = "daily_ai_tips.json"

    # =====================================================================
    # IDŐZÍTETT FUTTATÁS INDÍTÁSA
    # =====================================================================
    def start(self):
        if self.running:
            print("[SCHEDULER] Már fut.")
            return

        print("[SCHEDULER] Elindítva…")
        self.running = True

        thread = threading.Thread(target=self._loop)
        thread.daemon = True
        thread.start()

    # =====================================================================
    # IDŐZÍTŐ LOOP
    # =====================================================================
    def _loop(self):
        while self.running:
            now = datetime.datetime.utcnow()
            print(f"[SCHEDULER] Napi AI futtatás: {now}")

            try:
                # 1) AI futtatás
                results = SystemFlowInstance.test_run()

                # 2) Export
                SystemFlowInstance.export_tips(results, self.export_path)

            except Exception as e:
                print("[SCHEDULER] Hiba történt:", e)

            # 3) Várakozás a következő futásig
            time.sleep(self.interval_hours * 3600)

    # =====================================================================
    # LEÁLLÍTÁS
    # =====================================================================
    def stop(self):
        print("[SCHEDULER] Leállítva.")
        self.running = False


# Globális példány
SchedulerInstance = Scheduler()
