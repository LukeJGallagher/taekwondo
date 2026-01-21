"""
Alert and Notification System - Free Version
Logs alerts to file instead of sending emails (no SendGrid required)
"""

import os
import logging
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class Alert:
    title: str
    message: str
    severity: str
    category: str
    athlete_name: Optional[str] = None
    data: Optional[Dict] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class AlertSystemFree:
    def __init__(self, log_dir: str = "alerts"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.ranking_change_threshold = int(os.getenv('RANKING_CHANGE_THRESHOLD', '5'))
        self.opportunity_score_threshold = float(os.getenv('OPPORTUNITY_SCORE_THRESHOLD', '75'))
        self.alert_history = []

    def log_alert(self, alert: Alert) -> bool:
        try:
            log_file = self.log_dir / f"alerts_{datetime.now().strftime('%Y%m%d')}.log"
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write(f"{alert.title}\n")
                f.write(f"Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Severity: {alert.severity.upper()}\n")
                f.write(f"Category: {alert.category}\n")
                if alert.athlete_name:
                    f.write(f"Athlete: {alert.athlete_name}\n")
                f.write(f"\nMessage: {alert.message}\n")
                if alert.data:
                    f.write("\nData:\n")
                    for k, v in alert.data.items():
                        f.write(f"  {k}: {v}\n")
                f.write("=" * 80 + "\n\n")
            logger.info(f"ALERT: {alert.title}")
            return True
        except Exception as e:
            logger.error(f"Failed to log alert: {e}")
            return False

    def send_alert(self, alert: Alert) -> bool:
        return self.log_alert(alert)

    def alert_ranking_change(self, athlete_name: str, old_rank: int, new_rank: int, points_change: float):
        rank_change = old_rank - new_rank
        if abs(rank_change) < self.ranking_change_threshold:
            return
        severity = 'critical' if abs(rank_change) >= 10 else 'warning'
        message = f"{athlete_name}: Rank {old_rank} -> {new_rank} (change: {rank_change:+d})"
        alert = Alert("Ranking Change", message, severity, 'ranking', athlete_name, 
                     {'Old Rank': old_rank, 'New Rank': new_rank, 'Change': rank_change})
        self.send_alert(alert)

    def alert_medal_opportunity(self, athlete_name: str, category: str, opportunity_score: float, current_rank: int):
        if opportunity_score < self.opportunity_score_threshold:
            return
        severity = 'critical' if opportunity_score >= 90 else 'warning'
        message = f"Medal opportunity: {athlete_name} in {category} (Score: {opportunity_score:.1f})"
        alert = Alert("Medal Opportunity", message, severity, 'opportunity', athlete_name,
                     {'Category': category, 'Rank': current_rank, 'Score': opportunity_score})
        self.send_alert(alert)

    def alert_daily_summary(self, summary_data: dict):
        message = f"Active: {summary_data.get('total_athletes', 0)}, Top 50: {summary_data.get('top50_athletes', 0)}"
        alert = Alert("Daily Summary", message, 'info', 'summary', data=summary_data)
        self.send_alert(alert)


if __name__ == "__main__":
    print("Testing Free Alert System")
    alert_system = AlertSystemFree()
    alert_system.alert_ranking_change("Ahmed Ali", 48, 42, 12.5)
    alert_system.alert_medal_opportunity("Fahad Hassan", "M-68kg", 85.3, 12)
    print("Alerts logged to 'alerts' directory")
