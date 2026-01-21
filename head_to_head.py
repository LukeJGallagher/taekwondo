"""
Head-to-Head Analysis Module
Analyze historical matchups between athletes
Critical for match strategy and scouting
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from collections import defaultdict


class HeadToHeadAnalyzer:
    """
    Analyze historical head-to-head records between athletes
    Identify patterns, nemesis opponents, and favorable matchups
    """

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.matches_df = None
        self.athletes_df = None
        self._load_data()

    def _load_data(self):
        """Load match and athlete data"""
        # Load match data
        match_files = list((self.data_dir / "matches").glob("*.csv"))
        if match_files:
            self.matches_df = pd.concat([pd.read_csv(f) for f in match_files])
            print(f"Loaded {len(self.matches_df)} matches")

        # Load athlete data
        athlete_files = list((self.data_dir / "athletes").glob("*.csv"))
        if athlete_files:
            self.athletes_df = pd.read_csv(athlete_files[0])
            print(f"Loaded {len(self.athletes_df)} athletes")

    def analyze_matchup(self, athlete1_name: str, athlete2_name: str) -> Dict:
        """
        Analyze head-to-head record between two specific athletes

        Args:
            athlete1_name: First athlete name
            athlete2_name: Second athlete name

        Returns:
            Dictionary with detailed matchup analysis
        """
        if self.matches_df is None or self.matches_df.empty:
            return {'error': 'No match data available'}

        # Find all matches between these two athletes
        matches = self.matches_df[
            ((self.matches_df['athlete1_name'].str.contains(athlete1_name, case=False, na=False)) &
             (self.matches_df['athlete2_name'].str.contains(athlete2_name, case=False, na=False))) |
            ((self.matches_df['athlete1_name'].str.contains(athlete2_name, case=False, na=False)) &
             (self.matches_df['athlete2_name'].str.contains(athlete1_name, case=False, na=False)))
        ].copy()

        if matches.empty:
            return {
                'total_matches': 0,
                'message': 'No previous encounters found'
            }

        # Calculate wins for athlete1
        athlete1_wins = len(matches[matches['winner_name'].str.contains(athlete1_name, case=False, na=False)])
        athlete2_wins = len(matches) - athlete1_wins

        # Sort by date (most recent first)
        if 'date' in matches.columns:
            matches['date'] = pd.to_datetime(matches['date'], errors='coerce')
            matches = matches.sort_values('date', ascending=False)

        # Last 5 matches
        last_5_results = []
        for _, match in matches.head(5).iterrows():
            if athlete1_name.lower() in str(match.get('winner_name', '')).lower():
                last_5_results.append('W')
            else:
                last_5_results.append('L')

        # Calculate average point differential (if available)
        point_diff = None
        if 'athlete1_total' in matches.columns and 'athlete2_total' in matches.columns:
            for _, match in matches.iterrows():
                # Determine which athlete is athlete1 in this match
                if athlete1_name.lower() in str(match.get('athlete1_name', '')).lower():
                    diff = match['athlete1_total'] - match['athlete2_total']
                else:
                    diff = match['athlete2_total'] - match['athlete1_total']

                if point_diff is None:
                    point_diff = []
                point_diff.append(diff)

        avg_point_diff = np.mean(point_diff) if point_diff else None

        # Determine trend (recent form)
        trend = "N/A"
        if len(last_5_results) >= 3:
            recent_wins = last_5_results[:3].count('W')
            if recent_wins >= 2:
                trend = "Improving"
            elif recent_wins <= 1:
                trend = "Declining"
            else:
                trend = "Stable"

        return {
            'athlete1': athlete1_name,
            'athlete2': athlete2_name,
            'total_matches': len(matches),
            'athlete1_wins': athlete1_wins,
            'athlete2_wins': athlete2_wins,
            'win_rate': round((athlete1_wins / len(matches)) * 100, 1) if len(matches) > 0 else 0,
            'last_5_matches': last_5_results,
            'last_5_record': f"{last_5_results.count('W')}-{last_5_results.count('L')}",
            'avg_point_differential': round(avg_point_diff, 1) if avg_point_diff else None,
            'trend': trend,
            'last_encounter': matches.iloc[0]['date'].strftime('%Y-%m-%d') if not matches.empty and 'date' in matches.columns else None,
            'oldest_encounter': matches.iloc[-1]['date'].strftime('%Y-%m-%d') if not matches.empty and 'date' in matches.columns else None
        }

    def find_nemesis_opponents(self, athlete_name: str, min_matches: int = 3) -> List[Dict]:
        """
        Find opponents that consistently beat this athlete (nemesis opponents)

        Args:
            athlete_name: Athlete to analyze
            min_matches: Minimum matches to consider (default 3)

        Returns:
            List of nemesis opponents sorted by dominance
        """
        if self.matches_df is None or self.matches_df.empty:
            return []

        # Find all matches involving this athlete
        athlete_matches = self.matches_df[
            (self.matches_df['athlete1_name'].str.contains(athlete_name, case=False, na=False)) |
            (self.matches_df['athlete2_name'].str.contains(athlete_name, case=False, na=False))
        ]

        # Group by opponent
        opponents = defaultdict(lambda: {'wins': 0, 'losses': 0})

        for _, match in athlete_matches.iterrows():
            # Determine opponent
            if athlete_name.lower() in str(match.get('athlete1_name', '')).lower():
                opponent = match.get('athlete2_name', '')
                is_win = athlete_name.lower() in str(match.get('winner_name', '')).lower()
            else:
                opponent = match.get('athlete1_name', '')
                is_win = athlete_name.lower() in str(match.get('winner_name', '')).lower()

            if is_win:
                opponents[opponent]['wins'] += 1
            else:
                opponents[opponent]['losses'] += 1

        # Filter for nemesis (more losses than wins, minimum matches)
        nemesis_list = []
        for opponent, record in opponents.items():
            total_matches = record['wins'] + record['losses']

            if total_matches >= min_matches and record['losses'] > record['wins']:
                nemesis_list.append({
                    'opponent': opponent,
                    'wins': record['wins'],
                    'losses': record['losses'],
                    'total_matches': total_matches,
                    'win_rate': round((record['wins'] / total_matches) * 100, 1),
                    'dominance_score': record['losses'] - record['wins']  # How dominant they are
                })

        # Sort by dominance (most dominant first)
        nemesis_list.sort(key=lambda x: x['dominance_score'], reverse=True)

        return nemesis_list

    def find_favorable_matchups(self, athlete_name: str, min_matches: int = 3, min_win_rate: float = 60.0) -> List[Dict]:
        """
        Find opponents this athlete consistently beats (favorable matchups)

        Args:
            athlete_name: Athlete to analyze
            min_matches: Minimum matches to consider
            min_win_rate: Minimum win rate % to qualify

        Returns:
            List of favorable opponents
        """
        if self.matches_df is None or self.matches_df.empty:
            return []

        # Find all matches
        athlete_matches = self.matches_df[
            (self.matches_df['athlete1_name'].str.contains(athlete_name, case=False, na=False)) |
            (self.matches_df['athlete2_name'].str.contains(athlete_name, case=False, na=False))
        ]

        # Group by opponent
        opponents = defaultdict(lambda: {'wins': 0, 'losses': 0})

        for _, match in athlete_matches.iterrows():
            if athlete_name.lower() in str(match.get('athlete1_name', '')).lower():
                opponent = match.get('athlete2_name', '')
                is_win = athlete_name.lower() in str(match.get('winner_name', '')).lower()
            else:
                opponent = match.get('athlete1_name', '')
                is_win = athlete_name.lower() in str(match.get('winner_name', '')).lower()

            if is_win:
                opponents[opponent]['wins'] += 1
            else:
                opponents[opponent]['losses'] += 1

        # Filter for favorable (high win rate, minimum matches)
        favorable_list = []
        for opponent, record in opponents.items():
            total_matches = record['wins'] + record['losses']
            win_rate = (record['wins'] / total_matches) * 100 if total_matches > 0 else 0

            if total_matches >= min_matches and win_rate >= min_win_rate:
                favorable_list.append({
                    'opponent': opponent,
                    'wins': record['wins'],
                    'losses': record['losses'],
                    'total_matches': total_matches,
                    'win_rate': round(win_rate, 1),
                    'consistency_score': record['wins']  # More wins = more consistent
                })

        # Sort by win rate (highest first)
        favorable_list.sort(key=lambda x: x['win_rate'], reverse=True)

        return favorable_list

    def build_matchup_matrix(self, athletes: List[str]) -> pd.DataFrame:
        """
        Build head-to-head matrix for multiple athletes

        Args:
            athletes: List of athlete names

        Returns:
            DataFrame with win rates (row vs column)
        """
        matrix = pd.DataFrame(index=athletes, columns=athletes, dtype=float)

        for athlete1 in athletes:
            for athlete2 in athletes:
                if athlete1 == athlete2:
                    matrix.loc[athlete1, athlete2] = None  # Can't play yourself
                else:
                    h2h = self.analyze_matchup(athlete1, athlete2)
                    matrix.loc[athlete1, athlete2] = h2h.get('win_rate', 0)

        return matrix

    def get_common_opponents(self, athlete1_name: str, athlete2_name: str) -> List[Dict]:
        """
        Find common opponents and compare performance

        Args:
            athlete1_name: First athlete
            athlete2_name: Second athlete

        Returns:
            List of common opponents with comparison
        """
        if self.matches_df is None:
            return []

        # Get all opponents for athlete1
        athlete1_matches = self.matches_df[
            (self.matches_df['athlete1_name'].str.contains(athlete1_name, case=False, na=False)) |
            (self.matches_df['athlete2_name'].str.contains(athlete1_name, case=False, na=False))
        ]

        athlete1_opponents = set()
        for _, match in athlete1_matches.iterrows():
            if athlete1_name.lower() in str(match.get('athlete1_name', '')).lower():
                athlete1_opponents.add(match.get('athlete2_name', ''))
            else:
                athlete1_opponents.add(match.get('athlete1_name', ''))

        # Get all opponents for athlete2
        athlete2_matches = self.matches_df[
            (self.matches_df['athlete1_name'].str.contains(athlete2_name, case=False, na=False)) |
            (self.matches_df['athlete2_name'].str.contains(athlete2_name, case=False, na=False))
        ]

        athlete2_opponents = set()
        for _, match in athlete2_matches.iterrows():
            if athlete2_name.lower() in str(match.get('athlete1_name', '')).lower():
                athlete2_opponents.add(match.get('athlete2_name', ''))
            else:
                athlete2_opponents.add(match.get('athlete1_name', ''))

        # Find common opponents
        common = athlete1_opponents.intersection(athlete2_opponents)

        results = []
        for opponent in common:
            h2h_athlete1 = self.analyze_matchup(athlete1_name, opponent)
            h2h_athlete2 = self.analyze_matchup(athlete2_name, opponent)

            results.append({
                'opponent': opponent,
                'athlete1_record': f"{h2h_athlete1['athlete1_wins']}-{h2h_athlete1['athlete2_wins']}",
                'athlete1_win_rate': h2h_athlete1['win_rate'],
                'athlete2_record': f"{h2h_athlete2['athlete1_wins']}-{h2h_athlete2['athlete2_wins']}",
                'athlete2_win_rate': h2h_athlete2['win_rate'],
                'advantage': athlete1_name if h2h_athlete1['win_rate'] > h2h_athlete2['win_rate'] else athlete2_name
            })

        # Sort by difference in win rates
        results.sort(key=lambda x: abs(x['athlete1_win_rate'] - x['athlete2_win_rate']), reverse=True)

        return results

    def generate_scouting_report(self, saudi_athlete: str, opponent: str) -> Dict:
        """
        Generate comprehensive scouting report for upcoming match

        Args:
            saudi_athlete: Saudi athlete name
            opponent: Opponent name

        Returns:
            Detailed scouting report
        """
        h2h = self.analyze_matchup(saudi_athlete, opponent)

        report = {
            'saudi_athlete': saudi_athlete,
            'opponent': opponent,
            'report_date': datetime.now().strftime('%Y-%m-%d'),
            'head_to_head': h2h,
            'recommendation': '',
            'key_insights': []
        }

        # Generate insights
        if h2h['total_matches'] == 0:
            report['key_insights'].append("No previous encounters - unknown matchup")
            report['recommendation'] = "Study opponent video and consult with athletes who have faced them"

        elif h2h['win_rate'] >= 60:
            report['key_insights'].append(f"Favorable matchup - {h2h['win_rate']}% win rate")
            report['recommendation'] = "Continue proven strategy. Confidence is high."

        elif h2h['win_rate'] <= 40:
            report['key_insights'].append(f"Difficult matchup - only {h2h['win_rate']}% win rate")
            report['recommendation'] = "Study recent losses. May need tactical adjustment."

        else:
            report['key_insights'].append("Evenly matched opponents")
            report['recommendation'] = "Small details will matter. Focus on execution."

        # Trend analysis
        if h2h['trend'] == "Improving":
            report['key_insights'].append("Recent trend is POSITIVE - momentum on our side")
        elif h2h['trend'] == "Declining":
            report['key_insights'].append("Recent trend is NEGATIVE - need to reverse momentum")

        # Point differential
        if h2h.get('avg_point_differential'):
            diff = h2h['avg_point_differential']
            if diff > 3:
                report['key_insights'].append(f"Typically win by strong margin (+{diff:.1f} points avg)")
            elif diff < -3:
                report['key_insights'].append(f"Typically lose by significant margin ({diff:.1f} points avg)")

        return report

    def export_scouting_report_pdf(self, saudi_athlete: str, opponent: str, output_file: str):
        """Export scouting report as PDF (future enhancement)"""
        # Would use reportlab or similar
        report = self.generate_scouting_report(saudi_athlete, opponent)
        print(f"Scouting report for {saudi_athlete} vs {opponent}:")
        print(f"  Head-to-head record: {report['head_to_head']['athlete1_wins']}-{report['head_to_head']['athlete2_wins']}")
        print(f"  Recommendation: {report['recommendation']}")


# Example usage
if __name__ == "__main__":
    analyzer = HeadToHeadAnalyzer(data_dir="data")

    # Example 1: Analyze specific matchup
    print("\n" + "="*70)
    print("HEAD-TO-HEAD ANALYSIS")
    print("="*70)

    # h2h = analyzer.analyze_matchup("Ahmed Ali", "John Smith")
    # print(f"\nAhmed Ali vs John Smith:")
    # print(f"  Total matches: {h2h['total_matches']}")
    # print(f"  Win rate: {h2h['win_rate']}%")
    # print(f"  Last 5: {h2h['last_5_record']}")

    # Example 2: Find nemesis opponents
    # print("\n" + "="*70)
    # print("NEMESIS OPPONENTS (Athletes we struggle against)")
    # print("="*70)

    # nemesis = analyzer.find_nemesis_opponents("Ahmed Ali")
    # for i, opp in enumerate(nemesis[:5], 1):
    #     print(f"\n{i}. {opp['opponent']}")
    #     print(f"   Record: {opp['wins']}-{opp['losses']} (Win rate: {opp['win_rate']}%)")

    # Example 3: Find favorable matchups
    # print("\n" + "="*70)
    # print("FAVORABLE MATCHUPS (Athletes we consistently beat)")
    # print("="*70)

    # favorable = analyzer.find_favorable_matchups("Ahmed Ali")
    # for i, opp in enumerate(favorable[:5], 1):
    #     print(f"\n{i}. {opp['opponent']}")
    #     print(f"   Record: {opp['wins']}-{opp['losses']} (Win rate: {opp['win_rate']}%)")

    print("\nHead-to-head analysis module ready!")
    print("Note: Sample data needed for full functionality")
