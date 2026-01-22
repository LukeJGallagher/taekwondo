"""
Asian Games 2026 Analysis Module
Processes scraped data to generate strategic insights for Saudi Taekwondo team
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import json

# Team Saudi Brand Colors
TEAL_PRIMARY = '#1E5631'
GOLD_ACCENT = '#a08e66'


class AsianGamesAnalyzer:
    """Analyze rankings data for Asian Games 2026 strategic planning"""

    # Asian Games participating countries
    ASIAN_COUNTRIES = [
        'Republic of Korea', 'Korea', 'KOR',
        'Islamic Republic Of Iran', 'Iran', 'IRI',
        "People's Republic Of China", 'China', 'CHN',
        'Japan', 'JPN',
        'Uzbekistan', 'UZB',
        'Kazakhstan', 'KAZ',
        'Thailand', 'THA',
        'Viet Nam', 'Vietnam', 'VIE',
        'India', 'IND',
        'Chinese Taipei', 'Taiwan', 'TPE',
        'Jordan', 'JOR',
        'Saudi Arabia', 'KSA',
        'United Arab Emirates', 'UAE',
        'Kuwait', 'KUW',
        'Qatar', 'QAT',
        'Bahrain', 'BRN',
        'Malaysia', 'MAS',
        'Indonesia', 'INA',
        'Philippines', 'PHI',
        'Mongolia', 'MGL',
        'Hong Kong', 'HKG',
        'Singapore', 'SGP',
        'Pakistan', 'PAK',
        'Iraq', 'IRQ',
        'Nepal', 'NEP',
        'Afghanistan', 'AFG',
    ]

    # Olympic weight categories for Asian Games
    OLYMPIC_CATEGORIES = {
        'M': ['M-58kg', 'M-68kg', 'M-80kg', 'M+80kg'],  # Men's Olympic
        'F': ['F-49kg', 'F-57kg', 'F-67kg', 'F+67kg'],  # Women's Olympic
    }

    # All 16 weight categories
    ALL_CATEGORIES = {
        'M': ['M-54kg', 'M-58kg', 'M-63kg', 'M-68kg', 'M-74kg', 'M-80kg', 'M-87kg', 'M+87kg'],
        'F': ['F-46kg', 'F-49kg', 'F-53kg', 'F-57kg', 'F-62kg', 'F-67kg', 'F-73kg', 'F+73kg'],
    }

    def __init__(self, data_dir: str = "data/profiles"):
        self.data_dir = Path(data_dir)
        self.rankings_df = None
        self.asian_df = None
        self.saudi_df = None
        self.load_data()

    def load_data(self):
        """Load scraped data files"""
        # Try multiple possible locations
        possible_paths = [
            self.data_dir / 'all_rankings_latest.csv',
            Path('data/profiles/all_rankings_latest.csv'),
            Path('data/rankings/world_rankings_latest.csv'),
        ]

        for path in possible_paths:
            if path.exists():
                self.rankings_df = pd.read_csv(path)
                print(f"[OK] Loaded rankings from {path}")
                break

        if self.rankings_df is None:
            print("[WARN] No rankings data found")
            return

        # Filter for Asian countries
        self.asian_df = self.rankings_df[
            self.rankings_df['country'].apply(self._is_asian_country)
        ].copy()

        # Extract Saudi athletes
        self.saudi_df = self.rankings_df[
            self.rankings_df['country'].str.contains('KSA|Saudi', case=False, na=False)
        ].copy()

        print(f"[OK] Total athletes: {len(self.rankings_df)}")
        print(f"[OK] Asian athletes: {len(self.asian_df)}")
        print(f"[OK] Saudi athletes: {len(self.saudi_df)}")

    def _is_asian_country(self, country: str) -> bool:
        """Check if country is Asian Games participant"""
        if not country:
            return False
        country_lower = country.lower()
        for asian in self.ASIAN_COUNTRIES:
            if asian.lower() in country_lower:
                return True
        return False

    def get_category_analysis(self, category: str) -> dict:
        """Analyze a specific weight category for Asian Games"""
        if self.asian_df is None:
            return {}

        cat_df = self.asian_df[self.asian_df['weight_category'] == category].copy()

        if cat_df.empty:
            return {'category': category, 'athletes': 0}

        # Sort by rank
        cat_df = cat_df.sort_values('rank')

        # Medal contenders (top 8 Asian)
        medal_zone = cat_df.head(8)

        # Saudi position
        saudi_in_cat = cat_df[cat_df['country'].str.contains('KSA|Saudi', case=False, na=False)]

        analysis = {
            'category': category,
            'total_asian_athletes': len(cat_df),
            'countries_represented': cat_df['country'].nunique(),
            'medal_contenders': medal_zone[['rank', 'athlete_name', 'country', 'points']].to_dict('records'),
            'top_country': cat_df.iloc[0]['country'] if len(cat_df) > 0 else None,
            'top_athlete': cat_df.iloc[0]['athlete_name'] if len(cat_df) > 0 else None,
            'top_points': float(cat_df.iloc[0]['points']) if len(cat_df) > 0 else 0,
            'saudi_athletes': saudi_in_cat[['rank', 'athlete_name', 'points']].to_dict('records') if len(saudi_in_cat) > 0 else [],
            'saudi_best_rank': int(saudi_in_cat['rank'].min()) if len(saudi_in_cat) > 0 else None,
            'points_to_medal': None,
        }

        # Calculate points gap to medal zone
        if len(saudi_in_cat) > 0 and len(medal_zone) >= 3:
            saudi_points = saudi_in_cat['points'].max()
            bronze_points = medal_zone.iloc[2]['points'] if len(medal_zone) > 2 else medal_zone.iloc[-1]['points']
            analysis['points_to_medal'] = float(bronze_points - saudi_points)

        return analysis

    def get_country_strength_matrix(self) -> pd.DataFrame:
        """Generate country strength matrix for Asian Games"""
        if self.asian_df is None:
            return pd.DataFrame()

        # Count athletes per country per category
        matrix = self.asian_df.pivot_table(
            index='country',
            columns='weight_category',
            values='rank',
            aggfunc='count',
            fill_value=0
        )

        # Add total column
        matrix['Total'] = matrix.sum(axis=1)

        # Sort by total
        matrix = matrix.sort_values('Total', ascending=False)

        return matrix

    def get_medal_probability_by_category(self) -> list:
        """Calculate Saudi medal probability per category"""
        results = []

        all_categories = self.ALL_CATEGORIES['M'] + self.ALL_CATEGORIES['F']

        for category in all_categories:
            analysis = self.get_category_analysis(category)

            if not analysis.get('saudi_athletes'):
                probability = 0
                status = 'No Entry'
            else:
                saudi_rank = analysis.get('saudi_best_rank', 999)
                asian_athletes = analysis.get('total_asian_athletes', 0)

                # Simple probability based on Asian ranking
                if saudi_rank <= 3:
                    probability = 80
                    status = 'Medal Favorite'
                elif saudi_rank <= 5:
                    probability = 60
                    status = 'Strong Contender'
                elif saudi_rank <= 8:
                    probability = 40
                    status = 'Medal Possible'
                elif saudi_rank <= 15:
                    probability = 20
                    status = 'Outside Shot'
                else:
                    probability = 5
                    status = 'Development'

            results.append({
                'category': category,
                'gender': 'M' if category.startswith('M') else 'F',
                'saudi_rank_asian': analysis.get('saudi_best_rank'),
                'total_asian': analysis.get('total_asian_athletes', 0),
                'medal_probability': probability,
                'status': status,
                'points_gap': analysis.get('points_to_medal'),
                'top_rival': analysis.get('top_athlete'),
                'top_rival_country': analysis.get('top_country'),
            })

        return results

    def get_rival_analysis(self, country_filter: list = None) -> pd.DataFrame:
        """Analyze key rival countries"""
        if self.asian_df is None:
            return pd.DataFrame()

        if country_filter is None:
            # Top Asian taekwondo nations
            country_filter = ['Korea', 'Iran', 'China', 'Jordan', 'Uzbekistan', 'Thailand']

        rival_data = []

        for rival_term in country_filter:
            rival_df = self.asian_df[
                self.asian_df['country'].str.contains(rival_term, case=False, na=False)
            ]

            if rival_df.empty:
                continue

            # Count by category
            by_category = rival_df.groupby('weight_category').agg({
                'rank': ['min', 'count'],
                'points': 'max'
            }).reset_index()

            by_category.columns = ['category', 'best_rank', 'athlete_count', 'top_points']

            # Medal threats (rank <= 5 in Asian rankings)
            medal_threats = (rival_df['rank'] <= 5).sum()

            rival_data.append({
                'country': rival_term,
                'total_athletes': len(rival_df),
                'categories_covered': rival_df['weight_category'].nunique(),
                'medal_threats': medal_threats,
                'best_global_rank': rival_df['rank'].min(),
                'avg_rank': rival_df['rank'].mean(),
            })

        return pd.DataFrame(rival_data).sort_values('medal_threats', ascending=False)

    def get_head_to_head_matchups(self, saudi_athlete: str = None) -> list:
        """Get likely head-to-head matchups for Saudi athletes"""
        if self.saudi_df is None or self.saudi_df.empty:
            return []

        matchups = []

        for _, saudi in self.saudi_df.iterrows():
            category = saudi['weight_category']
            saudi_rank = saudi['rank']

            # Get Asian rivals in same category
            rivals = self.asian_df[
                (self.asian_df['weight_category'] == category) &
                (~self.asian_df['country'].str.contains('Saudi', case=False, na=False))
            ].sort_values('rank')

            # Likely opponents (within 10 ranks)
            likely_opponents = rivals[
                (rivals['rank'] >= saudi_rank - 10) &
                (rivals['rank'] <= saudi_rank + 10)
            ].head(5)

            matchups.append({
                'saudi_athlete': saudi['athlete_name'],
                'category': category,
                'saudi_rank': int(saudi_rank),
                'saudi_points': float(saudi['points']),
                'likely_opponents': likely_opponents[['athlete_name', 'country', 'rank', 'points']].to_dict('records')
            })

        return matchups

    def generate_full_report(self) -> dict:
        """Generate comprehensive Asian Games analysis report"""
        report = {
            'generated_at': datetime.now().isoformat(),
            'data_summary': {
                'total_athletes': len(self.rankings_df) if self.rankings_df is not None else 0,
                'asian_athletes': len(self.asian_df) if self.asian_df is not None else 0,
                'saudi_athletes': len(self.saudi_df) if self.saudi_df is not None else 0,
                'categories': self.rankings_df['weight_category'].nunique() if self.rankings_df is not None else 0,
            },
            'medal_probabilities': self.get_medal_probability_by_category(),
            'rival_analysis': self.get_rival_analysis().to_dict('records') if self.asian_df is not None else [],
            'saudi_matchups': self.get_head_to_head_matchups(),
            'category_breakdown': {},
        }

        # Add category-by-category analysis
        all_cats = self.ALL_CATEGORIES['M'] + self.ALL_CATEGORIES['F']
        for cat in all_cats:
            report['category_breakdown'][cat] = self.get_category_analysis(cat)

        return report

    def save_report(self, output_path: str = None):
        """Save analysis report to JSON"""
        if output_path is None:
            output_path = self.data_dir / 'asian_games_analysis.json'

        report = self.generate_full_report()

        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        print(f"[OK] Report saved to {output_path}")
        return report


def main():
    """Run Asian Games analysis"""
    print("="*60)
    print("ASIAN GAMES 2026 ANALYSIS")
    print("="*60)

    analyzer = AsianGamesAnalyzer()

    if analyzer.rankings_df is None:
        print("\n[ERROR] No data available for analysis")
        print("Run the GitHub Actions scrapers first:")
        print("  1. Weekly Rankings Scraper")
        print("  2. Athlete Profile Scraper")
        return

    # Generate report
    report = analyzer.save_report()

    # Print summary
    print("\n" + "="*60)
    print("ANALYSIS SUMMARY")
    print("="*60)

    print(f"\nData: {report['data_summary']['asian_athletes']} Asian athletes across {report['data_summary']['categories']} categories")

    print("\n--- MEDAL PROBABILITY BY CATEGORY ---")
    for prob in report['medal_probabilities']:
        if prob['saudi_rank_asian']:
            print(f"  {prob['category']}: {prob['status']} (Rank #{prob['saudi_rank_asian']} in Asia, {prob['medal_probability']}% chance)")

    print("\n--- RIVAL COUNTRY STRENGTH ---")
    for rival in report['rival_analysis'][:6]:
        print(f"  {rival['country']}: {rival['total_athletes']} athletes, {rival['medal_threats']} medal threats")

    print("\n--- SAUDI MATCHUPS ---")
    for matchup in report['saudi_matchups']:
        print(f"\n  {matchup['saudi_athlete']} ({matchup['category']}) - Rank #{matchup['saudi_rank']}")
        for opp in matchup['likely_opponents'][:3]:
            print(f"    vs {opp['athlete_name']} ({opp['country']}) - Rank #{opp['rank']}")


if __name__ == '__main__':
    main()
