"""
Alert and Notification System
Send email/SMS alerts for important events
"""

import os
import logging
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
from dataclasses import dataclass

# Email sending (install: pip install sendgrid)
try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False
    print("SendGrid not installed. Run: pip install sendgrid")

# Environment variables
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class Alert:
    """Alert data structure"""
    title: str
    message: str
    severity: str  # 'info', 'warning', 'critical'
    category: str  # 'ranking', 'opportunity', 'competition', 'performance'
    athlete_name: Optional[str] = None
    data: Optional[Dict] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class AlertSystem:
    """
    Comprehensive alert and notification system
    Supports email, SMS, and logging
    """

    def __init__(self, config_path: str = ".env"):
        """Initialize alert system with configuration"""

        # Load configuration
        self.sendgrid_api_key = os.getenv('SENDGRID_API_KEY')
        self.alert_emails = os.getenv('ALERT_EMAILS', '').split(',')
        self.alert_emails = [email.strip() for email in self.alert_emails if email.strip()]

        self.from_email = os.getenv('FROM_EMAIL', 'analytics@saudi-taekwondo.com')

        # Alert settings
        self.enabled = os.getenv('ALERTS_ENABLED', 'true').lower() == 'true'
        self.ranking_change_threshold = int(os.getenv('RANKING_CHANGE_THRESHOLD', '5'))
        self.opportunity_score_threshold = float(os.getenv('OPPORTUNITY_SCORE_THRESHOLD', '75'))

        # Validation
        if self.enabled and not SENDGRID_AVAILABLE:
            logger.warning("Alerts enabled but SendGrid not installed")
            self.enabled = False

        if self.enabled and not self.sendgrid_api_key:
            logger.warning("Alerts enabled but SENDGRID_API_KEY not set")
            self.enabled = False

        if not self.alert_emails:
            logger.warning("No alert email recipients configured")

        # Alert history (for deduplication)
        self.alert_history = []

    def send_email(self, subject: str, html_content: str, recipients: List[str] = None) -> bool:
        """
        Send email via SendGrid

        Args:
            subject: Email subject
            html_content: HTML email body
            recipients: List of recipient emails (default: from config)

        Returns:
            True if sent successfully
        """
        if not self.enabled:
            logger.info(f"Alerts disabled. Would have sent: {subject}")
            return False

        if recipients is None:
            recipients = self.alert_emails

        if not recipients:
            logger.warning("No recipients specified for email")
            return False

        try:
            # Create email message
            message = Mail(
                from_email=self.from_email,
                to_emails=recipients,
                subject=subject,
                html_content=html_content
            )

            # Send via SendGrid
            sg = SendGridAPIClient(self.sendgrid_api_key)
            response = sg.send(message)

            logger.info(f"Email sent: {subject} to {len(recipients)} recipients")
            logger.debug(f"SendGrid response: {response.status_code}")

            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    def send_alert(self, alert: Alert) -> bool:
        """
        Send alert via configured channels

        Args:
            alert: Alert object

        Returns:
            True if sent successfully
        """
        # Check if duplicate (sent in last hour)
        if self._is_duplicate(alert):
            logger.info(f"Skipping duplicate alert: {alert.title}")
            return False

        # Create email content
        subject = self._format_subject(alert)
        html_content = self._format_html_email(alert)

        # Send email
        success = self.send_email(subject, html_content)

        if success:
            self.alert_history.append({
                'alert': alert,
                'timestamp': datetime.now()
            })

        return success

    def _is_duplicate(self, alert: Alert, window_hours: int = 1) -> bool:
        """Check if similar alert was sent recently"""
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(hours=window_hours)

        for hist in self.alert_history:
            if hist['timestamp'] > cutoff:
                if (hist['alert'].title == alert.title and
                    hist['alert'].athlete_name == alert.athlete_name):
                    return True

        return False

    def _format_subject(self, alert: Alert) -> str:
        """Format email subject line"""
        severity_emoji = {
            'info': 'ℹ️',
            'warning': '⚠️',
            'critical': '🚨'
        }

        emoji = severity_emoji.get(alert.severity, '')

        if alert.athlete_name:
            return f"{emoji} Saudi Taekwondo: {alert.title} - {alert.athlete_name}"
        else:
            return f"{emoji} Saudi Taekwondo: {alert.title}"

    def _format_html_email(self, alert: Alert) -> str:
        """Format HTML email content"""
        severity_colors = {
            'info': '#17a2b8',
            'warning': '#ffc107',
            'critical': '#dc3545'
        }

        color = severity_colors.get(alert.severity, '#333')

        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: #1e4d2b; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .alert-box {{ border-left: 4px solid {color}; background-color: #f8f9fa; padding: 15px; margin: 15px 0; }}
                .data-table {{ border-collapse: collapse; width: 100%; margin-top: 15px; }}
                .data-table th, .data-table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                .data-table th {{ background-color: #1e4d2b; color: white; }}
                .footer {{ background-color: #f1f1f1; padding: 10px; text-align: center; font-size: 12px; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🥋 Saudi Arabia Taekwondo Analytics</h1>
            </div>

            <div class="content">
                <div class="alert-box">
                    <h2>{alert.title}</h2>
                    <p><strong>Severity:</strong> {alert.severity.upper()}</p>
                    <p><strong>Category:</strong> {alert.category}</p>
                    {f'<p><strong>Athlete:</strong> {alert.athlete_name}</p>' if alert.athlete_name else ''}
                    <p><strong>Time:</strong> {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>

                <div>
                    <h3>Details</h3>
                    <p>{alert.message}</p>
                </div>
        """

        # Add data table if available
        if alert.data:
            html += """
                <table class="data-table">
                    <tr>
                        <th>Field</th>
                        <th>Value</th>
                    </tr>
            """

            for key, value in alert.data.items():
                html += f"""
                    <tr>
                        <td>{key}</td>
                        <td>{value}</td>
                    </tr>
                """

            html += "</table>"

        html += """
            </div>

            <div class="footer">
                <p>This is an automated alert from the Saudi Arabia Taekwondo Performance Analysis System</p>
                <p>For questions, contact your analytics team</p>
            </div>
        </body>
        </html>
        """

        return html

    # Pre-defined alert templates

    def alert_ranking_change(self, athlete_name: str, old_rank: int, new_rank: int, points_change: float):
        """Alert when athlete ranking changes significantly"""
        rank_change = old_rank - new_rank  # Positive = improvement

        if abs(rank_change) < self.ranking_change_threshold:
            return  # Change too small to alert

        severity = 'critical' if abs(rank_change) >= 10 else 'warning'

        if rank_change > 0:
            message = f"{athlete_name} has improved from rank #{old_rank} to #{new_rank} (↑{rank_change} positions)"
        else:
            message = f"{athlete_name} has dropped from rank #{old_rank} to #{new_rank} (↓{abs(rank_change)} positions)"

        alert = Alert(
            title="Ranking Change Detected",
            message=message,
            severity=severity,
            category='ranking',
            athlete_name=athlete_name,
            data={
                'Previous Rank': old_rank,
                'New Rank': new_rank,
                'Change': f"{'+' if rank_change > 0 else ''}{rank_change}",
                'Points Change': f"{'+' if points_change > 0 else ''}{points_change:.1f}"
            }
        )

        self.send_alert(alert)

    def alert_medal_opportunity(self, athlete_name: str, category: str, opportunity_score: float, current_rank: int):
        """Alert when high medal opportunity identified"""
        if opportunity_score < self.opportunity_score_threshold:
            return  # Score too low to alert

        severity = 'critical' if opportunity_score >= 90 else 'warning'

        message = f"HIGH MEDAL OPPORTUNITY: {athlete_name} in {category} has an opportunity score of {opportunity_score:.1f}/100 (Rank #{current_rank})"

        alert = Alert(
            title="Medal Opportunity Identified",
            message=message,
            severity=severity,
            category='opportunity',
            athlete_name=athlete_name,
            data={
                'Weight Category': category,
                'Current Rank': current_rank,
                'Opportunity Score': f"{opportunity_score:.1f}/100",
                'Recommendation': 'Prioritize Grand Prix participation'
            }
        )

        self.send_alert(alert)

    def alert_competition_deadline(self, competition_name: str, deadline_date: datetime, days_remaining: int):
        """Alert for upcoming competition entry deadlines"""
        severity = 'critical' if days_remaining <= 7 else 'warning'

        message = f"Entry deadline for {competition_name} is in {days_remaining} days ({deadline_date.strftime('%Y-%m-%d')})"

        alert = Alert(
            title="Competition Entry Deadline Approaching",
            message=message,
            severity=severity,
            category='competition',
            data={
                'Competition': competition_name,
                'Deadline': deadline_date.strftime('%Y-%m-%d'),
                'Days Remaining': days_remaining
            }
        )

        self.send_alert(alert)

    def alert_upset_loss(self, athlete_name: str, opponent_name: str, athlete_rank: int, opponent_rank: int):
        """Alert when athlete loses to lower-ranked opponent"""
        rank_gap = opponent_rank - athlete_rank

        message = f"UPSET LOSS: {athlete_name} (Rank #{athlete_rank}) lost to {opponent_name} (Rank #{opponent_rank})"

        alert = Alert(
            title="Upset Loss Detected",
            message=message,
            severity='warning',
            category='performance',
            athlete_name=athlete_name,
            data={
                'Athlete Rank': athlete_rank,
                'Opponent': opponent_name,
                'Opponent Rank': opponent_rank,
                'Rank Gap': rank_gap,
                'Action': 'Review match video and opponent analysis'
            }
        )

        self.send_alert(alert)

    def alert_daily_summary(self, summary_data: dict):
        """Send daily summary alert"""
        message = f"""
        Daily summary for {datetime.now().strftime('%Y-%m-%d')}:

        - Total active athletes: {summary_data.get('total_athletes', 0)}
        - Athletes in Top 50: {summary_data.get('top50_athletes', 0)}
        - Ranking changes today: {summary_data.get('ranking_changes', 0)}
        - Upcoming competitions (30 days): {summary_data.get('upcoming_competitions', 0)}
        """

        alert = Alert(
            title="Daily Performance Summary",
            message=message,
            severity='info',
            category='summary',
            data=summary_data
        )

        self.send_alert(alert)


# Example usage
if __name__ == "__main__":
    # Create .env file with:
    # SENDGRID_API_KEY=your_key_here
    # ALERT_EMAILS=coach@example.com,analyst@example.com
    # ALERTS_ENABLED=true

    alert_system = AlertSystem()

    # Test ranking change alert
    alert_system.alert_ranking_change(
        athlete_name="Ahmed Ali",
        old_rank=48,
        new_rank=42,
        points_change=12.5
    )

    # Test medal opportunity alert
    alert_system.alert_medal_opportunity(
        athlete_name="Fahad Hassan",
        category="M-68kg",
        opportunity_score=85.3,
        current_rank=12
    )

    # Test competition deadline alert
    from datetime import timedelta
    alert_system.alert_competition_deadline(
        competition_name="2024 Grand Prix - Paris",
        deadline_date=datetime.now() + timedelta(days=6),
        days_remaining=6
    )

    print("Alert tests completed!")
