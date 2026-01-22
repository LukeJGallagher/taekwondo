"""
Coaching Insights Module for Taekwondo Performance Analytics
High-Performance Director and Head Coach focused analytics

Features:
- Squad Overview with readiness indicators
- Training Load Recommendations
- Competition Calendar with ROI analysis
- Athlete Development Pathways
- Performance Trend Analysis
- Weekly/Monthly Executive Summaries

Usage:
    from coaching_insights import CoachingInsights

    insights = CoachingInsights()
    squad = insights.get_squad_overview()
    report = insights.generate_weekly_report()
"""

import sys
import io
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
import json

# UTF-8 encoding for Windows compatibility (skip in Streamlit)
try:
    if sys.platform == 'win32' and hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
except (ValueError, AttributeError):
    pass  # Streamlit environment - stdout already configured

import pandas as pd
import numpy as np

# Local imports
try:
    from config import (
        ASIAN_RIVALS, ASIAN_COUNTRIES, WEIGHT_CATEGORIES,
        ASIAN_GAMES_2026, LA_2028_OLYMPICS, DUAL_TRACK_MILESTONES
    )
except ImportError:
    ASIAN_RIVALS = ['KOR', 'CHN', 'IRI', 'JPN', 'JOR', 'UZB', 'THA', 'KAZ']
    ASIAN_COUNTRIES = []
    WEIGHT_CATEGORIES = {
        'M': ['-54kg', '-58kg', '-63kg', '-68kg', '-74kg', '-80kg', '-87kg', '+87kg'],
        'F': ['-46kg', '-49kg', '-53kg', '-57kg', '-62kg', '-67kg', '-73kg', '+73kg']
    }
    ASIAN_GAMES_2026 = {'start_date': '2026-09-19'}
    LA_2028_OLYMPICS = {'start_date': '2028-07-14'}
    DUAL_TRACK_MILESTONES = []


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class AthleteStatus:
    """Individual athlete status for coaching dashboard."""
    name: str
    weight_category: str
    world_rank: int
    asian_rank: int = 0
    points: float = 0.0

    # Performance indicators
    form_score: int = 50  # 0-100
    form_trend: str = "Stable"  # Improving, Declining, Stable
    recent_results: List[str] = field(default_factory=list)  # ['W', 'L', 'W', ...]

    # Readiness status
    readiness: str = "Ready"  # Ready, Caution, Unavailable
    readiness_notes: str = ""

    # Target tracking
    asian_games_target: bool = False
    olympics_target: bool = False
    qualification_probability: float = 0.0

    # Development
    development_stage: str = "Peak"  # Emerging, Developing, Peak, Experienced
    priority_level: str = "A"  # A, B, C


@dataclass
class CompetitionOpportunity:
    """Competition opportunity analysis for coaching decisions."""
    name: str
    date: str
    location: str
    tier: str  # G1, G2, G4, etc.
    ranking_points: int
    estimated_cost: float

    # Strategic value
    roi_score: float = 0.0
    strategic_value: str = "Medium"  # High, Medium, Low
    recommended_athletes: List[str] = field(default_factory=list)

    # Decision support
    recommendation: str = ""
    risk_factors: List[str] = field(default_factory=list)


@dataclass
class SquadOverview:
    """Complete squad overview for HP Director."""
    generated_date: str
    total_athletes: int
    athletes_by_category: Dict[str, int] = field(default_factory=dict)

    # Readiness summary
    ready_count: int = 0
    caution_count: int = 0
    unavailable_count: int = 0

    # Target tracking
    asian_games_targets: int = 0
    olympics_targets: int = 0

    # Performance summary
    avg_form_score: float = 0.0
    top_performers: List[str] = field(default_factory=list)
    concerns: List[str] = field(default_factory=list)

    # Athletes list
    athletes: List[AthleteStatus] = field(default_factory=list)


@dataclass
class WeeklyReport:
    """Weekly coaching report for HP Director."""
    week_start: str
    week_end: str
    generated_date: str

    # Key metrics
    key_highlights: List[str] = field(default_factory=list)
    concerns: List[str] = field(default_factory=list)

    # Ranking movements
    ranking_changes: List[Dict] = field(default_factory=list)

    # Upcoming focus
    upcoming_competitions: List[str] = field(default_factory=list)
    training_priorities: List[str] = field(default_factory=list)

    # Action items
    action_items: List[str] = field(default_factory=list)


# =============================================================================
# COACHING INSIGHTS ENGINE
# =============================================================================

class CoachingInsights:
    """
    Provides coaching and high-performance director focused analytics.
    """

    def __init__(self, data_dir: str = None):
        """Initialize coaching insights engine."""
        self.data_dir = Path(data_dir) if data_dir else Path('.')
        self.rankings_df = None
        self.matches_df = None

        # Load data
        self._load_data()

        # Calculate days to major events
        self.days_to_asian_games = self._days_to_event(ASIAN_GAMES_2026.get('start_date', '2026-09-19'))
        self.days_to_olympics = self._days_to_event(LA_2028_OLYMPICS.get('start_date', '2028-07-14'))

    def _load_data(self):
        """Load required data files."""
        data_paths = [
            self.data_dir / 'data',
            self.data_dir / 'data_incremental',
            self.data_dir / 'data_all_categories',
        ]

        # Load rankings
        for base_path in data_paths:
            rankings_path = base_path / 'rankings'
            if rankings_path.exists():
                csv_files = sorted(rankings_path.glob('*.csv'), reverse=True)
                if csv_files:
                    try:
                        self.rankings_df = pd.read_csv(csv_files[0])
                        self._normalize_columns()
                        break
                    except Exception as e:
                        continue

        # Load matches
        matches_paths = [
            self.data_dir / 'data' / 'matches' / 'all_matches.csv',
            self.data_dir / 'data' / 'matches' / 'matches.csv',
        ]

        for mp in matches_paths:
            if mp.exists():
                try:
                    self.matches_df = pd.read_csv(mp)
                    break
                except:
                    continue

    def _normalize_columns(self):
        """Normalize column names."""
        if self.rankings_df is None:
            return

        column_map = {
            'RANK': 'rank',
            'MEMBER NATION': 'country',
            'NAME': 'athlete_name',
            'WEIGHT CATEGORY': 'weight_category',
            'POINTS': 'points',
        }

        for old, new in column_map.items():
            if old in self.rankings_df.columns and new not in self.rankings_df.columns:
                self.rankings_df = self.rankings_df.rename(columns={old: new})

    def _days_to_event(self, event_date: str) -> int:
        """Calculate days until event."""
        try:
            event = datetime.strptime(event_date, '%Y-%m-%d')
            return (event - datetime.now()).days
        except:
            return 999

    # =========================================================================
    # SQUAD MANAGEMENT
    # =========================================================================

    def get_squad_overview(self) -> SquadOverview:
        """
        Get complete squad overview for HP Director dashboard.

        Returns:
            SquadOverview with all athlete statuses and metrics
        """
        overview = SquadOverview(
            generated_date=datetime.now().isoformat(),
            total_athletes=0
        )

        if self.rankings_df is None:
            return overview

        # Filter to Saudi athletes
        country_col = 'country' if 'country' in self.rankings_df.columns else 'MEMBER NATION'
        saudi_df = self.rankings_df[
            self.rankings_df[country_col].str.contains('KSA|SAUDI', case=False, na=False)
        ]

        overview.total_athletes = len(saudi_df)

        # Process each athlete
        for _, row in saudi_df.iterrows():
            athlete = self._create_athlete_status(row)
            overview.athletes.append(athlete)

            # Update category counts
            cat = athlete.weight_category
            overview.athletes_by_category[cat] = overview.athletes_by_category.get(cat, 0) + 1

            # Update readiness counts
            if athlete.readiness == "Ready":
                overview.ready_count += 1
            elif athlete.readiness == "Caution":
                overview.caution_count += 1
            else:
                overview.unavailable_count += 1

            # Update target counts
            if athlete.asian_games_target:
                overview.asian_games_targets += 1
            if athlete.olympics_target:
                overview.olympics_targets += 1

        # Calculate averages and summaries
        if overview.athletes:
            overview.avg_form_score = np.mean([a.form_score for a in overview.athletes])

            # Top performers (form > 70)
            top = [a.name for a in overview.athletes if a.form_score >= 70]
            overview.top_performers = top[:5]

            # Concerns (form < 40 or declining)
            concerns = [a.name for a in overview.athletes
                       if a.form_score < 40 or a.form_trend == "Declining"]
            overview.concerns = concerns[:5]

        return overview

    def _create_athlete_status(self, row: pd.Series) -> AthleteStatus:
        """Create athlete status from data row."""
        name_col = 'athlete_name' if 'athlete_name' in row.index else 'NAME'
        rank_col = 'rank' if 'rank' in row.index else 'RANK'
        cat_col = 'weight_category' if 'weight_category' in row.index else 'WEIGHT CATEGORY'
        points_col = 'points' if 'points' in row.index else 'POINTS'

        name = str(row.get(name_col, 'Unknown'))
        world_rank = int(row.get(rank_col, 999)) if pd.notna(row.get(rank_col)) else 999
        category = str(row.get(cat_col, ''))
        points = float(row.get(points_col, 0)) if pd.notna(row.get(points_col)) else 0

        # Calculate form score based on rank
        if world_rank <= 5:
            form_score = 90
        elif world_rank <= 10:
            form_score = 80
        elif world_rank <= 20:
            form_score = 65
        elif world_rank <= 30:
            form_score = 50
        else:
            form_score = 35

        # Determine targets based on rank
        asian_target = world_rank <= 20
        olympic_target = world_rank <= 15

        # Development stage based on rank trajectory (simplified)
        if world_rank <= 10:
            dev_stage = "Peak"
        elif world_rank <= 20:
            dev_stage = "Developing"
        else:
            dev_stage = "Emerging"

        # Priority based on rank and Olympic categories
        olympic_categories = ['-58kg', '-68kg', '-80kg', '+80kg', '-49kg', '-57kg', '-67kg', '+67kg']
        if world_rank <= 10:
            priority = "A"
        elif world_rank <= 20 or any(cat in category for cat in olympic_categories):
            priority = "B"
        else:
            priority = "C"

        return AthleteStatus(
            name=name,
            weight_category=category,
            world_rank=world_rank,
            points=points,
            form_score=form_score,
            form_trend="Stable",  # Would need historical data for trend
            asian_games_target=asian_target,
            olympics_target=olympic_target,
            qualification_probability=max(0, min(1, (30 - world_rank) / 25)),
            development_stage=dev_stage,
            priority_level=priority
        )

    # =========================================================================
    # COMPETITION PLANNING
    # =========================================================================

    def get_competition_opportunities(self, months_ahead: int = 6) -> List[CompetitionOpportunity]:
        """
        Get upcoming competition opportunities with ROI analysis.

        Args:
            months_ahead: How many months ahead to look

        Returns:
            List of CompetitionOpportunity objects
        """
        # Define upcoming competitions (would normally come from scraper)
        competitions = [
            CompetitionOpportunity(
                name="Grand Prix Manchester",
                date="2026-03-15",
                location="UK",
                tier="G4",
                ranking_points=40,
                estimated_cost=8000,
                roi_score=75,
                strategic_value="High",
                recommendation="Attend - Strong ROI for ranking points",
                recommended_athletes=["Priority A athletes"],
                risk_factors=["Travel fatigue", "Strong Korean field"]
            ),
            CompetitionOpportunity(
                name="Asian Championships 2026",
                date="2026-05-01",
                location="TBD",
                tier="Continental",
                ranking_points=50,
                estimated_cost=12000,
                roi_score=95,
                strategic_value="Critical",
                recommendation="MUST ATTEND - Asian Games qualification",
                recommended_athletes=["All Asian Games targets"],
                risk_factors=["Peak preparation timing"]
            ),
            CompetitionOpportunity(
                name="Grand Prix Rome",
                date="2026-06-10",
                location="Italy",
                tier="G4",
                ranking_points=40,
                estimated_cost=9000,
                roi_score=70,
                strategic_value="Medium",
                recommendation="Consider for Olympic track athletes",
                recommended_athletes=["Olympic category athletes"],
                risk_factors=["Close to Asian Games"]
            ),
            CompetitionOpportunity(
                name="Asian Games 2026",
                date="2026-09-19",
                location="Nagoya, Japan",
                tier="Multi-Sport Games",
                ranking_points=100,
                estimated_cost=25000,
                roi_score=100,
                strategic_value="Critical",
                recommendation="PRIMARY TARGET - Full team",
                recommended_athletes=["Qualified athletes"],
                risk_factors=["Peak timing critical", "Japan home advantage"]
            ),
        ]

        # Filter by date
        cutoff = datetime.now() + timedelta(days=months_ahead * 30)
        filtered = []
        for comp in competitions:
            try:
                comp_date = datetime.strptime(comp.date, '%Y-%m-%d')
                if comp_date <= cutoff:
                    filtered.append(comp)
            except:
                filtered.append(comp)

        return filtered

    def generate_competition_calendar(self) -> Dict[str, Any]:
        """
        Generate competition calendar with recommendations.

        Returns:
            Dictionary with calendar data and recommendations
        """
        competitions = self.get_competition_opportunities(months_ahead=12)

        calendar = {
            'generated_date': datetime.now().isoformat(),
            'days_to_asian_games': self.days_to_asian_games,
            'days_to_olympics': self.days_to_olympics,
            'competitions': [],
            'priority_events': [],
            'budget_estimate': 0
        }

        for comp in competitions:
            calendar['competitions'].append({
                'name': comp.name,
                'date': comp.date,
                'tier': comp.tier,
                'roi_score': comp.roi_score,
                'cost': comp.estimated_cost,
                'recommendation': comp.recommendation,
                'strategic_value': comp.strategic_value
            })

            if comp.strategic_value in ['Critical', 'High']:
                calendar['priority_events'].append(comp.name)

            calendar['budget_estimate'] += comp.estimated_cost

        return calendar

    # =========================================================================
    # REPORTING
    # =========================================================================

    def generate_weekly_report(self) -> WeeklyReport:
        """
        Generate weekly executive report for HP Director.

        Returns:
            WeeklyReport with key metrics and action items
        """
        now = datetime.now()
        week_start = (now - timedelta(days=now.weekday())).strftime('%Y-%m-%d')
        week_end = (now + timedelta(days=6-now.weekday())).strftime('%Y-%m-%d')

        report = WeeklyReport(
            week_start=week_start,
            week_end=week_end,
            generated_date=now.isoformat()
        )

        # Get squad overview for metrics
        squad = self.get_squad_overview()

        # Key highlights
        if squad.top_performers:
            report.key_highlights.append(
                f"Top performing athletes: {', '.join(squad.top_performers[:3])}"
            )

        report.key_highlights.append(
            f"Squad readiness: {squad.ready_count}/{squad.total_athletes} athletes competition-ready"
        )

        report.key_highlights.append(
            f"Days to Asian Games 2026: {self.days_to_asian_games}"
        )

        # Concerns
        if squad.concerns:
            report.concerns.append(
                f"Athletes requiring attention: {', '.join(squad.concerns[:3])}"
            )

        if squad.caution_count > 0:
            report.concerns.append(
                f"{squad.caution_count} athlete(s) on caution status"
            )

        # Upcoming competitions
        comps = self.get_competition_opportunities(months_ahead=2)
        report.upcoming_competitions = [f"{c.name} ({c.date})" for c in comps[:3]]

        # Training priorities
        report.training_priorities = [
            "Competition simulation for Asian Games targets",
            "Video analysis of key Asian rivals (KOR, IRI, JPN)",
            "Weight management monitoring for all categories"
        ]

        # Action items
        report.action_items = [
            f"Review qualification status for {squad.asian_games_targets} Asian Games targets",
            "Schedule individual athlete meetings for Olympic pathway athletes",
            "Confirm travel arrangements for upcoming competitions"
        ]

        return report

    def generate_monthly_summary(self) -> Dict[str, Any]:
        """
        Generate monthly executive summary.

        Returns:
            Dictionary with monthly metrics and trends
        """
        squad = self.get_squad_overview()
        calendar = self.generate_competition_calendar()

        summary = {
            'month': datetime.now().strftime('%B %Y'),
            'generated_date': datetime.now().isoformat(),

            # Squad metrics
            'squad_size': squad.total_athletes,
            'readiness_rate': squad.ready_count / squad.total_athletes if squad.total_athletes > 0 else 0,
            'avg_form_score': squad.avg_form_score,

            # Target tracking
            'asian_games_targets': squad.asian_games_targets,
            'olympics_targets': squad.olympics_targets,

            # Key dates
            'days_to_asian_games': self.days_to_asian_games,
            'days_to_olympics': self.days_to_olympics,

            # Financial
            'competition_budget_required': calendar['budget_estimate'],

            # Priorities
            'priority_events': calendar['priority_events'],

            # Recommendations
            'strategic_priorities': [
                "Maximize ranking points before Asian Games qualification deadline",
                "Focus resources on Priority A athletes in Olympic categories",
                "Develop contingency plans for non-qualified categories"
            ]
        }

        return summary

    # =========================================================================
    # ATHLETE DEVELOPMENT
    # =========================================================================

    def get_development_pathways(self) -> Dict[str, List[AthleteStatus]]:
        """
        Categorize athletes by development pathway.

        Returns:
            Dictionary with athletes grouped by development stage
        """
        squad = self.get_squad_overview()

        pathways = {
            'medal_contenders': [],      # Top 10, ready for medals
            'qualification_track': [],    # Top 20, focused on qualifying
            'development_pool': [],       # Top 30, building experience
            'emerging_talent': []         # Beyond 30, long-term development
        }

        for athlete in squad.athletes:
            if athlete.world_rank <= 10:
                pathways['medal_contenders'].append(athlete)
            elif athlete.world_rank <= 20:
                pathways['qualification_track'].append(athlete)
            elif athlete.world_rank <= 30:
                pathways['development_pool'].append(athlete)
            else:
                pathways['emerging_talent'].append(athlete)

        return pathways

    def get_training_recommendations(self, athlete_name: str) -> Dict[str, Any]:
        """
        Get personalized training recommendations for an athlete.

        Args:
            athlete_name: Name of the athlete

        Returns:
            Dictionary with training recommendations
        """
        squad = self.get_squad_overview()

        # Find athlete
        athlete = None
        for a in squad.athletes:
            if athlete_name.lower() in a.name.lower():
                athlete = a
                break

        if not athlete:
            return {'error': 'Athlete not found'}

        recommendations = {
            'athlete': athlete.name,
            'current_rank': athlete.world_rank,
            'development_stage': athlete.development_stage,
            'priority_level': athlete.priority_level,

            'focus_areas': [],
            'competition_strategy': '',
            'technical_priorities': [],
            'physical_priorities': [],
            'mental_priorities': []
        }

        # Recommendations based on rank and stage
        if athlete.world_rank <= 10:
            recommendations['focus_areas'] = [
                "Peak performance maintenance",
                "Tactical refinement against specific opponents",
                "Competition simulation under pressure"
            ]
            recommendations['competition_strategy'] = "Select high-value events strategically"
            recommendations['technical_priorities'] = [
                "Perfect execution of signature techniques",
                "Develop counter-strategies for top 5 rivals"
            ]

        elif athlete.world_rank <= 20:
            recommendations['focus_areas'] = [
                "Consistent ranking points accumulation",
                "Close rate analysis (converting close fights)",
                "Endurance for deep tournament runs"
            ]
            recommendations['competition_strategy'] = "Attend multiple G4 events for points"
            recommendations['technical_priorities'] = [
                "Improve scoring efficiency",
                "Develop reliable opening round strategies"
            ]

        else:
            recommendations['focus_areas'] = [
                "Experience building at international level",
                "Fundamental technique refinement",
                "Physical development"
            ]
            recommendations['competition_strategy'] = "Gain experience at Opens and lower-tier events"
            recommendations['technical_priorities'] = [
                "Build reliable scoring combinations",
                "Improve defensive fundamentals"
            ]

        # Universal mental priorities
        recommendations['mental_priorities'] = [
            "Pre-competition routines",
            "In-match composure",
            "Recovery from setbacks"
        ]

        return recommendations


# =============================================================================
# STREAMLIT INTEGRATION FUNCTIONS
# =============================================================================

def render_squad_card(athlete: AthleteStatus) -> str:
    """Render athlete status as HTML card for Streamlit - Team Saudi Theme."""
    # Team Saudi Brand Colors - Logo Green
    TEAL_PRIMARY = '#1E5631'      # Forest green (logo match)
    GOLD_ACCENT = '#a08e66'
    TEAL_DARK = '#163d24'         # Darker green
    TEAL_LIGHT = '#2D5A3D'        # Lighter green
    GRAY_BLUE = '#78909C'

    # Status colors - Team Saudi palette
    readiness_colors = {
        'Ready': TEAL_PRIMARY,      # Teal for ready
        'Caution': GOLD_ACCENT,     # Gold for caution
        'Unavailable': '#dc3545'    # Red for unavailable
    }

    priority_colors = {
        'A': TEAL_PRIMARY,
        'B': TEAL_LIGHT,
        'C': GRAY_BLUE
    }

    readiness_color = readiness_colors.get(athlete.readiness, GRAY_BLUE)
    priority_color = priority_colors.get(athlete.priority_level, GRAY_BLUE)

    # Form indicator - Team Saudi colors
    if athlete.form_score >= 70:
        form_color = TEAL_PRIMARY
        form_icon = '▲'
    elif athlete.form_score >= 50:
        form_color = GOLD_ACCENT
        form_icon = '●'
    else:
        form_color = '#dc3545'
        form_icon = '▼'

    targets = []
    if athlete.asian_games_target:
        targets.append('🎯 AG2026')
    if athlete.olympics_target:
        targets.append('🏅 LA2028')

    targets_html = ' '.join(targets) if targets else ''

    return f"""
    <div style="border: 1px solid #ddd; border-radius: 10px; padding: 15px; margin: 10px 0; background: white; border-left: 5px solid {priority_color};">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h4 style="margin: 0; color: #333; font-family: 'Inter', sans-serif;">{athlete.name}</h4>
                <p style="margin: 5px 0; color: #666;">{athlete.weight_category} | #{athlete.world_rank} World</p>
            </div>
            <div style="text-align: right;">
                <span style="background: {readiness_color}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 0.8em;">
                    {athlete.readiness}
                </span>
            </div>
        </div>

        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin: 15px 0;">
            <div style="text-align: center; padding: 8px; background: rgba(0, 113, 103, 0.05); border-radius: 6px;">
                <div style="font-size: 1.2em; font-weight: bold; color: {form_color};">{form_icon} {athlete.form_score}</div>
                <div style="font-size: 0.75em; color: #666;">Form</div>
            </div>
            <div style="text-align: center; padding: 8px; background: rgba(0, 113, 103, 0.05); border-radius: 6px;">
                <div style="font-size: 1.2em; font-weight: bold; color: {TEAL_PRIMARY};">{athlete.points:.0f}</div>
                <div style="font-size: 0.75em; color: #666;">Points</div>
            </div>
            <div style="text-align: center; padding: 8px; background: rgba(0, 113, 103, 0.05); border-radius: 6px;">
                <div style="font-size: 1.2em; font-weight: bold; color: {TEAL_PRIMARY};">{athlete.qualification_probability:.0%}</div>
                <div style="font-size: 0.75em; color: #666;">Qual %</div>
            </div>
            <div style="text-align: center; padding: 8px; background: rgba(0, 113, 103, 0.05); border-radius: 6px;">
                <div style="font-size: 1.2em; font-weight: bold; color: {priority_color};">{athlete.priority_level}</div>
                <div style="font-size: 0.75em; color: #666;">Priority</div>
            </div>
        </div>

        <div style="font-size: 0.85em; color: #666;">
            {targets_html} | {athlete.development_stage} | Trend: {athlete.form_trend}
        </div>
    </div>
    """


def render_competition_card(comp: CompetitionOpportunity) -> str:
    """Render competition opportunity as HTML card - Team Saudi Theme."""
    # Team Saudi Brand Colors - Logo Green
    TEAL_PRIMARY = '#1E5631'      # Forest green (logo match)
    GOLD_ACCENT = '#a08e66'
    TEAL_DARK = '#163d24'         # Darker green
    TEAL_LIGHT = '#2D5A3D'        # Lighter green

    # Strategic value colors - Team Saudi palette
    strategic_colors = {
        'Critical': '#dc3545',       # Red for critical
        'High': GOLD_ACCENT,         # Gold for high
        'Medium': TEAL_LIGHT,        # Light teal for medium
        'Low': TEAL_PRIMARY          # Primary teal for low priority
    }

    color = strategic_colors.get(comp.strategic_value, '#78909C')

    return f"""
    <div style="border: 2px solid {color}; border-radius: 10px; padding: 15px; margin: 10px 0; background: white; font-family: 'Inter', sans-serif;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h4 style="margin: 0; color: #333;">{comp.name}</h4>
                <p style="margin: 5px 0; color: #666;">{comp.date} | {comp.location}</p>
            </div>
            <span style="background: {color}; color: white; padding: 5px 10px; border-radius: 15px; font-size: 0.8em;">
                {comp.strategic_value}
            </span>
        </div>

        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin: 15px 0;">
            <div style="text-align: center; padding: 8px; background: rgba(0, 113, 103, 0.08); border-radius: 6px;">
                <div style="font-size: 1.2em; font-weight: bold; color: {TEAL_PRIMARY};">{comp.ranking_points}</div>
                <div style="font-size: 0.75em; color: #666;">Points</div>
            </div>
            <div style="text-align: center; padding: 8px; background: rgba(160, 142, 102, 0.08); border-radius: 6px;">
                <div style="font-size: 1.2em; font-weight: bold; color: {GOLD_ACCENT};">${comp.estimated_cost:,.0f}</div>
                <div style="font-size: 0.75em; color: #666;">Est. Cost</div>
            </div>
            <div style="text-align: center; padding: 8px; background: rgba(0, 113, 103, 0.08); border-radius: 6px;">
                <div style="font-size: 1.2em; font-weight: bold; color: {TEAL_PRIMARY};">{comp.roi_score:.0f}/100</div>
                <div style="font-size: 0.75em; color: #666;">ROI Score</div>
            </div>
        </div>

        <div style="background: rgba(0, 113, 103, 0.05); padding: 10px; border-radius: 6px; margin-top: 10px; border-left: 3px solid {TEAL_PRIMARY};">
            <strong style="color: {TEAL_DARK};">Recommendation:</strong> {comp.recommendation}
        </div>
    </div>
    """


# =============================================================================
# MAIN (CLI Testing)
# =============================================================================

def main():
    """Test the coaching insights module."""
    print("=" * 60)
    print("COACHING INSIGHTS - HP DIRECTOR DASHBOARD")
    print("=" * 60)

    insights = CoachingInsights()

    # Squad overview
    print("\n[SQUAD OVERVIEW]")
    squad = insights.get_squad_overview()
    print(f"  Total Athletes: {squad.total_athletes}")
    print(f"  Ready: {squad.ready_count} | Caution: {squad.caution_count} | Unavailable: {squad.unavailable_count}")
    print(f"  Asian Games Targets: {squad.asian_games_targets}")
    print(f"  Olympics Targets: {squad.olympics_targets}")
    print(f"  Avg Form Score: {squad.avg_form_score:.1f}")

    if squad.top_performers:
        print(f"  Top Performers: {', '.join(squad.top_performers[:3])}")

    # Key dates
    print(f"\n[KEY DATES]")
    print(f"  Days to Asian Games 2026: {insights.days_to_asian_games}")
    print(f"  Days to LA 2028 Olympics: {insights.days_to_olympics}")

    # Competition calendar
    print("\n[UPCOMING COMPETITIONS]")
    comps = insights.get_competition_opportunities(months_ahead=6)
    for comp in comps[:3]:
        print(f"  - {comp.name} ({comp.date})")
        print(f"    {comp.strategic_value} | ROI: {comp.roi_score}/100 | ${comp.estimated_cost:,.0f}")

    # Weekly report
    print("\n[WEEKLY REPORT]")
    report = insights.generate_weekly_report()
    print(f"  Week: {report.week_start} to {report.week_end}")
    print(f"  Highlights:")
    for h in report.key_highlights[:2]:
        print(f"    - {h}")
    print(f"  Action Items:")
    for a in report.action_items[:2]:
        print(f"    - {a}")

    print("\n" + "=" * 60)
    print("Coaching Insights Ready")
    print("=" * 60)


if __name__ == "__main__":
    main()
