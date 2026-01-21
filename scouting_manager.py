"""
Tactical Scouting Manager for Taekwondo Performance Analytics
Provides opponent profiling, head-to-head analysis, and tactical recommendations.

Features:
- Opponent profile cards with strengths/weaknesses
- Head-to-head history between athletes
- Style analysis (offensive/defensive/counter)
- Competition encounter predictions
- Scouting report generation

Usage:
    from scouting_manager import ScoutingManager

    scout = ScoutingManager()
    profile = scout.get_opponent_profile('KOR-1234')
    h2h = scout.head_to_head('KSA-0001', 'KOR-1234')
    report = scout.generate_scouting_report('KSA-0001', category='-68kg')
"""

import os
import sys
import io
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from enum import Enum

# UTF-8 encoding for Windows compatibility
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import pandas as pd
import numpy as np

# Local imports
try:
    from config import RIVAL_COUNTRIES, ASIAN_RIVALS, WEIGHT_CATEGORIES
except ImportError:
    RIVAL_COUNTRIES = ['KOR', 'IRI', 'JOR', 'TUR', 'CHN', 'GBR', 'FRA', 'MEX', 'UAE', 'THA']
    ASIAN_RIVALS = ['KOR', 'CHN', 'IRI', 'JPN', 'JOR', 'UZB', 'THA', 'KAZ', 'TPE', 'VIE']
    WEIGHT_CATEGORIES = {
        'M': ['-54kg', '-58kg', '-63kg', '-68kg', '-74kg', '-80kg', '-87kg', '+87kg'],
        'F': ['-46kg', '-49kg', '-53kg', '-57kg', '-62kg', '-67kg', '-73kg', '+73kg']
    }


# =============================================================================
# DATA CLASSES
# =============================================================================

class FightingStyle(Enum):
    """Classification of fighting styles in Taekwondo."""
    OFFENSIVE = "Offensive"      # High volume, initiates attacks
    DEFENSIVE = "Defensive"      # Counter-focused, patient
    COUNTER = "Counter"          # Waits for opponent mistakes
    BALANCED = "Balanced"        # Mix of styles
    UNKNOWN = "Unknown"


class ThreatLevel(Enum):
    """Threat classification for opponents."""
    CRITICAL = "Critical"        # Top 5, direct medal threat
    HIGH = "High"                # Top 10, likely to face
    MEDIUM = "Medium"            # Top 20, possible encounter
    LOW = "Low"                  # Below top 20
    UNKNOWN = "Unknown"


@dataclass
class MatchRecord:
    """Record of a single match."""
    date: str
    competition: str
    opponent_name: str
    opponent_country: str
    result: str  # 'W', 'L', 'D'
    score: str   # e.g., "12-8"
    round_stage: str  # "Final", "Semi", "Quarter", "R16", etc.
    points_scored: int = 0
    points_conceded: int = 0

    def __post_init__(self):
        # Parse score if not already parsed
        if self.score and '-' in self.score and self.points_scored == 0:
            try:
                parts = self.score.split('-')
                self.points_scored = int(parts[0].strip())
                self.points_conceded = int(parts[1].strip())
            except (ValueError, IndexError):
                pass


@dataclass
class OpponentProfile:
    """Comprehensive profile of an opponent."""
    athlete_id: str
    name: str
    country: str
    country_code: str
    weight_category: str

    # Rankings
    world_rank: int = 0
    asian_rank: int = 0  # If Asian athlete
    olympic_rank: int = 0

    # Performance stats
    total_matches: int = 0
    wins: int = 0
    losses: int = 0
    win_rate: float = 0.0

    # Points analysis
    avg_points_scored: float = 0.0
    avg_points_conceded: float = 0.0
    point_differential: float = 0.0

    # Style analysis
    fighting_style: FightingStyle = FightingStyle.UNKNOWN
    style_confidence: float = 0.0

    # Strengths and weaknesses
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)

    # Recent form (last 6 months)
    recent_form: List[str] = field(default_factory=list)  # ['W', 'W', 'L', ...]
    form_trend: str = "Stable"  # "Improving", "Declining", "Stable"

    # Threat assessment
    threat_level: ThreatLevel = ThreatLevel.UNKNOWN

    # Head-to-head vs KSA
    h2h_vs_ksa: Dict[str, Any] = field(default_factory=dict)

    # Key competitions
    major_results: List[Dict] = field(default_factory=list)

    # Last updated
    last_updated: str = ""

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        data = asdict(self)
        data['fighting_style'] = self.fighting_style.value
        data['threat_level'] = self.threat_level.value
        return data


@dataclass
class HeadToHeadRecord:
    """Head-to-head record between two athletes."""
    athlete1_id: str
    athlete1_name: str
    athlete2_id: str
    athlete2_name: str

    total_meetings: int = 0
    athlete1_wins: int = 0
    athlete2_wins: int = 0
    draws: int = 0

    # Points summary
    athlete1_total_points: int = 0
    athlete2_total_points: int = 0

    # Match history
    matches: List[MatchRecord] = field(default_factory=list)

    # Analysis
    dominant_athlete: str = ""
    win_rate_athlete1: float = 0.0
    recent_winner: str = ""  # Who won most recently

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        data = asdict(self)
        data['matches'] = [asdict(m) for m in self.matches]
        return data


@dataclass
class ScoutingReport:
    """Complete scouting report for an athlete's upcoming competition."""
    athlete_id: str
    athlete_name: str
    weight_category: str
    competition: str
    generated_date: str

    # Likely opponents
    likely_opponents: List[OpponentProfile] = field(default_factory=list)

    # Draw analysis
    draw_analysis: Dict[str, Any] = field(default_factory=dict)

    # Tactical recommendations
    recommendations: List[str] = field(default_factory=list)

    # Key threats
    key_threats: List[str] = field(default_factory=list)

    # Medal probability
    medal_probability: float = 0.0
    gold_probability: float = 0.0

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        data = asdict(self)
        data['likely_opponents'] = [op.to_dict() for op in self.likely_opponents]
        return data


# =============================================================================
# SCOUTING MANAGER
# =============================================================================

class ScoutingManager:
    """
    Manages tactical scouting and opponent analysis.
    """

    def __init__(self, data_dir: str = None):
        """
        Initialize the scouting manager.

        Args:
            data_dir: Base directory for data files
        """
        self.data_dir = Path(data_dir) if data_dir else Path('.')
        self.rankings_df = None
        self.matches_df = None
        self.athletes_df = None

        # Cache for profiles
        self._profile_cache: Dict[str, OpponentProfile] = {}

        # Load data
        self._load_data()

    def _load_data(self):
        """Load all required data files."""
        # Try multiple data locations
        data_paths = [
            self.data_dir / 'data',
            self.data_dir / 'data_incremental',
            self.data_dir / 'data_all_categories',
            self.data_dir / 'data_wt_detailed',
        ]

        # Load rankings
        for base_path in data_paths:
            rankings_path = base_path / 'rankings'
            if rankings_path.exists():
                csv_files = sorted(rankings_path.glob('*.csv'), reverse=True)
                if csv_files:
                    try:
                        self.rankings_df = pd.read_csv(csv_files[0])
                        self._normalize_rankings_columns()
                        # Logging handled silently for Streamlit compatibility
                        break
                    except Exception as e:
                        pass  # Silent fail for Streamlit compatibility

        # Load matches
        matches_paths = [
            self.data_dir / 'data' / 'matches' / 'all_matches.csv',
            self.data_dir / 'data' / 'matches' / 'matches.csv',
        ]

        for mp in matches_paths:
            if mp.exists():
                try:
                    self.matches_df = pd.read_csv(mp)
                    self._normalize_matches_columns()
                    break
                except Exception as e:
                    pass  # Silent fail for Streamlit compatibility

        # If no consolidated matches, try to load from detailed competition files
        if self.matches_df is None or self.matches_df.empty:
            self._load_detailed_matches()

        # Load athletes
        athletes_paths = [
            self.data_dir / 'data' / 'athletes' / 'athletes_from_rankings.csv',
            self.data_dir / 'data' / 'athletes' / 'athletes.csv',
        ]

        for ap in athletes_paths:
            if ap.exists():
                try:
                    self.athletes_df = pd.read_csv(ap)
                    break
                except Exception as e:
                    pass  # Silent fail for Streamlit compatibility

    def _load_detailed_matches(self):
        """Load matches from individual competition result files."""
        detailed_dir = self.data_dir / 'data_wt_detailed'
        if not detailed_dir.exists():
            return

        all_matches = []
        result_files = list(detailed_dir.glob('*results*.csv'))

        for rf in result_files[:50]:  # Limit to first 50 files
            try:
                df = pd.read_csv(rf)
                # Extract competition name from filename
                comp_name = rf.stem.replace('_results_table_0', '').replace('_', ' ')
                df['competition'] = comp_name
                df['source_file'] = rf.name
                all_matches.append(df)
            except Exception as e:
                continue

        if all_matches:
            self.matches_df = pd.concat(all_matches, ignore_index=True)
            self._normalize_matches_columns()

    def _normalize_rankings_columns(self):
        """Normalize column names in rankings DataFrame."""
        if self.rankings_df is None:
            return

        column_map = {
            'RANK': 'rank',
            'MEMBER NATION': 'country',
            'NAME': 'athlete_name',
            'WEIGHT CATEGORY': 'weight_category',
            'POINTS': 'points',
            'GAL ID': 'athlete_id',
        }

        for old_name, new_name in column_map.items():
            if old_name in self.rankings_df.columns and new_name not in self.rankings_df.columns:
                self.rankings_df = self.rankings_df.rename(columns={old_name: new_name})

        # Handle long column names (concatenated weight categories)
        for col in self.rankings_df.columns:
            if len(col) > 50 and 'kg' in col.lower():
                # This is likely a concatenated column, try to extract weight category
                if '-54kg' in col or '+87kg' in col:
                    self.rankings_df = self.rankings_df.rename(columns={col: 'weight_category'})
                    break

    def _normalize_matches_columns(self):
        """Normalize column names in matches DataFrame."""
        if self.matches_df is None:
            return

        column_map = {
            'ATHLETE 1': 'athlete1_name',
            'ATHLETE 2': 'athlete2_name',
            'COUNTRY 1': 'country1',
            'COUNTRY 2': 'country2',
            'SCORE': 'score',
            'WINNER': 'winner',
            'ROUND': 'round_stage',
            'WEIGHT': 'weight_category',
            'COMPETITION': 'competition',
            'DATE': 'date',
        }

        for old_name, new_name in column_map.items():
            if old_name in self.matches_df.columns and new_name not in self.matches_df.columns:
                self.matches_df = self.matches_df.rename(columns={old_name: new_name})

    # =========================================================================
    # OPPONENT PROFILING
    # =========================================================================

    def get_opponent_profile(self, athlete_id: str = None,
                            athlete_name: str = None,
                            country: str = None) -> Optional[OpponentProfile]:
        """
        Get comprehensive profile for an opponent.

        Args:
            athlete_id: Unique athlete identifier (e.g., 'KOR-1234')
            athlete_name: Athlete name (fallback if no ID)
            country: Country code to help disambiguate

        Returns:
            OpponentProfile or None if not found
        """
        # Check cache first
        cache_key = athlete_id or f"{athlete_name}_{country}"
        if cache_key in self._profile_cache:
            return self._profile_cache[cache_key]

        # Find athlete in rankings
        athlete_data = self._find_athlete(athlete_id, athlete_name, country)
        if athlete_data is None:
            return None

        # Build profile
        profile = OpponentProfile(
            athlete_id=athlete_data.get('athlete_id', athlete_id or ''),
            name=athlete_data.get('athlete_name', athlete_name or ''),
            country=athlete_data.get('country', country or ''),
            country_code=self._get_country_code(athlete_data.get('country', '')),
            weight_category=athlete_data.get('weight_category', ''),
            world_rank=int(athlete_data.get('rank', 0)) if pd.notna(athlete_data.get('rank')) else 0,
            last_updated=datetime.now().isoformat()
        )

        # Calculate Asian rank if applicable
        if profile.country_code in ASIAN_RIVALS or profile.country_code in ['KSA']:
            profile.asian_rank = self._calculate_asian_rank(profile)

        # Get match statistics
        self._populate_match_stats(profile)

        # Analyze fighting style
        self._analyze_fighting_style(profile)

        # Identify strengths and weaknesses
        self._identify_strengths_weaknesses(profile)

        # Assess threat level
        self._assess_threat_level(profile)

        # Get recent form
        self._analyze_recent_form(profile)

        # Get major results
        self._get_major_results(profile)

        # Cache the profile
        self._profile_cache[cache_key] = profile

        return profile

    def _find_athlete(self, athlete_id: str = None,
                     athlete_name: str = None,
                     country: str = None) -> Optional[Dict]:
        """Find athlete in available data."""
        if self.rankings_df is None or self.rankings_df.empty:
            return None

        df = self.rankings_df.copy()

        # Search by ID
        if athlete_id and 'athlete_id' in df.columns:
            matches = df[df['athlete_id'] == athlete_id]
            if not matches.empty:
                return matches.iloc[0].to_dict()

        # Search by name
        if athlete_name:
            name_col = 'athlete_name' if 'athlete_name' in df.columns else 'NAME'
            if name_col in df.columns:
                matches = df[df[name_col].str.contains(athlete_name, case=False, na=False)]

                # Filter by country if provided
                if not matches.empty and country:
                    country_col = 'country' if 'country' in df.columns else 'MEMBER NATION'
                    if country_col in matches.columns:
                        country_matches = matches[
                            matches[country_col].str.contains(country, case=False, na=False)
                        ]
                        if not country_matches.empty:
                            return country_matches.iloc[0].to_dict()

                if not matches.empty:
                    return matches.iloc[0].to_dict()

        return None

    def _get_country_code(self, country: str) -> str:
        """Extract 3-letter country code from country string."""
        if not country:
            return ''

        # Common patterns: "Korea (KOR)", "KOR", "Korea"
        country = str(country).upper()

        # Check if already a code
        if len(country) == 3:
            return country

        # Extract from parentheses
        if '(' in country and ')' in country:
            start = country.find('(') + 1
            end = country.find(')')
            return country[start:end]

        # Common country name mappings
        country_codes = {
            'KOREA': 'KOR', 'SOUTH KOREA': 'KOR',
            'IRAN': 'IRI',
            'SAUDI ARABIA': 'KSA', 'SAUDI': 'KSA',
            'CHINA': 'CHN',
            'JAPAN': 'JPN',
            'JORDAN': 'JOR',
            'TURKEY': 'TUR',
            'GREAT BRITAIN': 'GBR', 'UK': 'GBR',
            'FRANCE': 'FRA',
            'MEXICO': 'MEX',
            'UAE': 'UAE', 'UNITED ARAB EMIRATES': 'UAE',
            'THAILAND': 'THA',
            'UZBEKISTAN': 'UZB',
            'KAZAKHSTAN': 'KAZ',
            'CHINESE TAIPEI': 'TPE', 'TAIWAN': 'TPE',
            'VIETNAM': 'VIE',
        }

        for name, code in country_codes.items():
            if name in country:
                return code

        return country[:3] if len(country) >= 3 else country

    def _calculate_asian_rank(self, profile: OpponentProfile) -> int:
        """Calculate Asian rank from world rankings."""
        if self.rankings_df is None or profile.weight_category == '':
            return 0

        df = self.rankings_df.copy()

        # Filter to same weight category
        cat_col = 'weight_category' if 'weight_category' in df.columns else 'WEIGHT CATEGORY'
        if cat_col in df.columns:
            df = df[df[cat_col].str.contains(profile.weight_category.replace('+', r'\+'), case=False, na=False)]

        # Filter to Asian countries
        country_col = 'country' if 'country' in df.columns else 'MEMBER NATION'
        asian_countries_pattern = '|'.join(ASIAN_RIVALS + ['KSA'])
        asian_df = df[df[country_col].str.contains(asian_countries_pattern, case=False, na=False)]

        if asian_df.empty:
            return 0

        # Sort by world rank and find position
        rank_col = 'rank' if 'rank' in asian_df.columns else 'RANK'
        asian_df = asian_df.sort_values(rank_col)

        name_col = 'athlete_name' if 'athlete_name' in asian_df.columns else 'NAME'
        for idx, (_, row) in enumerate(asian_df.iterrows(), 1):
            if profile.name.upper() in str(row[name_col]).upper():
                return idx

        return 0

    def _populate_match_stats(self, profile: OpponentProfile):
        """Populate match statistics for the profile."""
        if self.matches_df is None or self.matches_df.empty:
            return

        df = self.matches_df.copy()

        # Find matches involving this athlete
        name_pattern = profile.name.upper()

        # Check for athlete in either position
        athlete1_col = next((c for c in df.columns if 'athlete1' in c.lower() or 'athlete_1' in c.lower()), None)
        athlete2_col = next((c for c in df.columns if 'athlete2' in c.lower() or 'athlete_2' in c.lower()), None)

        if not athlete1_col or not athlete2_col:
            return

        athlete_matches = df[
            (df[athlete1_col].str.upper().str.contains(name_pattern, na=False)) |
            (df[athlete2_col].str.upper().str.contains(name_pattern, na=False))
        ]

        profile.total_matches = len(athlete_matches)

        if profile.total_matches == 0:
            return

        # Calculate wins/losses
        winner_col = next((c for c in df.columns if 'winner' in c.lower()), None)
        if winner_col:
            wins = athlete_matches[
                athlete_matches[winner_col].str.upper().str.contains(name_pattern, na=False)
            ]
            profile.wins = len(wins)
            profile.losses = profile.total_matches - profile.wins
            profile.win_rate = profile.wins / profile.total_matches if profile.total_matches > 0 else 0.0

        # Calculate points averages (if score data available)
        score_col = next((c for c in df.columns if 'score' in c.lower()), None)
        if score_col:
            points_scored = []
            points_conceded = []

            for _, row in athlete_matches.iterrows():
                score = str(row.get(score_col, ''))
                if '-' in score:
                    try:
                        parts = score.split('-')
                        p1 = int(parts[0].strip())
                        p2 = int(parts[1].strip())

                        # Determine which side the athlete was on
                        if name_pattern in str(row.get(athlete1_col, '')).upper():
                            points_scored.append(p1)
                            points_conceded.append(p2)
                        else:
                            points_scored.append(p2)
                            points_conceded.append(p1)
                    except (ValueError, IndexError):
                        continue

            if points_scored:
                profile.avg_points_scored = np.mean(points_scored)
                profile.avg_points_conceded = np.mean(points_conceded)
                profile.point_differential = profile.avg_points_scored - profile.avg_points_conceded

    def _analyze_fighting_style(self, profile: OpponentProfile):
        """Analyze and classify fighting style."""
        # Based on available stats, classify style
        if profile.avg_points_scored == 0:
            profile.fighting_style = FightingStyle.UNKNOWN
            profile.style_confidence = 0.0
            return

        # High scoring + positive differential = Offensive
        # Low scoring + positive differential = Defensive/Counter
        # High scoring + negative differential = Aggressive but vulnerable

        if profile.avg_points_scored > 10:
            if profile.point_differential > 2:
                profile.fighting_style = FightingStyle.OFFENSIVE
                profile.style_confidence = 0.7
            else:
                profile.fighting_style = FightingStyle.BALANCED
                profile.style_confidence = 0.5
        elif profile.avg_points_scored < 6:
            if profile.point_differential > 0:
                profile.fighting_style = FightingStyle.COUNTER
                profile.style_confidence = 0.6
            else:
                profile.fighting_style = FightingStyle.DEFENSIVE
                profile.style_confidence = 0.5
        else:
            profile.fighting_style = FightingStyle.BALANCED
            profile.style_confidence = 0.5

    def _identify_strengths_weaknesses(self, profile: OpponentProfile):
        """Identify key strengths and weaknesses."""
        profile.strengths = []
        profile.weaknesses = []

        # Based on stats
        if profile.win_rate >= 0.7:
            profile.strengths.append("High win rate (70%+)")
        elif profile.win_rate < 0.4:
            profile.weaknesses.append("Low win rate (<40%)")

        if profile.avg_points_scored > 10:
            profile.strengths.append("High scoring output")
        elif profile.avg_points_scored < 5 and profile.avg_points_scored > 0:
            profile.weaknesses.append("Low scoring output")

        if profile.point_differential > 3:
            profile.strengths.append("Strong point differential")
        elif profile.point_differential < -2:
            profile.weaknesses.append("Negative point differential")

        if profile.world_rank > 0 and profile.world_rank <= 5:
            profile.strengths.append("Elite world ranking (Top 5)")
        elif profile.world_rank > 0 and profile.world_rank <= 10:
            profile.strengths.append("Strong world ranking (Top 10)")

        # Based on country (historical strength)
        if profile.country_code == 'KOR':
            profile.strengths.append("Korean program - elite technical training")
        elif profile.country_code == 'IRI':
            profile.strengths.append("Iranian program - strong physical style")
        elif profile.country_code == 'CHN':
            profile.strengths.append("Chinese program - disciplined approach")

    def _assess_threat_level(self, profile: OpponentProfile):
        """Assess threat level for KSA athletes."""
        if profile.world_rank > 0 and profile.world_rank <= 5:
            profile.threat_level = ThreatLevel.CRITICAL
        elif profile.world_rank <= 10:
            profile.threat_level = ThreatLevel.HIGH
        elif profile.world_rank <= 20:
            profile.threat_level = ThreatLevel.MEDIUM
        elif profile.world_rank > 0:
            profile.threat_level = ThreatLevel.LOW
        else:
            profile.threat_level = ThreatLevel.UNKNOWN

        # Elevate threat for key rival countries
        if profile.country_code in ['KOR', 'IRI', 'CHN'] and profile.threat_level == ThreatLevel.MEDIUM:
            profile.threat_level = ThreatLevel.HIGH

    def _analyze_recent_form(self, profile: OpponentProfile):
        """Analyze recent form over last 6 months."""
        if self.matches_df is None or self.matches_df.empty:
            return

        df = self.matches_df.copy()

        # Filter to recent matches
        date_col = next((c for c in df.columns if 'date' in c.lower()), None)
        if date_col:
            try:
                df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
                six_months_ago = datetime.now() - timedelta(days=180)
                df = df[df[date_col] >= six_months_ago]
            except Exception:
                pass

        # Find athlete's matches
        name_pattern = profile.name.upper()
        athlete1_col = next((c for c in df.columns if 'athlete1' in c.lower()), None)
        athlete2_col = next((c for c in df.columns if 'athlete2' in c.lower()), None)
        winner_col = next((c for c in df.columns if 'winner' in c.lower()), None)

        if not all([athlete1_col, athlete2_col, winner_col]):
            return

        recent_matches = df[
            (df[athlete1_col].str.upper().str.contains(name_pattern, na=False)) |
            (df[athlete2_col].str.upper().str.contains(name_pattern, na=False))
        ]

        # Build form string
        for _, match in recent_matches.iterrows():
            if name_pattern in str(match.get(winner_col, '')).upper():
                profile.recent_form.append('W')
            else:
                profile.recent_form.append('L')

        # Determine trend
        if len(profile.recent_form) >= 3:
            recent_3 = profile.recent_form[-3:]
            if recent_3.count('W') >= 2:
                profile.form_trend = "Improving"
            elif recent_3.count('L') >= 2:
                profile.form_trend = "Declining"
            else:
                profile.form_trend = "Stable"

    def _get_major_results(self, profile: OpponentProfile):
        """Get major competition results."""
        if self.matches_df is None:
            return

        df = self.matches_df.copy()

        # Find athlete's matches in major events
        name_pattern = profile.name.upper()
        athlete1_col = next((c for c in df.columns if 'athlete1' in c.lower()), None)
        athlete2_col = next((c for c in df.columns if 'athlete2' in c.lower()), None)
        comp_col = next((c for c in df.columns if 'competition' in c.lower()), None)
        round_col = next((c for c in df.columns if 'round' in c.lower()), None)

        if not all([athlete1_col, athlete2_col, comp_col]):
            return

        athlete_matches = df[
            (df[athlete1_col].str.upper().str.contains(name_pattern, na=False)) |
            (df[athlete2_col].str.upper().str.contains(name_pattern, na=False))
        ]

        # Look for finals/semi-finals
        major_keywords = ['olympic', 'world', 'grand prix', 'grand slam', 'asian']
        finals_keywords = ['final', 'gold', 'bronze']

        for _, match in athlete_matches.iterrows():
            comp_name = str(match.get(comp_col, '')).lower()
            round_stage = str(match.get(round_col, '')).lower() if round_col else ''

            is_major = any(kw in comp_name for kw in major_keywords)
            is_final = any(kw in round_stage for kw in finals_keywords) or any(kw in comp_name for kw in finals_keywords)

            if is_major or is_final:
                profile.major_results.append({
                    'competition': match.get(comp_col, ''),
                    'round': match.get(round_col, '') if round_col else '',
                    'result': 'Final' if is_final else 'Major Event'
                })

        # Limit to 5 most notable
        profile.major_results = profile.major_results[:5]

    # =========================================================================
    # HEAD-TO-HEAD ANALYSIS
    # =========================================================================

    def head_to_head(self, athlete1_name: str, athlete2_name: str) -> Optional[HeadToHeadRecord]:
        """
        Get head-to-head record between two athletes.

        Args:
            athlete1_name: First athlete name (usually KSA athlete)
            athlete2_name: Second athlete name (opponent)

        Returns:
            HeadToHeadRecord or None
        """
        if self.matches_df is None or self.matches_df.empty:
            return None

        df = self.matches_df.copy()

        name1_pattern = athlete1_name.upper()
        name2_pattern = athlete2_name.upper()

        athlete1_col = next((c for c in df.columns if 'athlete1' in c.lower()), None)
        athlete2_col = next((c for c in df.columns if 'athlete2' in c.lower()), None)
        winner_col = next((c for c in df.columns if 'winner' in c.lower()), None)
        score_col = next((c for c in df.columns if 'score' in c.lower()), None)

        if not all([athlete1_col, athlete2_col]):
            return None

        # Find matches where both athletes competed
        h2h_matches = df[
            ((df[athlete1_col].str.upper().str.contains(name1_pattern, na=False)) &
             (df[athlete2_col].str.upper().str.contains(name2_pattern, na=False))) |
            ((df[athlete1_col].str.upper().str.contains(name2_pattern, na=False)) &
             (df[athlete2_col].str.upper().str.contains(name1_pattern, na=False)))
        ]

        if h2h_matches.empty:
            return HeadToHeadRecord(
                athlete1_id='',
                athlete1_name=athlete1_name,
                athlete2_id='',
                athlete2_name=athlete2_name,
                total_meetings=0
            )

        record = HeadToHeadRecord(
            athlete1_id='',
            athlete1_name=athlete1_name,
            athlete2_id='',
            athlete2_name=athlete2_name,
            total_meetings=len(h2h_matches)
        )

        # Count wins
        if winner_col:
            record.athlete1_wins = len(h2h_matches[
                h2h_matches[winner_col].str.upper().str.contains(name1_pattern, na=False)
            ])
            record.athlete2_wins = len(h2h_matches[
                h2h_matches[winner_col].str.upper().str.contains(name2_pattern, na=False)
            ])

        # Calculate win rate
        if record.total_meetings > 0:
            record.win_rate_athlete1 = record.athlete1_wins / record.total_meetings

        # Determine dominant athlete
        if record.athlete1_wins > record.athlete2_wins:
            record.dominant_athlete = athlete1_name
        elif record.athlete2_wins > record.athlete1_wins:
            record.dominant_athlete = athlete2_name
        else:
            record.dominant_athlete = "Even"

        # Build match history
        for _, row in h2h_matches.iterrows():
            match = MatchRecord(
                date=str(row.get('date', '')),
                competition=str(row.get('competition', '')),
                opponent_name=athlete2_name if name1_pattern in str(row.get(athlete1_col, '')).upper() else athlete1_name,
                opponent_country='',
                result='W' if name1_pattern in str(row.get(winner_col, '')).upper() else 'L',
                score=str(row.get(score_col, '')) if score_col else '',
                round_stage=str(row.get('round', ''))
            )
            record.matches.append(match)

        return record

    # =========================================================================
    # SCOUTING REPORTS
    # =========================================================================

    def generate_scouting_report(self, athlete_name: str,
                                weight_category: str,
                                competition: str = "Upcoming Competition") -> ScoutingReport:
        """
        Generate comprehensive scouting report for an athlete.

        Args:
            athlete_name: KSA athlete name
            weight_category: Weight category (e.g., '-68kg')
            competition: Competition name

        Returns:
            ScoutingReport with likely opponents and recommendations
        """
        report = ScoutingReport(
            athlete_id='',
            athlete_name=athlete_name,
            weight_category=weight_category,
            competition=competition,
            generated_date=datetime.now().isoformat()
        )

        # Get likely opponents (top ranked in category)
        likely_opponents = self.get_category_rankings(weight_category, limit=10)

        for opp_data in likely_opponents:
            opp_name = opp_data.get('athlete_name', opp_data.get('NAME', ''))
            if opp_name.upper() != athlete_name.upper():  # Exclude the athlete themselves
                profile = self.get_opponent_profile(athlete_name=opp_name)
                if profile:
                    report.likely_opponents.append(profile)

        # Identify key threats
        for opp in report.likely_opponents:
            if opp.threat_level in [ThreatLevel.CRITICAL, ThreatLevel.HIGH]:
                report.key_threats.append(f"{opp.name} ({opp.country_code}) - Rank #{opp.world_rank}")

        # Generate tactical recommendations
        report.recommendations = self._generate_recommendations(athlete_name, report.likely_opponents)

        # Calculate medal probability (simplified)
        report.medal_probability = self._calculate_medal_probability(athlete_name, weight_category)
        report.gold_probability = report.medal_probability * 0.3  # Simplified estimate

        return report

    def get_category_rankings(self, weight_category: str, limit: int = 20) -> List[Dict]:
        """Get top ranked athletes in a weight category."""
        if self.rankings_df is None:
            return []

        df = self.rankings_df.copy()

        cat_col = 'weight_category' if 'weight_category' in df.columns else 'WEIGHT CATEGORY'
        rank_col = 'rank' if 'rank' in df.columns else 'RANK'

        if cat_col not in df.columns:
            return []

        # Filter to category
        category_df = df[df[cat_col].str.contains(weight_category.replace('+', r'\+'), case=False, na=False)]

        # Sort by rank
        if rank_col in category_df.columns:
            category_df = category_df.sort_values(rank_col)

        return category_df.head(limit).to_dict('records')

    def _generate_recommendations(self, athlete_name: str,
                                 opponents: List[OpponentProfile]) -> List[str]:
        """Generate tactical recommendations."""
        recommendations = []

        # General recommendations based on opponent analysis
        offensive_count = sum(1 for o in opponents if o.fighting_style == FightingStyle.OFFENSIVE)
        defensive_count = sum(1 for o in opponents if o.fighting_style in [FightingStyle.DEFENSIVE, FightingStyle.COUNTER])

        if offensive_count > defensive_count:
            recommendations.append("Many opponents favor offensive style - practice counter-attacking and defensive positioning")
        elif defensive_count > offensive_count:
            recommendations.append("Many opponents favor defensive/counter style - develop initiative and first-attack strategies")

        # Identify Korean opponents
        korean_opponents = [o for o in opponents if o.country_code == 'KOR']
        if korean_opponents:
            recommendations.append(f"Korean opponents ({len(korean_opponents)}): Expect high technical skill and fast foot techniques")

        # Identify Iranian opponents
        iranian_opponents = [o for o in opponents if o.country_code == 'IRI']
        if iranian_opponents:
            recommendations.append(f"Iranian opponents ({len(iranian_opponents)}): Prepare for physical strength and powerful body kicks")

        # High scorers warning
        high_scorers = [o for o in opponents if o.avg_points_scored > 12]
        if high_scorers:
            names = ', '.join([o.name for o in high_scorers[:3]])
            recommendations.append(f"High-scoring opponents: {names} - focus on defensive discipline")

        # General competition advice
        recommendations.append("Review video footage of key opponents before competition")
        recommendations.append("Focus on peak physical condition - strength and endurance for multiple bouts")

        return recommendations

    def _calculate_medal_probability(self, athlete_name: str, weight_category: str) -> float:
        """Calculate simplified medal probability."""
        # Find athlete's ranking
        if self.rankings_df is None:
            return 0.0

        df = self.rankings_df.copy()
        name_col = 'athlete_name' if 'athlete_name' in df.columns else 'NAME'
        rank_col = 'rank' if 'rank' in df.columns else 'RANK'

        athlete_data = df[df[name_col].str.upper().str.contains(athlete_name.upper(), na=False)]

        if athlete_data.empty:
            return 0.0

        rank = athlete_data.iloc[0].get(rank_col, 100)

        # Simple probability model based on rank
        if rank <= 3:
            return 0.70
        elif rank <= 5:
            return 0.55
        elif rank <= 8:
            return 0.40
        elif rank <= 12:
            return 0.25
        elif rank <= 20:
            return 0.15
        else:
            return 0.05

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    def get_saudi_athletes(self) -> List[Dict]:
        """Get all Saudi athletes from rankings."""
        if self.rankings_df is None:
            return []

        df = self.rankings_df.copy()
        country_col = 'country' if 'country' in df.columns else 'MEMBER NATION'

        saudi_df = df[df[country_col].str.contains('KSA|SAUDI', case=False, na=False)]
        return saudi_df.to_dict('records')

    def get_rival_profiles(self, weight_category: str,
                          rival_countries: List[str] = None) -> List[OpponentProfile]:
        """Get profiles of key rivals in a weight category."""
        if rival_countries is None:
            rival_countries = ASIAN_RIVALS

        profiles = []
        category_rankings = self.get_category_rankings(weight_category, limit=30)

        for athlete in category_rankings:
            country = self._get_country_code(athlete.get('country', athlete.get('MEMBER NATION', '')))
            if country in rival_countries:
                name = athlete.get('athlete_name', athlete.get('NAME', ''))
                profile = self.get_opponent_profile(athlete_name=name, country=country)
                if profile:
                    profiles.append(profile)

        return profiles

    def export_scouting_report(self, report: ScoutingReport,
                              output_path: str = None) -> str:
        """Export scouting report to JSON file."""
        if output_path is None:
            output_dir = Path('reports/scouting')
            output_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = output_dir / f"scouting_{report.athlete_name.replace(' ', '_')}_{timestamp}.json"

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)

        print(f"Scouting report saved: {output_path}")
        return str(output_path)


# =============================================================================
# STREAMLIT INTEGRATION
# =============================================================================

def render_opponent_card(profile: OpponentProfile) -> str:
    """Render opponent profile as HTML card for Streamlit - Team Saudi Theme."""
    # Team Saudi Brand Colors
    TEAL_PRIMARY = '#007167'
    GOLD_ACCENT = '#a08e66'
    TEAL_DARK = '#005a51'
    TEAL_LIGHT = '#009688'
    GRAY_BLUE = '#78909C'

    # Threat level colors - Team Saudi palette
    threat_colors = {
        ThreatLevel.CRITICAL: '#dc3545',    # Red for critical threat
        ThreatLevel.HIGH: GOLD_ACCENT,       # Gold for high threat
        ThreatLevel.MEDIUM: TEAL_LIGHT,      # Light teal for medium
        ThreatLevel.LOW: TEAL_PRIMARY,       # Primary teal for low
        ThreatLevel.UNKNOWN: GRAY_BLUE,
    }

    threat_color = threat_colors.get(profile.threat_level, GRAY_BLUE)

    # Form display with Team Saudi colors
    form_display = ''.join([
        f'<span style="color: {TEAL_PRIMARY if r == "W" else "#dc3545"}; font-weight: bold;">{r}</span>'
        for r in profile.recent_form[-5:]
    ]) or 'N/A'

    strengths_html = ''.join([f'<li>{s}</li>' for s in profile.strengths[:3]]) or '<li>No data</li>'
    weaknesses_html = ''.join([f'<li>{w}</li>' for w in profile.weaknesses[:3]]) or '<li>No data</li>'

    return f"""
    <div style="border: 2px solid {threat_color}; border-radius: 10px; padding: 15px; margin: 10px 0; background: white; font-family: 'Inter', sans-serif;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
            <div>
                <h3 style="margin: 0; color: #333;">{profile.name}</h3>
                <p style="margin: 5px 0; color: #666;">{profile.country} | {profile.weight_category}</p>
            </div>
            <div style="text-align: right;">
                <span style="background: {threat_color}; color: white; padding: 5px 10px; border-radius: 15px; font-size: 0.8em;">
                    {profile.threat_level.value}
                </span>
            </div>
        </div>

        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin: 15px 0;">
            <div style="text-align: center; padding: 10px; background: rgba(0, 113, 103, 0.08); border-radius: 8px;">
                <div style="font-size: 1.5em; font-weight: bold; color: {TEAL_PRIMARY};">#{profile.world_rank}</div>
                <div style="font-size: 0.8em; color: #666;">World Rank</div>
            </div>
            <div style="text-align: center; padding: 10px; background: rgba(0, 113, 103, 0.08); border-radius: 8px;">
                <div style="font-size: 1.5em; font-weight: bold; color: {TEAL_PRIMARY};">{profile.win_rate:.0%}</div>
                <div style="font-size: 0.8em; color: #666;">Win Rate</div>
            </div>
            <div style="text-align: center; padding: 10px; background: rgba(0, 113, 103, 0.08); border-radius: 8px;">
                <div style="font-size: 1.5em; font-weight: bold; color: {TEAL_PRIMARY};">{profile.avg_points_scored:.1f}</div>
                <div style="font-size: 0.8em; color: #666;">Avg Points</div>
            </div>
            <div style="text-align: center; padding: 10px; background: rgba(160, 142, 102, 0.08); border-radius: 8px;">
                <div style="font-size: 1.2em; font-weight: bold;">{form_display}</div>
                <div style="font-size: 0.8em; color: #666;">Recent Form</div>
            </div>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
            <div>
                <h4 style="color: {TEAL_PRIMARY}; margin-bottom: 5px;">Strengths</h4>
                <ul style="margin: 0; padding-left: 20px; font-size: 0.9em;">{strengths_html}</ul>
            </div>
            <div>
                <h4 style="color: {GOLD_ACCENT}; margin-bottom: 5px;">Weaknesses</h4>
                <ul style="margin: 0; padding-left: 20px; font-size: 0.9em;">{weaknesses_html}</ul>
            </div>
        </div>

        <div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid #eee;">
            <span style="color: #666; font-size: 0.85em;">
                Style: <strong style="color: {TEAL_DARK};">{profile.fighting_style.value}</strong> |
                Trend: <strong style="color: {TEAL_DARK};">{profile.form_trend}</strong>
            </span>
        </div>
    </div>
    """


# =============================================================================
# MAIN (CLI Testing)
# =============================================================================

def main():
    """Test the scouting manager."""
    print("=" * 60)
    print("TAEKWONDO SCOUTING MANAGER")
    print("=" * 60)

    scout = ScoutingManager()

    # Test getting category rankings
    print("\n[TEST] Top 10 in M-68kg:")
    top_10 = scout.get_category_rankings('-68kg', limit=10)
    for i, athlete in enumerate(top_10, 1):
        name = athlete.get('athlete_name', athlete.get('NAME', 'Unknown'))
        country = athlete.get('country', athlete.get('MEMBER NATION', '?'))
        rank = athlete.get('rank', athlete.get('RANK', '?'))
        print(f"  {i}. {name} ({country}) - Rank #{rank}")

    # Test opponent profile
    if top_10:
        first_athlete = top_10[0].get('athlete_name', top_10[0].get('NAME', ''))
        print(f"\n[TEST] Profile for: {first_athlete}")
        profile = scout.get_opponent_profile(athlete_name=first_athlete)
        if profile:
            print(f"  World Rank: #{profile.world_rank}")
            print(f"  Win Rate: {profile.win_rate:.1%}")
            print(f"  Fighting Style: {profile.fighting_style.value}")
            print(f"  Threat Level: {profile.threat_level.value}")
            print(f"  Strengths: {', '.join(profile.strengths[:3])}")

    # Test scouting report
    print("\n[TEST] Generating scouting report for M-68kg...")
    report = scout.generate_scouting_report(
        athlete_name="Test Athlete",
        weight_category="-68kg",
        competition="Asian Games 2026"
    )
    print(f"  Likely opponents: {len(report.likely_opponents)}")
    print(f"  Key threats: {len(report.key_threats)}")
    print(f"  Recommendations: {len(report.recommendations)}")

    print("\n" + "=" * 60)
    print("Scouting Manager Ready")
    print("=" * 60)


if __name__ == "__main__":
    main()
