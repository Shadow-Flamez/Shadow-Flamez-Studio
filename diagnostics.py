"""
diagnostics.py - Performance Monitoring & System Logging
"""
import logging
import time
from typing import Dict, List, Any

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("StudioLogger")


class DiagnosticsTracker:
    def __init__(self):
        self.start_time = time.time()
        self.tasks_logged: List[Dict[str, Any]] = []

    def record_task(self, task_name: str, duration: float, status: str = "SUCCESS", details: str = ""):
        entry = {
            "task": task_name,
            "duration_sec": round(duration, 2),
            "status": status,
            "details": details,
            "timestamp": time.strftime("%H:%M:%S")
        }
        self.tasks_logged.append(entry)
        logger.info(f"Task: {task_name} | Status: {status} | Duration: {duration:.2f}s | Details: {details}")

    def generate_report_html(self) -> str:
        uptime = round(time.time() - self.start_time, 1)
        total_tasks = len(self.tasks_logged)

        rows = ""
        for t in reversed(self.tasks_logged[-10:]):  # Show last 10 tasks
            color = "#00ff66" if t["status"] == "SUCCESS" else "#ff0055"
            rows += f"""
            <tr>
                <td style="padding:8px; border-bottom: 1px solid #333;">{t['timestamp']}</td>
                <td style="padding:8px; border-bottom: 1px solid #333;">{t['task']}</td>
                <td style="padding:8px; border-bottom: 1px solid #333; color: {color};">{t['status']}</td>
                <td style="padding:8px; border-bottom: 1px solid #333;">{t['duration_sec']}s</td>
                <td style="padding:8px; border-bottom: 1px solid #333;">{t['details']}</td>
            </tr>
            """

        if not rows:
            rows = "<tr><td colspan='5' style='padding:10px; text-align:center; color:#888;'>No tasks processed yet.</td></tr>"

        return f"""
        <div style="background: #12141d; padding: 15px; border-radius: 8px; font-family: monospace; color: #fff;">
            <div style="display: flex; gap: 20px; margin-bottom: 15px;">
                <div><strong>Uptime:</strong> {uptime}s</div>
                <div><strong>Tasks Executed:</strong> {total_tasks}</div>
            </div>
            <table style="width: 100%; border-collapse: collapse; text-align: left; font-size: 13px;">
                <thead>
                    <tr style="border-bottom: 2px solid #00ffff; color: #00ffff;">
                        <th style="padding:8px;">Time</th>
                        <th style="padding:8px;">Task</th>
                        <th style="padding:8px;">Status</th>
                        <th style="padding:8px;">Duration</th>
                        <th style="padding:8px;">Details</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </div>
        """


diagnostics = DiagnosticsTracker()
