"""
Ranking History Tracker
Stores daily ranking snapshots to enable trend analysis and change detection
Critical component for automated alerts
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import sqlite3


class RankingHistoryTracker:
    """
    Tracks ranking changes over time for all athletes
    Enables trend analysis, change detection, and forecasting
    """

    def __init__(self, db_path: str = "data/ranking_history.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database for ranking history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create ranking history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ranking_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                athlete_name TEXT NOT NULL,
                country TEXT NOT NULL,
                weight_category TEXT NOT NULL,
                rank INTEGER NOT NULL,
                points REAL,
                gender TEXT,
                source_file TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(date, athlete_name, weight_category)
            )
        ''')

        # Create indices for fast queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_athlete_date
            ON ranking_history(athlete_name, date)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_country_date
            ON ranking_history(country, date)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_category_date
            ON ranking_history(weight_category, date)
        ''')

        conn.commit()
        conn.close()

    def record_current_rankings(self, rankings_df: pd.DataFrame, date: str = None):
        """
        Record current rankings snapshot

        Args:
            rankings_df: DataFrame with current rankings
            date: Date of snapshot (default: today)
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        conn = sqlite3.connect(self.db_path)

        # Prepare data
        rankings_df = rankings_df.copy()
        rankings_df['date'] = date

        # Required columns mapping
        column_mapping = {
            'athlete_name': 'athlete_name',
            'country': 'country',
            'weight_category': 'weight_category',
            'rank': 'rank',
            'points': 'points',
        }

        # Select and rename columns
        required_cols = list(column_mapping.keys())
        available_cols = [col for col in required_cols if col in rankings_df.columns]

        if not available_cols:
            print(f"ERROR: No ranking columns found in DataFrame")
            conn.close()
            return

        # Insert records (ignore duplicates)
        try:
            rankings_df[available_cols + ['date']].to_sql(
                'ranking_history',
                conn,
                if_exists='append',
                index=False
            )
            print(f"Recorded {len(rankings_df)} rankings for {date}")
        except sqlite3.IntegrityError as e:
            print(f"Some rankings already exist for {date} - skipping duplicates")

        conn.close()

    def get_athlete_history(self, athlete_name: str, days: int = 180) -> pd.DataFrame:
        """Get ranking history for specific athlete"""
        conn = sqlite3.connect(self.db_path)

        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        query = '''
            SELECT date, rank, points, weight_category
            FROM ranking_history
            WHERE athlete_name = ? AND date >= ?
            ORDER BY date ASC
        '''

        df = pd.read_sql_query(query, conn, params=(athlete_name, cutoff_date))
        conn.close()

        return df

    def detect_rank_changes(self, days: int = 7, min_change: int = 5) -> List[Dict]:
        """
        Detect significant ranking changes

        Args:
            days: Look back period
            min_change: Minimum rank change to report

        Returns:
            List of change events
        """
        conn = sqlite3.connect(self.db_path)

        # Get rankings from N days ago and latest
        date_old = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        date_new = datetime.now().strftime('%Y-%m-%d')

        query = '''
            WITH old_ranks AS (
                SELECT athlete_name, weight_category, rank as old_rank
                FROM ranking_history
                WHERE date = ?
            ),
            new_ranks AS (
                SELECT athlete_name, weight_category, rank as new_rank, country
                FROM ranking_history
                WHERE date = ?
            )
            SELECT
                n.athlete_name,
                n.country,
                n.weight_category,
                o.old_rank,
                n.new_rank,
                (o.old_rank - n.new_rank) as change
            FROM new_ranks n
            LEFT JOIN old_ranks o
                ON n.athlete_name = o.athlete_name
                AND n.weight_category = o.weight_category
            WHERE ABS(o.old_rank - n.new_rank) >= ?
            ORDER BY ABS(o.old_rank - n.new_rank) DESC
        '''

        df = pd.read_sql_query(query, conn, params=(date_old, date_new, min_change))
        conn.close()

        # Convert to list of dicts
        changes = df.to_dict('records')

        return changes

    def get_saudi_ranking_trends(self, days: int = 365) -> pd.DataFrame:
        """Get ranking trends for all Saudi athletes"""
        conn = sqlite3.connect(self.db_path)

        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        query = '''
            SELECT date, athlete_name, weight_category, rank, points
            FROM ranking_history
            WHERE country IN ('KSA', 'SAUDI ARABIA', 'SAUDI')
                AND date >= ?
            ORDER BY date ASC, rank ASC
        '''

        df = pd.read_sql_query(query, conn, params=(cutoff_date,))
        conn.close()

        return df

    def calculate_trend(self, athlete_name: str, days: int = 180) -> Dict:
        """
        Calculate ranking trend for athlete

        Returns:
            Dict with trend analysis (improving/stable/declining)
        """
        history = self.get_athlete_history(athlete_name, days)

        if len(history) < 2:
            return {
                'athlete': athlete_name,
                'trend': 'insufficient_data',
                'data_points': len(history),
                'change': 0
            }

        # Calculate trend
        recent_rank = history.iloc[-1]['rank']
        old_rank = history.iloc[0]['rank']
        change = old_rank - recent_rank  # Positive = improvement

        # Categorize
        if change >= 5:
            trend = 'improving'
        elif change <= -5:
            trend = 'declining'
        else:
            trend = 'stable'

        return {
            'athlete': athlete_name,
            'trend': trend,
            'change': int(change),
            'current_rank': int(recent_rank),
            'data_points': len(history),
            'days_tracked': days
        }

    def export_history_csv(self, output_file: str, days: int = 365):
        """Export ranking history to CSV"""
        conn = sqlite3.connect(self.db_path)

        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        query = '''
            SELECT *
            FROM ranking_history
            WHERE date >= ?
            ORDER BY date DESC, rank ASC
        '''

        df = pd.read_sql_query(query, conn, params=(cutoff_date,))
        conn.close()

        df.to_csv(output_file, index=False)
        print(f"Exported {len(df)} records to {output_file}")


def main():
    """Example usage and testing"""
    print("Ranking History Tracker - Initialization")
    print("=" * 70)

    tracker = RankingHistoryTracker()

    # Example: Load current rankings and record them
    rankings_file = Path("data/rankings/world_rankings_20251112.csv")

    if rankings_file.exists():
        try:
            df = pd.read_csv(rankings_file)
            if not df.empty:
                tracker.record_current_rankings(df)
                print("\nSample ranking history recorded")
        except Exception as e:
            print(f"Could not load rankings: {e}")

    # Example: Detect changes
    print("\nDetecting rank changes...")
    changes = tracker.detect_rank_changes(days=7, min_change=5)

    if changes:
        print(f"Found {len(changes)} significant changes:")
        for change in changes[:5]:
            print(f"  {change['athlete_name']} ({change['weight_category']}): "
                  f"{change['old_rank']} -> {change['new_rank']} "
                  f"({change['change']:+d})")
    else:
        print("  No significant changes (may need more historical data)")

    print("\n" + "=" * 70)
    print("Ranking tracker ready for automated daily updates")


if __name__ == "__main__":
    main()
