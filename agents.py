"""
Automated Analysis Agents for Taekwondo Performance
Scheduled tasks and automation for data collection and reporting
"""

import schedule
import time
from datetime import datetime, timedelta
from pathlib import Path
import logging

from taekwondo_scraper import TaekwondoDataScraper
from performance_analyzer import TaekwondoPerformanceAnalyzer

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('agents.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DataCollectionAgent:
    """
    Agent responsible for automated data scraping
    Runs on schedule to keep data fresh
    """

    def __init__(self, data_dir="data"):
        self.scraper = TaekwondoDataScraper(output_dir=data_dir)
        self.last_run = None

    def run_daily_update(self):
        """Daily scraping job - updates rankings and recent competitions"""
        logger.info("="*70)
        logger.info("Starting Daily Data Update")
        logger.info("="*70)

        try:
            # 1. Update world rankings
            logger.info("Updating world rankings...")
            self.scraper.scrape_world_rankings()

            # 2. Update Saudi athlete profiles
            logger.info("Updating Saudi athlete profiles...")
            self.scraper.scrape_saudi_athletes()

            # 3. Check for new competitions (last 30 days)
            logger.info("Checking for new competitions...")
            current_year = datetime.now().year
            self.scraper.scrape_competition_list(year_from=current_year, year_to=current_year)

            self.last_run = datetime.now()
            logger.info(f"Daily update completed successfully at {self.last_run}")

        except Exception as e:
            logger.error(f"Error in daily update: {e}", exc_info=True)

    def run_weekly_deep_scrape(self):
        """Weekly comprehensive scraping - includes match details"""
        logger.info("="*70)
        logger.info("Starting Weekly Deep Scrape")
        logger.info("="*70)

        try:
            # Run full scrape
            self.scraper.run_full_scrape(focus_saudi=True)

            logger.info("Weekly deep scrape completed successfully")

        except Exception as e:
            logger.error(f"Error in weekly scrape: {e}", exc_info=True)


class AnalysisAgent:
    """
    Agent responsible for automated analysis and reporting
    Generates insights and alerts
    """

    def __init__(self, data_dir="data", reports_dir="reports"):
        self.analyzer = TaekwondoPerformanceAnalyzer(data_dir=data_dir)
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(exist_ok=True)

    def generate_daily_report(self):
        """Generate daily performance summary"""
        logger.info("Generating daily report...")

        try:
            # Generate Excel report
            report_file = self.reports_dir / f"daily_report_{datetime.now().strftime('%Y%m%d')}.xlsx"
            self.analyzer.export_analysis_report(str(report_file))

            logger.info(f"Daily report generated: {report_file}")

        except Exception as e:
            logger.error(f"Error generating daily report: {e}", exc_info=True)

    def check_ranking_changes(self):
        """Monitor and alert on significant ranking changes"""
        logger.info("Checking for ranking changes...")

        try:
            # This would compare current rankings to previous day
            # For now, just log
            team_analytics = self.analyzer.analyze_saudi_team()

            logger.info(f"Current team status:")
            logger.info(f"  Active athletes: {team_analytics.total_active_athletes}")
            logger.info(f"  Athletes in Top 50: {team_analytics.athletes_in_top50}")
            logger.info(f"  Total medals: {team_analytics.total_gold + team_analytics.total_silver + team_analytics.total_bronze}")

            # Check for significant changes (would need historical data)
            # if rankings improved significantly, send alert

        except Exception as e:
            logger.error(f"Error checking ranking changes: {e}", exc_info=True)

    def identify_urgent_actions(self):
        """Identify time-sensitive opportunities or concerns"""
        logger.info("Identifying urgent actions...")

        try:
            opportunities = self.analyzer.identify_medal_opportunities()

            # Check for high-opportunity athletes close to qualification deadlines
            urgent_opportunities = [
                opp for opp in opportunities
                if opp['opportunity_score'] >= 70 and opp['gap_to_medals'] <= 5
            ]

            if urgent_opportunities:
                logger.warning(f"URGENT: {len(urgent_opportunities)} high-priority medal opportunities identified!")

                for opp in urgent_opportunities:
                    logger.warning(
                        f"  - {opp['athlete_name']} in {opp['weight_category']}: "
                        f"Rank #{opp['current_rank']}, Score {opp['opportunity_score']}"
                    )

        except Exception as e:
            logger.error(f"Error identifying urgent actions: {e}", exc_info=True)


class CompetitionMonitorAgent:
    """
    Agent to monitor upcoming competitions and participation
    """

    def __init__(self):
        self.competitions = []

    def check_upcoming_competitions(self):
        """Check for upcoming competitions in next 30 days"""
        logger.info("Checking upcoming competitions...")

        # This would integrate with competition calendar
        # For now, just a placeholder

        logger.info("No immediate competitions identified (placeholder)")

    def recommend_participation(self):
        """Recommend which athletes should participate in upcoming events"""
        logger.info("Generating participation recommendations...")

        # Would analyze athlete form, ranking points needed, etc.
        logger.info("Participation recommendations (placeholder)")


class AgentOrchestrator:
    """
    Coordinates all agents and schedules their execution
    """

    def __init__(self, data_dir="data", reports_dir="reports"):
        self.data_agent = DataCollectionAgent(data_dir=data_dir)
        self.analysis_agent = AnalysisAgent(data_dir=data_dir, reports_dir=reports_dir)
        self.competition_agent = CompetitionMonitorAgent()

    def setup_schedules(self):
        """Configure all scheduled jobs"""
        logger.info("Setting up agent schedules...")

        # Daily jobs
        schedule.every().day.at("06:00").do(self.data_agent.run_daily_update)
        schedule.every().day.at("07:00").do(self.analysis_agent.generate_daily_report)
        schedule.every().day.at("07:15").do(self.analysis_agent.check_ranking_changes)
        schedule.every().day.at("08:00").do(self.competition_agent.check_upcoming_competitions)

        # Weekly jobs
        schedule.every().monday.at("05:00").do(self.data_agent.run_weekly_deep_scrape)
        schedule.every().monday.at("09:00").do(self.analysis_agent.identify_urgent_actions)

        logger.info("All schedules configured")

    def run_immediate_analysis(self):
        """Run all analysis jobs immediately (for testing)"""
        logger.info("Running immediate analysis...")

        self.data_agent.run_daily_update()
        self.analysis_agent.generate_daily_report()
        self.analysis_agent.check_ranking_changes()
        self.analysis_agent.identify_urgent_actions()
        self.competition_agent.check_upcoming_competitions()

        logger.info("Immediate analysis complete")

    def run_forever(self):
        """Run the agent scheduler indefinitely"""
        logger.info("Starting agent scheduler...")
        logger.info("Press Ctrl+C to stop")

        self.setup_schedules()

        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute

        except KeyboardInterrupt:
            logger.info("Agent scheduler stopped")


def main():
    """Run agents"""
    orchestrator = AgentOrchestrator(data_dir="data", reports_dir="reports")

    # For testing: run immediate analysis
    orchestrator.run_immediate_analysis()

    # For production: run scheduler
    # orchestrator.run_forever()


if __name__ == "__main__":
    main()
