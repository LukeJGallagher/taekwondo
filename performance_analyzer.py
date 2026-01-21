"""
Performance Analysis Engine for Taekwondo
Saudi-focused analytics and insights
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import json

from models import (
    Athlete, Match, Competition, PerformanceMetrics,
    SaudiTeamAnalytics, CompetitionLevel, WeightCategory
)


class TaekwondoPerformanceAnalyzer:
    """
    Advanced performance analysis for taekwondo athletes and teams
    Focus on Saudi Arabia performance and strategic insights
    """

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)

        # Additional data directories
        self.wt_detailed_dir = Path("data_wt_detailed")
        self.all_categories_dir = Path("data_all_categories")
        self.extracted_data_dir = Path("extracted_data")  # PDF extracted data

        # Load data
        self.athletes_df = None
        self.matches_df = None
        self.competitions_df = None
        self.rankings_df = None

        self._load_data()

    def _load_data(self):
        """Load all available data from scraped sources"""
        print("Loading data...")

        # Load athletes
        athlete_files = list((self.data_dir / "athletes").glob("*.csv"))
        if athlete_files:
            try:
                self.athletes_df = pd.read_csv(athlete_files[0])
                if not self.athletes_df.empty:
                    print(f"  Loaded {len(self.athletes_df)} athletes")
                else:
                    print("  Athletes file is empty - run scraper to collect data")
            except pd.errors.EmptyDataError:
                print("  Athletes file is empty - run scraper to collect data")
                self.athletes_df = None
        else:
            print("  No athlete files found - run scraper to collect data")

        # Load rankings
        ranking_files = list((self.data_dir / "rankings").glob("*.csv"))
        if ranking_files:
            try:
                # Get most recent
                self.rankings_df = pd.read_csv(sorted(ranking_files)[-1])
                if not self.rankings_df.empty:
                    print(f"  Loaded {len(self.rankings_df)} rankings")
                else:
                    print("  Rankings file is empty - run scraper to collect data")
            except (pd.errors.EmptyDataError, Exception) as e:
                print(f"  Could not load rankings: {e}")
                self.rankings_df = None
        else:
            print("  No ranking files found - run scraper to collect data")

        # Load matches (if available)
        # First check data_wt_detailed for competition results
        match_files = []

        if self.wt_detailed_dir.exists():
            wt_match_files = list(self.wt_detailed_dir.glob("*_results_table_0.csv"))
            if wt_match_files:
                match_files.extend(wt_match_files)
                print(f"  Found {len(wt_match_files)} competition result files")

        # Also check data/matches directory
        data_match_dir = self.data_dir / "matches"
        if data_match_dir.exists():
            data_match_files = list(data_match_dir.glob("*.csv"))
            match_files.extend(data_match_files)

        if match_files:
            try:
                dfs = []
                for f in match_files:
                    try:
                        df = pd.read_csv(f)
                        if not df.empty:
                            # Add source file info
                            df['source_file'] = f.name
                            dfs.append(df)
                    except (pd.errors.EmptyDataError, Exception) as e:
                        continue

                if dfs:
                    self.matches_df = pd.concat(dfs, ignore_index=True)
                    print(f"  Loaded {len(self.matches_df)} matches from {len(dfs)} competitions")
                else:
                    print("  Match files are empty")
            except Exception as e:
                print(f"  Could not load matches: {e}")
                self.matches_df = None
        else:
            print("  No match files found - run scraper to collect match data")

        # Load PDF-extracted data (additional historical data)
        if self.extracted_data_dir.exists():
            pdf_data_loaded = self._load_pdf_extracted_data()
            if pdf_data_loaded > 0:
                print(f"  Loaded {pdf_data_loaded} additional records from PDF extraction")

    def analyze_saudi_athlete(self, athlete_name: str) -> PerformanceMetrics:
        """
        Comprehensive performance analysis for a Saudi athlete
        """
        if self.athletes_df is None:
            print("No athlete data available")
            return None

        # Find athlete
        athlete = self.athletes_df[
            self.athletes_df['athlete_name'].str.contains(athlete_name, case=False, na=False)
        ]

        if athlete.empty:
            print(f"Athlete '{athlete_name}' not found")
            return None

        athlete_data = athlete.iloc[0]

        metrics = PerformanceMetrics(
            athlete_id=str(athlete_data.get('athlete_id', 'unknown')),
            analysis_date=datetime.now()
        )

        # Calculate metrics from available data
        if self.matches_df is not None:
            athlete_matches = self.matches_df[
                (self.matches_df['athlete1_name'] == athlete_name) |
                (self.matches_df['athlete2_name'] == athlete_name)
            ]

            # Recent form (last 6 months)
            six_months_ago = datetime.now() - timedelta(days=180)
            recent_matches = athlete_matches[
                pd.to_datetime(athlete_matches['date']) >= six_months_ago
            ]

            metrics.recent_matches = len(recent_matches)

            # Calculate wins/losses
            wins = len(recent_matches[recent_matches['winner_name'] == athlete_name])
            metrics.recent_wins = wins
            metrics.recent_losses = metrics.recent_matches - wins

            if metrics.recent_matches > 0:
                metrics.recent_win_rate = (wins / metrics.recent_matches) * 100

        return metrics

    def analyze_saudi_team(self) -> SaudiTeamAnalytics:
        """
        Team-level analytics for Saudi Arabia
        """
        analytics = SaudiTeamAnalytics(analysis_date=datetime.now())

        if self.athletes_df is None:
            return analytics

        # Filter Saudi athletes
        saudi_athletes = self.athletes_df[
            self.athletes_df['country'].str.upper().isin(['KSA', 'SAUDI ARABIA', 'SAUDI'])
        ]

        analytics.total_active_athletes = len(saudi_athletes)

        # Ranking distribution
        if 'rank' in saudi_athletes.columns:
            saudi_athletes['rank'] = pd.to_numeric(saudi_athletes['rank'], errors='coerce')

            analytics.athletes_in_top10 = len(saudi_athletes[saudi_athletes['rank'] <= 10])
            analytics.athletes_in_top50 = len(saudi_athletes[saudi_athletes['rank'] <= 50])
            analytics.athletes_in_top100 = len(saudi_athletes[saudi_athletes['rank'] <= 100])

        # Medal counts (if available)
        if 'gold_medals' in saudi_athletes.columns:
            analytics.total_gold = saudi_athletes['gold_medals'].sum()
            analytics.total_silver = saudi_athletes['silver_medals'].sum()
            analytics.total_bronze = saudi_athletes['bronze_medals'].sum()

        return analytics

    def benchmark_against_rivals(self, rival_countries: List[str] = None) -> pd.DataFrame:
        """
        Compare Saudi performance against key rival nations
        Default rivals: South Korea, Iran, Jordan, Turkey, China
        """
        if rival_countries is None:
            rival_countries = ['KOR', 'IRI', 'JOR', 'TUR', 'CHN', 'GBR', 'FRA', 'MEX']

        if self.rankings_df is None:
            print("No ranking data available")
            return pd.DataFrame()

        # Add Saudi Arabia to comparison
        countries = ['KSA'] + rival_countries

        comparison_data = []

        for country in countries:
            # Handle both 'country' and 'MEMBER NATION' column names
            country_col = 'country' if 'country' in self.rankings_df.columns else 'MEMBER NATION'

            country_athletes = self.rankings_df[
                self.rankings_df[country_col].str.upper().str.contains(country, na=False)
            ]

            if not country_athletes.empty:
                # Convert rank to numeric (handle both 'rank' and 'RANK')
                rank_col = 'rank' if 'rank' in country_athletes.columns else 'RANK'
                country_athletes['rank'] = pd.to_numeric(
                    country_athletes[rank_col],
                    errors='coerce'
                )

                comparison_data.append({
                    'country': country,
                    'total_ranked_athletes': len(country_athletes),
                    'athletes_in_top10': len(country_athletes[country_athletes['rank'] <= 10]),
                    'athletes_in_top50': len(country_athletes[country_athletes['rank'] <= 50]),
                    'average_rank': country_athletes['rank'].mean(),
                    'best_rank': country_athletes['rank'].min(),
                    'total_ranking_points': country_athletes['points'].sum()
                        if 'points' in country_athletes.columns else 0
                })

        df = pd.DataFrame(comparison_data)
        df = df.sort_values('total_ranking_points', ascending=False)

        return df

    def identify_medal_opportunities(self) -> List[Dict]:
        """
        Identify weight categories where Saudi athletes have best medal chances
        Based on current rankings and competition
        """
        opportunities = []

        if self.rankings_df is None:
            return opportunities

        # Check if weight_category column exists
        if 'weight_category' not in self.rankings_df.columns:
            # No weight category data - return empty or analyze globally
            return opportunities

        # Analyze each weight category
        weight_categories = self.rankings_df['weight_category'].unique()

        for category in weight_categories:
            category_rankings = self.rankings_df[
                self.rankings_df['weight_category'] == category
            ].copy()

            # Find Saudi athletes in this category
            saudi_in_cat = category_rankings[
                category_rankings['country'].str.upper().str.contains('KSA', na=False)
            ]

            if not saudi_in_cat.empty:
                saudi_in_cat['rank'] = pd.to_numeric(saudi_in_cat['rank'], errors='coerce')
                best_saudi_rank = saudi_in_cat['rank'].min()

                # Medal opportunity if Saudi athlete in top 20
                if best_saudi_rank <= 20:
                    athlete_name = saudi_in_cat[
                        saudi_in_cat['rank'] == best_saudi_rank
                    ]['athlete_name'].iloc[0]

                    # Count competitors in top 8 (medal positions)
                    top8_in_category = len(category_rankings[
                        pd.to_numeric(category_rankings['rank'], errors='coerce') <= 8
                    ])

                    opportunities.append({
                        'weight_category': category,
                        'athlete_name': athlete_name,
                        'current_rank': int(best_saudi_rank),
                        'gap_to_medals': max(0, int(best_saudi_rank) - 8),
                        'top8_competition_level': top8_in_category,
                        'opportunity_score': self._calculate_opportunity_score(
                            best_saudi_rank,
                            top8_in_category
                        )
                    })

        # Sort by opportunity score
        opportunities = sorted(
            opportunities,
            key=lambda x: x['opportunity_score'],
            reverse=True
        )

        return opportunities

    def _load_pdf_extracted_data(self) -> int:
        """
        Load data from PDF extraction (historical competitions)
        Returns number of records loaded
        """
        total_loaded = 0

        # Look for combined CSV files in each category
        for category_dir in self.extracted_data_dir.iterdir():
            if not category_dir.is_dir():
                continue

            # Look for combined CSV files
            combined_files = list(category_dir.glob("*_combined.csv"))

            for csv_file in combined_files:
                try:
                    df = pd.read_csv(csv_file)
                    if not df.empty:
                        # Add source tracking
                        df['source_category'] = category_dir.name
                        df['source_type'] = 'pdf_extraction'

                        # Merge with existing matches if they exist
                        if self.matches_df is not None:
                            self.matches_df = pd.concat([self.matches_df, df], ignore_index=True)
                        else:
                            self.matches_df = df

                        total_loaded += len(df)
                except Exception as e:
                    # Silently skip problematic files
                    continue

        return total_loaded

    def _calculate_opportunity_score(self, rank: float, competition: int) -> float:
        """
        Calculate medal opportunity score (0-100)
        Higher score = better opportunity
        """
        if pd.isna(rank):
            return 0

        # Base score from ranking
        rank_score = max(0, 100 - (rank * 4))  # Rank 1 = 96, Rank 25 = 0

        # Adjust for competition level
        competition_factor = 1.0 - (competition / 20)  # Less competition = better

        score = rank_score * (0.7 + 0.3 * competition_factor)

        return round(min(100, max(0, score)), 1)

    def generate_competition_recommendations(self) -> List[Dict]:
        """
        Recommend which competitions Saudi athletes should prioritize
        Based on ranking points, medal opportunities, and strategic value
        """
        recommendations = []

        # Competition priorities
        priority_competitions = [
            {
                'name': 'Olympic Games Qualifier',
                'level': CompetitionLevel.OLYMPIC_GAMES,
                'priority': 100,
                'reasoning': 'Critical for Olympic qualification',
                'ranking_points': 'Maximum'
            },
            {
                'name': 'World Championships',
                'level': CompetitionLevel.WORLD_CHAMPIONSHIPS,
                'priority': 95,
                'reasoning': 'Highest ranking points and prestige',
                'ranking_points': 'Very High'
            },
            {
                'name': 'Grand Prix Series',
                'level': CompetitionLevel.GRAND_PRIX,
                'priority': 80,
                'reasoning': 'Strong ranking points and international exposure',
                'ranking_points': 'High'
            },
            {
                'name': 'Asian Championships',
                'level': CompetitionLevel.CONTINENTAL,
                'priority': 75,
                'reasoning': 'Regional dominance and ranking points',
                'ranking_points': 'Medium-High'
            },
            {
                'name': 'President\'s Cup',
                'level': CompetitionLevel.PRESIDENT_CUP,
                'priority': 70,
                'reasoning': 'Good ranking points, continental exposure',
                'ranking_points': 'Medium'
            }
        ]

        return priority_competitions

    def export_analysis_report(self, output_file: str = "saudi_taekwondo_analysis.xlsx"):
        """
        Export comprehensive analysis to Excel with multiple sheets
        """
        print(f"\nGenerating analysis report: {output_file}")

        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:

            # Sheet 1: Team Overview
            team_analytics = self.analyze_saudi_team()
            team_df = pd.DataFrame([{
                'Total Active Athletes': team_analytics.total_active_athletes,
                'Athletes in Top 10': team_analytics.athletes_in_top10,
                'Athletes in Top 50': team_analytics.athletes_in_top50,
                'Athletes in Top 100': team_analytics.athletes_in_top100,
                'Gold Medals': team_analytics.total_gold,
                'Silver Medals': team_analytics.total_silver,
                'Bronze Medals': team_analytics.total_bronze,
            }])
            team_df.to_excel(writer, sheet_name='Team Overview', index=False)

            # Sheet 2: Rival Comparison
            rivals_df = self.benchmark_against_rivals()
            if not rivals_df.empty:
                rivals_df.to_excel(writer, sheet_name='Rival Comparison', index=False)

            # Sheet 3: Medal Opportunities
            opportunities = self.identify_medal_opportunities()
            if opportunities:
                opp_df = pd.DataFrame(opportunities)
                opp_df.to_excel(writer, sheet_name='Medal Opportunities', index=False)

            # Sheet 4: Competition Recommendations
            recommendations = self.generate_competition_recommendations()
            rec_df = pd.DataFrame(recommendations)
            rec_df.to_excel(writer, sheet_name='Recommended Competitions', index=False)

            # Sheet 5: Current Rankings
            if self.rankings_df is not None:
                # Handle both 'country' and 'MEMBER NATION' column names
                country_col = 'country' if 'country' in self.rankings_df.columns else 'MEMBER NATION'
                saudi_rankings = self.rankings_df[
                    self.rankings_df[country_col].str.upper().str.contains('KSA', na=False)
                ]
                saudi_rankings.to_excel(writer, sheet_name='Saudi Rankings', index=False)

        print(f"  [OK] Report saved to: {output_file}")


def main():
    """Run sample analysis"""
    analyzer = TaekwondoPerformanceAnalyzer(data_dir="data")

    print("\n" + "="*70)
    print("SAUDI TAEKWONDO PERFORMANCE ANALYSIS")
    print("="*70)

    # Team analysis
    team_analytics = analyzer.analyze_saudi_team()
    print(f"\nTotal Active Athletes: {team_analytics.total_active_athletes}")
    print(f"Athletes in Top 10: {team_analytics.athletes_in_top10}")
    print(f"Athletes in Top 50: {team_analytics.athletes_in_top50}")

    # Rival comparison
    print("\n" + "-"*70)
    print("BENCHMARKING AGAINST RIVALS")
    print("-"*70)
    rivals = analyzer.benchmark_against_rivals()
    print(rivals.to_string())

    # Medal opportunities
    print("\n" + "-"*70)
    print("MEDAL OPPORTUNITIES")
    print("-"*70)
    opportunities = analyzer.identify_medal_opportunities()
    for opp in opportunities[:5]:  # Top 5
        print(f"  {opp['weight_category']}: {opp['athlete_name']} "
              f"(Rank #{opp['current_rank']}, Score: {opp['opportunity_score']})")

    # Export report
    analyzer.export_analysis_report()


if __name__ == "__main__":
    main()
