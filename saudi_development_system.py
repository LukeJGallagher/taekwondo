"""
Saudi Athlete Development System
=====================================
Strategic planning tool for Saudi Taekwondo athletes targeting:
- Asian Games 2026 (Nagoya, Japan)
- World Championships 2025/2027
- LA 2028 Olympics

Provides pathway analysis, qualification tracking, and competition recommendations.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import json

# Team Saudi Brand Colors
TEAL_PRIMARY = '#007167'
GOLD_ACCENT = '#a08e66'


@dataclass
class SaudiAthlete:
    """Saudi athlete profile with development tracking"""
    name: str
    weight_category: str
    gender: str  # 'M' or 'F'
    current_world_rank: Optional[int] = None
    current_asian_rank: Optional[int] = None
    ranking_points: float = 0.0
    age: Optional[int] = None
    coach: str = ""

    # Profile picture - local path or URL
    profile_photo: str = ""  # Path to local photo or URL
    simplycompete_id: str = ""  # SimplyCompete UUID for profile lookup
    nationality: str = "Saudi Arabia"
    birth_date: str = ""
    height_cm: Optional[int] = None
    weight_kg: Optional[float] = None

    # Performance metrics
    total_fights: int = 0
    wins: int = 0
    losses: int = 0
    win_rate: float = 0.0
    golden_points_won: int = 0
    golden_points_lost: int = 0

    # Competition history
    competitions_2024: int = 0
    competitions_2025: int = 0
    best_result_2024: str = ""
    best_result_2025: str = ""

    # Targets
    target_asian_games: bool = False
    target_worlds_2025: bool = False
    target_la_2028: bool = False

    # Development notes
    strengths: List[str] = field(default_factory=list)
    areas_to_improve: List[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class QualificationPathway:
    """Qualification pathway to major events"""
    event_name: str
    event_date: str
    host_city: str
    qualification_deadline: str

    # Qualification requirements
    min_world_rank: Optional[int] = None
    min_asian_rank: Optional[int] = None
    min_points: Optional[float] = None
    continental_quota: Optional[int] = None

    # How to qualify
    qualification_routes: List[str] = field(default_factory=list)
    key_competitions: List[str] = field(default_factory=list)


class SaudiDevelopmentSystem:
    """Main system for Saudi athlete development tracking"""

    # Weight categories (Olympic format for major games)
    OLYMPIC_CATEGORIES = {
        'M': ['M-58kg', 'M-68kg', 'M-80kg', 'M+80kg'],
        'F': ['F-49kg', 'F-57kg', 'F-67kg', 'F+67kg']
    }

    # All 16 WT categories
    ALL_CATEGORIES = {
        'M': ['M-54kg', 'M-58kg', 'M-63kg', 'M-68kg', 'M-74kg', 'M-80kg', 'M-87kg', 'M+87kg'],
        'F': ['F-46kg', 'F-49kg', 'F-53kg', 'F-57kg', 'F-62kg', 'F-67kg', 'F-73kg', 'F+73kg']
    }

    # Key rival nations for Saudi Arabia in Asia
    ASIAN_RIVALS = [
        'Republic of Korea', 'Korea', 'KOR',
        'Islamic Republic Of Iran', 'Iran', 'IRI',
        "People's Republic Of China", 'China', 'CHN',
        'Japan', 'JPN',
        'Uzbekistan', 'UZB',
        'Jordan', 'JOR',
        'Thailand', 'THA',
        'Chinese Taipei', 'TPE',
        'Kazakhstan', 'KAZ',
        'Vietnam', 'VIE'
    ]

    # Competition points by tier (approximate World Taekwondo ranking points)
    COMPETITION_POINTS = {
        'Olympic Games': {'gold': 120, 'silver': 72, 'bronze': 43.2},
        'World Championships': {'gold': 120, 'silver': 72, 'bronze': 43.2},
        'Grand Prix': {'gold': 40, 'silver': 24, 'bronze': 14.4},
        'Grand Prix Final': {'gold': 60, 'silver': 36, 'bronze': 21.6},
        'Continental Championships': {'gold': 20, 'silver': 12, 'bronze': 7.2},
        'G2 International Open': {'gold': 10, 'silver': 6, 'bronze': 3.6},
        'G1 International Open': {'gold': 4, 'silver': 2.4, 'bronze': 1.44},
    }

    # Major event calendar
    MAJOR_EVENTS = {
        'asian_games_2026': QualificationPathway(
            event_name='Asian Games 2026',
            event_date='September 2026',
            host_city='Nagoya, Japan',
            qualification_deadline='June 2026',
            min_asian_rank=8,  # Approximate - top 8 in Asia have good chance
            continental_quota=1,  # 1 per country per category
            qualification_routes=[
                'Asian Championships qualification',
                'World ranking pathway',
                'Host country invitation'
            ],
            key_competitions=[
                'Asian Championships 2025',
                'Asian Championships 2026',
                'Grand Prix Series 2025-2026',
                'World Championships 2025'
            ]
        ),
        'worlds_2025': QualificationPathway(
            event_name='World Championships 2025',
            event_date='May 2025',
            host_city='Wuxi, China',
            qualification_deadline='April 2025',
            min_world_rank=None,  # Open entry via national federation
            qualification_routes=[
                'National federation entry',
                'World ranking consideration'
            ],
            key_competitions=[
                'Grand Prix Series 2024-2025',
                'Asian Championships 2025'
            ]
        ),
        'worlds_2027': QualificationPathway(
            event_name='World Championships 2027',
            event_date='TBD 2027',
            host_city='TBD',
            qualification_deadline='TBD',
            min_world_rank=None,
            qualification_routes=['National federation entry'],
            key_competitions=['Grand Prix 2026-2027', 'Asian Games 2026']
        ),
        'la_2028': QualificationPathway(
            event_name='LA 2028 Olympics',
            event_date='July-August 2028',
            host_city='Los Angeles, USA',
            qualification_deadline='June 2028',
            min_world_rank=5,  # Top 5 in world ranking qualify directly
            continental_quota=2,  # Asian qualification tournament
            qualification_routes=[
                'World Ranking (Top 5 per category)',
                'Asian Olympic Qualifier (Top 2)',
                'World Olympic Qualifier',
                'Tripartite invitation'
            ],
            key_competitions=[
                'Asian Games 2026',
                'World Championships 2025',
                'World Championships 2027',
                'Grand Prix Series 2026-2028',
                'Asian Olympic Qualifier 2028'
            ]
        )
    }

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.athletes_dir = self.data_dir / "athletes"
        self.athletes_dir.mkdir(parents=True, exist_ok=True)

        self.saudi_athletes: List[SaudiAthlete] = []
        self.rankings_df: Optional[pd.DataFrame] = None

        self.load_data()

    def load_data(self):
        """Load existing data"""
        # Try to load Saudi athletes from JSON
        athletes_file = self.athletes_dir / "saudi_squad.json"
        if athletes_file.exists():
            with open(athletes_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.saudi_athletes = [SaudiAthlete(**a) for a in data.get('athletes', [])]
                print(f"[OK] Loaded {len(self.saudi_athletes)} Saudi athletes")

        # Load world rankings
        rankings_paths = [
            self.data_dir / 'rankings' / 'world_rankings_latest.csv',
            self.data_dir / 'rankings' / 'world_rankings_all_20260121.csv',
            self.data_dir / 'profiles' / 'all_rankings_latest.csv',
        ]

        for path in rankings_paths:
            if path.exists():
                self.rankings_df = pd.read_csv(path)
                print(f"[OK] Loaded rankings from {path}")
                break

    def add_athlete(self, athlete: SaudiAthlete):
        """Add or update a Saudi athlete"""
        # Check if athlete already exists
        existing = [a for a in self.saudi_athletes if a.name == athlete.name]
        if existing:
            # Update existing
            idx = self.saudi_athletes.index(existing[0])
            self.saudi_athletes[idx] = athlete
        else:
            self.saudi_athletes.append(athlete)

        self.save_athletes()
        print(f"[OK] {'Updated' if existing else 'Added'} athlete: {athlete.name}")

    def save_athletes(self):
        """Save Saudi athletes to JSON"""
        data = {
            'last_updated': datetime.now().isoformat(),
            'athletes': [vars(a) for a in self.saudi_athletes]
        }

        with open(self.athletes_dir / 'saudi_squad.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get_category_analysis(self, category: str) -> Dict:
        """Analyze a weight category's competitive landscape"""
        if self.rankings_df is None:
            return {'category': category, 'error': 'No rankings data'}

        # Handle column name variations
        cat_col = 'weight_category' if 'weight_category' in self.rankings_df.columns else 'category'

        if cat_col not in self.rankings_df.columns:
            return {'category': category, 'error': 'No category column in data'}

        cat_df = self.rankings_df[self.rankings_df[cat_col] == category].copy()

        if cat_df.empty:
            return {'category': category, 'athletes': 0, 'message': 'No data for this category'}

        # Sort by rank
        cat_df = cat_df.sort_values('rank')

        # Get Asian rivals
        country_col = 'country' if 'country' in cat_df.columns else 'MEMBER NATION'

        asian_df = cat_df[cat_df[country_col].apply(self._is_asian_rival)].head(10)

        analysis = {
            'category': category,
            'total_ranked': len(cat_df),
            'top_10': cat_df.head(10)[['rank', 'athlete_name', country_col, 'points']].to_dict('records'),
            'asian_top_10': asian_df[['rank', 'athlete_name', country_col, 'points']].to_dict('records') if len(asian_df) > 0 else [],
            'points_for_top_10': float(cat_df.iloc[9]['points']) if len(cat_df) >= 10 else None,
            'points_for_top_20': float(cat_df.iloc[19]['points']) if len(cat_df) >= 20 else None,
            'dominant_nations': cat_df.head(20)[country_col].value_counts().head(5).to_dict(),
        }

        return analysis

    def _is_asian_rival(self, country: str) -> bool:
        """Check if country is an Asian rival"""
        if not country:
            return False
        for rival in self.ASIAN_RIVALS:
            if rival.lower() in country.lower():
                return True
        return False

    def calculate_points_gap(self, athlete: SaudiAthlete, target_rank: int) -> Dict:
        """Calculate points needed to reach target rank"""
        if self.rankings_df is None:
            return {'error': 'No rankings data'}

        cat_col = 'weight_category' if 'weight_category' in self.rankings_df.columns else 'category'

        if cat_col not in self.rankings_df.columns:
            return {'error': 'No category column'}

        cat_df = self.rankings_df[
            self.rankings_df[cat_col] == athlete.weight_category
        ].sort_values('rank')

        if len(cat_df) < target_rank:
            return {
                'current_points': athlete.ranking_points,
                'target_rank': target_rank,
                'target_points': 0,
                'points_gap': 0,
                'message': f'Only {len(cat_df)} athletes ranked in {athlete.weight_category}'
            }

        target_points = float(cat_df.iloc[target_rank - 1]['points'])
        points_gap = max(0, target_points - athlete.ranking_points)

        return {
            'current_points': athlete.ranking_points,
            'current_rank': athlete.current_world_rank,
            'target_rank': target_rank,
            'target_points': target_points,
            'points_gap': points_gap,
            'competitions_needed': self._estimate_competitions_needed(points_gap)
        }

    def _estimate_competitions_needed(self, points_gap: float) -> Dict:
        """Estimate competitions needed to close points gap"""
        estimates = {}

        # Average points per competition tier (assuming bronze)
        for tier, medals in self.COMPETITION_POINTS.items():
            bronze_pts = medals['bronze']
            if bronze_pts > 0:
                comps_needed = int(np.ceil(points_gap / bronze_pts))
                estimates[tier] = {
                    'competitions_for_bronze': comps_needed,
                    'competitions_for_gold': int(np.ceil(points_gap / medals['gold']))
                }

        return estimates

    def recommend_competitions(self, athlete: SaudiAthlete, target_event: str = 'asian_games_2026') -> List[Dict]:
        """Recommend competitions for an athlete to reach their target"""
        recommendations = []

        pathway = self.MAJOR_EVENTS.get(target_event)
        if not pathway:
            return [{'error': f'Unknown target event: {target_event}'}]

        # 2025 Calendar - Key events
        calendar_2025 = [
            {
                'name': 'Asian Taekwondo Championships 2025',
                'date': 'May 2025',
                'location': 'TBD',
                'tier': 'Continental Championships',
                'priority': 'HIGH',
                'reason': 'Asian Games qualifier, continental ranking points'
            },
            {
                'name': 'World Taekwondo Championships 2025',
                'date': 'May 2025',
                'location': 'Wuxi, China',
                'tier': 'World Championships',
                'priority': 'HIGH',
                'reason': 'Maximum ranking points, Olympic pathway'
            },
            {
                'name': 'Grand Prix Series 2025',
                'date': 'Throughout 2025',
                'location': 'Various',
                'tier': 'Grand Prix',
                'priority': 'HIGH',
                'reason': 'Consistent points accumulation, world ranking boost'
            },
            {
                'name': 'President\'s Cup 2025',
                'date': 'Q3-Q4 2025',
                'location': 'Asia Region',
                'tier': 'G2 International Open',
                'priority': 'MEDIUM',
                'reason': 'Regional experience, G2 ranking points'
            },
            {
                'name': 'G1 International Opens',
                'date': 'Throughout 2025',
                'location': 'Various',
                'tier': 'G1 International Open',
                'priority': 'MEDIUM',
                'reason': 'Competition experience, base ranking points'
            }
        ]

        # Filter by category (Olympic vs non-Olympic)
        is_olympic_category = athlete.weight_category in (
            self.OLYMPIC_CATEGORIES['M'] + self.OLYMPIC_CATEGORIES['F']
        )

        for comp in calendar_2025:
            rec = comp.copy()
            rec['potential_points'] = self.COMPETITION_POINTS.get(comp['tier'], {})
            rec['olympic_category'] = is_olympic_category

            if is_olympic_category and target_event == 'la_2028':
                rec['la_2028_relevance'] = 'Critical for Olympic pathway'

            recommendations.append(rec)

        return recommendations

    def generate_development_plan(self, athlete: SaudiAthlete) -> Dict:
        """Generate comprehensive development plan for an athlete"""
        plan = {
            'athlete': athlete.name,
            'category': athlete.weight_category,
            'generated_at': datetime.now().isoformat(),
            'targets': {},
            'current_status': {},
            'pathway_analysis': {},
            'competition_calendar': {},
            'training_focus': [],
        }

        # Current status
        plan['current_status'] = {
            'world_rank': athlete.current_world_rank or 'Unranked',
            'asian_rank': athlete.current_asian_rank or 'Unranked',
            'ranking_points': athlete.ranking_points,
            'win_rate': f"{athlete.win_rate:.1f}%" if athlete.win_rate else 'N/A',
            'total_fights': athlete.total_fights,
        }

        # Target analysis
        if athlete.target_asian_games:
            plan['targets']['asian_games_2026'] = {
                'event': 'Asian Games 2026 - Nagoya',
                'date': 'September 2026',
                'qualification_status': self._assess_qualification_status(athlete, 'asian_games_2026'),
                'points_gap': self.calculate_points_gap(athlete, 8),  # Top 8 in Asia
                'recommended_competitions': self.recommend_competitions(athlete, 'asian_games_2026')
            }

        if athlete.target_la_2028:
            plan['targets']['la_2028'] = {
                'event': 'LA 2028 Olympics',
                'date': 'July-August 2028',
                'qualification_routes': self.MAJOR_EVENTS['la_2028'].qualification_routes,
                'points_gap_top_5': self.calculate_points_gap(athlete, 5),
                'points_gap_top_20': self.calculate_points_gap(athlete, 20),
                'recommended_competitions': self.recommend_competitions(athlete, 'la_2028')
            }

        if athlete.target_worlds_2025:
            plan['targets']['worlds_2025'] = {
                'event': 'World Championships 2025 - Wuxi',
                'date': 'May 2025',
                'qualification_status': 'Open via national federation',
                'preparation_competitions': self.recommend_competitions(athlete, 'worlds_2025')
            }

        # Category competitive analysis
        plan['pathway_analysis']['category_landscape'] = self.get_category_analysis(athlete.weight_category)

        # Training focus recommendations based on stats
        if athlete.win_rate < 60:
            plan['training_focus'].append({
                'area': 'Match Winning Ability',
                'priority': 'HIGH',
                'current': f"{athlete.win_rate:.0f}% win rate",
                'target': '70%+ win rate',
                'recommendation': 'Focus on tactical game plans, match simulations'
            })

        if athlete.golden_points_lost > athlete.golden_points_won:
            plan['training_focus'].append({
                'area': 'Golden Point Situations',
                'priority': 'HIGH',
                'current': f"Won {athlete.golden_points_won}, Lost {athlete.golden_points_lost}",
                'target': 'Positive GP ratio',
                'recommendation': 'Clutch situation drills, mental conditioning'
            })

        plan['training_focus'].append({
            'area': 'Ranking Points Accumulation',
            'priority': 'HIGH',
            'current': f"{athlete.ranking_points} points",
            'target': 'Top 20 World Ranking',
            'recommendation': 'Strategic competition selection, consistent podium finishes'
        })

        return plan

    def _assess_qualification_status(self, athlete: SaudiAthlete, event: str) -> str:
        """Assess current qualification status for an event"""
        pathway = self.MAJOR_EVENTS.get(event)
        if not pathway:
            return 'Unknown event'

        if event == 'asian_games_2026':
            if athlete.current_asian_rank and athlete.current_asian_rank <= 3:
                return 'Strong Position - Medal Contender'
            elif athlete.current_asian_rank and athlete.current_asian_rank <= 8:
                return 'Qualification Possible - On Track'
            elif athlete.current_asian_rank and athlete.current_asian_rank <= 15:
                return 'Development Phase - Points Needed'
            else:
                return 'Building Phase - Significant Points Required'

        if event == 'la_2028':
            if athlete.current_world_rank and athlete.current_world_rank <= 5:
                return 'On Track for Direct Qualification'
            elif athlete.current_world_rank and athlete.current_world_rank <= 20:
                return 'Asian Qualifier Route - Good Position'
            else:
                return 'Development Phase - Long-term Build Required'

        return 'Assessment pending'

    def get_squad_summary(self) -> Dict:
        """Get summary of entire Saudi squad"""
        if not self.saudi_athletes:
            return {
                'total_athletes': 0,
                'message': 'No Saudi athletes registered. Use add_sample_squad() to add sample data.'
            }

        summary = {
            'total_athletes': len(self.saudi_athletes),
            'by_gender': {'M': 0, 'F': 0},
            'by_category': {},
            'targets': {
                'asian_games_2026': 0,
                'worlds_2025': 0,
                'la_2028': 0
            },
            'ranked_athletes': [],
            'development_athletes': [],
        }

        for athlete in self.saudi_athletes:
            summary['by_gender'][athlete.gender] += 1
            summary['by_category'][athlete.weight_category] = summary['by_category'].get(athlete.weight_category, 0) + 1

            if athlete.target_asian_games:
                summary['targets']['asian_games_2026'] += 1
            if athlete.target_worlds_2025:
                summary['targets']['worlds_2025'] += 1
            if athlete.target_la_2028:
                summary['targets']['la_2028'] += 1

            if athlete.current_world_rank and athlete.current_world_rank <= 50:
                summary['ranked_athletes'].append({
                    'name': athlete.name,
                    'category': athlete.weight_category,
                    'world_rank': athlete.current_world_rank,
                    'asian_rank': athlete.current_asian_rank,
                    'points': athlete.ranking_points
                })
            else:
                summary['development_athletes'].append({
                    'name': athlete.name,
                    'category': athlete.weight_category,
                    'points': athlete.ranking_points
                })

        return summary

    def add_sample_squad(self):
        """Add sample Saudi squad for demonstration"""
        # Note: These are sample athletes for demonstration
        # Replace with actual Saudi athlete data when available

        sample_athletes = [
            SaudiAthlete(
                name="Ahmed Al-Mutairi",
                weight_category="M-68kg",
                gender="M",
                current_world_rank=45,
                current_asian_rank=12,
                ranking_points=65.5,
                age=24,
                coach="Coach Kim",
                profile_photo="",  # Add URL when available
                simplycompete_id="",  # Add ID when scraped
                height_cm=178,
                weight_kg=68.0,
                total_fights=42,
                wins=28,
                losses=14,
                win_rate=66.7,
                golden_points_won=3,
                golden_points_lost=2,
                competitions_2024=6,
                best_result_2024="Bronze - Asian Open",
                target_asian_games=True,
                target_worlds_2025=True,
                target_la_2028=True,
                strengths=["Fast combination kicks", "Good stamina", "Strong mental game"],
                areas_to_improve=["Head kicks", "Defensive clinch"],
                notes="Primary focus athlete for Asian Games 2026"
            ),
            SaudiAthlete(
                name="Faisal Al-Rashid",
                weight_category="M-80kg",
                gender="M",
                current_world_rank=72,
                current_asian_rank=18,
                ranking_points=42.3,
                age=22,
                coach="Coach Park",
                total_fights=35,
                wins=22,
                losses=13,
                win_rate=62.9,
                golden_points_won=2,
                golden_points_lost=3,
                competitions_2024=5,
                best_result_2024="5th Place - President's Cup",
                target_asian_games=True,
                target_la_2028=True,
                strengths=["Power kicks", "Counter-attacks"],
                areas_to_improve=["Footwork", "Golden point situations"],
                notes="Development phase - potential for 2028"
            ),
            SaudiAthlete(
                name="Khalid Al-Dossary",
                weight_category="M-58kg",
                gender="M",
                current_world_rank=None,
                current_asian_rank=25,
                ranking_points=28.5,
                age=20,
                coach="Coach Lee",
                total_fights=22,
                wins=14,
                losses=8,
                win_rate=63.6,
                golden_points_won=1,
                golden_points_lost=2,
                competitions_2024=4,
                best_result_2024="Bronze - GCC Championships",
                target_asian_games=True,
                target_worlds_2025=True,
                strengths=["Speed", "Agility"],
                areas_to_improve=["Experience at senior level", "Power"],
                notes="Rising talent - needs more international experience"
            ),
            SaudiAthlete(
                name="Omar Al-Qahtani",
                weight_category="M+80kg",
                gender="M",
                current_world_rank=88,
                current_asian_rank=22,
                ranking_points=35.8,
                age=26,
                coach="Coach Kim",
                total_fights=48,
                wins=30,
                losses=18,
                win_rate=62.5,
                golden_points_won=4,
                golden_points_lost=5,
                competitions_2024=7,
                best_result_2024="Silver - Arab Championships",
                target_asian_games=True,
                target_la_2028=True,
                strengths=["Physical presence", "Experience"],
                areas_to_improve=["Mobility", "Technical variety"],
                notes="Experienced heavyweight - Asian Games focus"
            ),
            SaudiAthlete(
                name="Noura Al-Saud",
                weight_category="F-57kg",
                gender="F",
                current_world_rank=55,
                current_asian_rank=14,
                ranking_points=52.1,
                age=23,
                coach="Coach Chen",
                total_fights=38,
                wins=26,
                losses=12,
                win_rate=68.4,
                golden_points_won=3,
                golden_points_lost=1,
                competitions_2024=6,
                best_result_2024="Silver - Asian Open",
                target_asian_games=True,
                target_worlds_2025=True,
                target_la_2028=True,
                strengths=["Technical precision", "Tactical awareness", "Excellent GP record"],
                areas_to_improve=["Physical conditioning", "Heavy opponent tactics"],
                notes="Leading female athlete - strong Olympic potential"
            ),
            SaudiAthlete(
                name="Maha Al-Farsi",
                weight_category="F-67kg",
                gender="F",
                current_world_rank=None,
                current_asian_rank=28,
                ranking_points=24.3,
                age=21,
                coach="Coach Park",
                total_fights=18,
                wins=11,
                losses=7,
                win_rate=61.1,
                golden_points_won=1,
                golden_points_lost=2,
                competitions_2024=4,
                best_result_2024="5th - GCC Championships",
                target_asian_games=True,
                target_worlds_2025=True,
                strengths=["Height advantage", "Long-range kicks"],
                areas_to_improve=["Close-range fighting", "Competition experience"],
                notes="Development athlete - building toward 2028"
            ),
        ]

        for athlete in sample_athletes:
            self.add_athlete(athlete)

        print(f"\n[OK] Added {len(sample_athletes)} sample Saudi athletes")
        print("    Use system.get_squad_summary() to view squad overview")
        print("    Use system.generate_development_plan(athlete) for individual plans")

    def export_squad_report(self, output_path: str = None) -> str:
        """Export comprehensive squad report to JSON"""
        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = self.athletes_dir / f'squad_report_{timestamp}.json'

        report = {
            'generated_at': datetime.now().isoformat(),
            'squad_summary': self.get_squad_summary(),
            'athlete_plans': [],
            'event_pathways': {
                'asian_games_2026': vars(self.MAJOR_EVENTS['asian_games_2026']),
                'la_2028': vars(self.MAJOR_EVENTS['la_2028']),
            }
        }

        for athlete in self.saudi_athletes:
            plan = self.generate_development_plan(athlete)
            report['athlete_plans'].append(plan)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)

        print(f"[OK] Squad report exported to {output_path}")
        return str(output_path)


def main():
    """Main function - demonstrate the Saudi Development System"""
    print("="*70)
    print("SAUDI TAEKWONDO DEVELOPMENT SYSTEM")
    print("Targeting: Asian Games 2026 | World Championships | LA 2028 Olympics")
    print("="*70)

    system = SaudiDevelopmentSystem()

    # Check if we have athletes
    summary = system.get_squad_summary()

    if summary['total_athletes'] == 0:
        print("\n[INFO] No Saudi athletes registered yet.")
        print("[INFO] Adding sample squad for demonstration...\n")
        system.add_sample_squad()
        summary = system.get_squad_summary()

    # Display squad summary
    print("\n" + "="*70)
    print("SQUAD SUMMARY")
    print("="*70)
    print(f"Total Athletes: {summary['total_athletes']}")
    print(f"  Men: {summary['by_gender']['M']} | Women: {summary['by_gender']['F']}")
    print(f"\nCategories Covered:")
    for cat, count in summary['by_category'].items():
        print(f"  {cat}: {count} athlete(s)")

    print(f"\nTarget Events:")
    print(f"  Asian Games 2026: {summary['targets']['asian_games_2026']} athletes")
    print(f"  World Championships 2025: {summary['targets']['worlds_2025']} athletes")
    print(f"  LA 2028 Olympics: {summary['targets']['la_2028']} athletes")

    # Show ranked athletes
    if summary['ranked_athletes']:
        print("\n" + "-"*50)
        print("RANKED ATHLETES (World Top 50)")
        print("-"*50)
        for a in sorted(summary['ranked_athletes'], key=lambda x: x['world_rank'] or 999):
            print(f"  #{a['world_rank']:3d} World | #{a['asian_rank']:2d} Asia | {a['name']} ({a['category']}) - {a['points']:.1f} pts")

    # Generate development plan for top athlete
    if system.saudi_athletes:
        top_athlete = sorted(
            system.saudi_athletes,
            key=lambda x: x.ranking_points,
            reverse=True
        )[0]

        print("\n" + "="*70)
        print(f"DEVELOPMENT PLAN: {top_athlete.name}")
        print("="*70)

        plan = system.generate_development_plan(top_athlete)

        print(f"\nCategory: {plan['category']}")
        print(f"Current Status:")
        for k, v in plan['current_status'].items():
            print(f"  {k}: {v}")

        if 'asian_games_2026' in plan['targets']:
            ag = plan['targets']['asian_games_2026']
            print(f"\n--- ASIAN GAMES 2026 ---")
            print(f"Qualification Status: {ag['qualification_status']}")
            if 'points_gap' in ag:
                pg = ag['points_gap']
                print(f"Current Points: {pg.get('current_points', 0)}")
                print(f"Points Gap to Top 8: {pg.get('points_gap', 'N/A')}")

        if 'la_2028' in plan['targets']:
            la = plan['targets']['la_2028']
            print(f"\n--- LA 2028 OLYMPICS ---")
            print(f"Qualification Routes:")
            for route in la.get('qualification_routes', []):
                print(f"  - {route}")

        if plan['training_focus']:
            print(f"\n--- TRAINING PRIORITIES ---")
            for focus in plan['training_focus']:
                print(f"  [{focus['priority']}] {focus['area']}")
                print(f"       Current: {focus['current']}")
                print(f"       Target: {focus['target']}")

    # Export report
    print("\n" + "="*70)
    report_path = system.export_squad_report()
    print("="*70)

    return system


if __name__ == '__main__':
    main()
