# backend/reporting/daily_reporter.py

import csv
import os
import datetime
from openpyxl import Workbook

class DailyReporter:
    """
    DAILY REPORT ENGINE
    -------------------
    Minden nap:
        - összegyűjti a tippeket
        - eredményeket beolvassa
        - bankroll frissítés
        - ROI számítás
        - CSV + Excel riport készítés
    """

    def __init__(self, config):
        self.config = config
        self.history_dir = "backend/data/history"
        os.makedirs(self.history_dir, exist_ok=True)

    # -------------------------------------------------------
    # MENTÉS CSV-BE
    # -------------------------------------------------------
    def save_csv(self, filename, rows):
        path = os.path.join(self.history_dir, filename)

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(rows)

        return path

    # -------------------------------------------------------
    # MENTÉS EXCELBE
    # -------------------------------------------------------
    def save_excel(self, filename, rows):
        path = os.path.join(self.history_dir, filename)

        wb = Workbook()
        ws = wb.active

        for row in rows:
            ws.append(row)

        wb.save(path)

        return path

    # -------------------------------------------------------
    # FŐ RIPORT GENERÁLÁS
    # -------------------------------------------------------
    def generate_daily_report(self, tips, results, bankroll_before, bankroll_after):

        today = datetime.date.today().strftime("%Y-%m-%d")

        rows = []
        rows.append(["Dátum", today])
        rows.append(["Bankroll induló", bankroll_before])
        rows.append(["Bankroll záró", bankroll_after])
        rows.append(["Változás", round(bankroll_after - bankroll_before, 2)])
        rows.append([])
        rows.append([
            "Meccs",
            "Piac",
            "Tipp típusa",
            "Odds",
            "Stake",
            "Eredmény",
            "Profit/Loss",
            "Value Score",
            "Deep Value",
            "Confidence"
        ])

        for tip in tips:
            m = results.get(tip["match_id"], {})
            outcome = m.get("result", "pending")
            pnl = m.get("profit", 0)

            rows.append([
                tip["match"],
                tip["market"],
                tip["type"],
                tip["odds"],
                tip["stake"],
                outcome,
                pnl,
                tip.get("value_score", "-"),
                tip.get("deep_value", "-"),
                tip.get("confidence", "-"),
            ])

        csv_name = f"daily_report_{today}.csv"
        xlsx_name = f"daily_report_{today}.xlsx"

        csv_path = self.save_csv(csv_name, rows)
        xlsx_path = self.save_excel(xlsx_name, rows)

        return {
            "csv": csv_path,
            "excel": xlsx_path,
            "summary": f"Daily report saved for {today}"
        }
