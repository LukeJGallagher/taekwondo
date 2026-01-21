"""
Data Models for Taekwondo Performance Analysis
Structured schemas for athletes, competitions, matches, and analytics
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum


class WeightCategory(Enum):
    """Olympic and World Championship weight categories"""
    # Men's categories
    M_54 = "M-54kg"
    M_58 = "M-58kg"
    M_63 = "M-63kg"
    M_68 = "M-68kg"
    M_74 = "M-74kg"
    M_80 = "M-80kg"
    M_87 = "M-87kg"
    M_PLUS87 = "M+87kg"

    # Women's categories
    F_46 = "F-46kg"
    F_49 = "F-49kg"
    F_53 = "F-53kg"
    F_57 = "F-57kg"
    F_62 = "F-62kg"
    F_67 = "F-67kg"
    F_73 = "F-73kg"
    F_PLUS73 = "F+73kg"


class CompetitionLevel(Enum):
    """Competition tiers for ranking importance"""
    OLYMPIC_GAMES = "Olympic Games"
    WORLD_CHAMPIONSHIPS = "World Championships"
    GRAND_PRIX = "Grand Prix"
    GRAND_SLAM = "Grand Slam"
    PRESIDENT_CUP = "President's Cup"
    OPEN = "Open"
    CONTINENTAL = "Continental Championships"
    NATIONAL = "National Championships"


class MedalType(Enum):
    GOLD = "Gold"
    SILVER = "Silver"
    BRONZE = "Bronze"


@dataclass
class Athlete:
    """Individual athlete profile"""
    athlete_id: str
    name: str
    country_code: str  # ISO 3-letter code (e.g., KSA for Saudi Arabia)
    country_name: str
    birth_date: Optional[datetime] = None
    gender: str = ""  # M or F
    weight_category: Optional[WeightCategory] = None
    world_rank: Optional[int] = None
    world_ranking_points: float = 0.0
    active: bool = True

    # Career statistics
    total_competitions: int = 0
    total_matches: int = 0
    wins: int = 0
    losses: int = 0
    win_rate: float = 0.0

    # Medals
    gold_medals: int = 0
    silver_medals: int = 0
    bronze_medals: int = 0

    # Competition history
    competitions: List[str] = field(default_factory=list)  # List of competition IDs
    matches: List[str] = field(default_factory=list)  # List of match IDs

    # Additional metadata
    coach: str = ""
    club_team: str = ""
    height_cm: Optional[float] = None
    reach_cm: Optional[float] = None

    def __post_init__(self):
        if self.total_matches > 0:
            self.win_rate = (self.wins / self.total_matches) * 100


@dataclass
class Match:
    """Individual match/bout details"""
    match_id: str
    competition_id: str
    date: datetime
    round: str  # "Preliminary", "Round of 16", "Quarter-Final", "Semi-Final", "Final"

    # Athletes
    athlete1_id: str
    athlete1_name: str
    athlete1_country: str

    athlete2_id: str
    athlete2_name: str
    athlete2_country: str

    # Results
    winner_id: str
    winner_name: str
    loser_id: str
    loser_name: str

    # Scoring
    athlete1_round1: int = 0
    athlete1_round2: int = 0
    athlete1_round3: int = 0
    athlete1_total: int = 0

    athlete2_round1: int = 0
    athlete2_round2: int = 0
    athlete2_round3: int = 0
    athlete2_total: int = 0

    # Match details
    weight_category: Optional[WeightCategory] = None
    duration_seconds: int = 0
    win_type: str = ""  # "Points", "Knockout", "Referee Stop Contest", "Withdrawal"

    # Advanced stats (if available)
    athlete1_head_kicks: int = 0
    athlete1_body_kicks: int = 0
    athlete1_punches: int = 0
    athlete1_penalties: int = 0

    athlete2_head_kicks: int = 0
    athlete2_body_kicks: int = 0
    athlete2_punches: int = 0
    athlete2_penalties: int = 0


@dataclass
class Competition:
    """Competition/Tournament details"""
    competition_id: str
    name: str
    level: CompetitionLevel
    start_date: datetime
    end_date: datetime
    location_city: str
    location_country: str

    # Categories
    weight_categories: List[WeightCategory] = field(default_factory=list)

    # Participants
    total_athletes: int = 0
    countries_represented: int = 0

    # Results
    matches: List[str] = field(default_factory=list)  # List of match IDs

    # Saudi-specific tracking
    saudi_athletes: List[str] = field(default_factory=list)  # List of Saudi athlete IDs
    saudi_medals: Dict[str, int] = field(default_factory=dict)  # {'gold': 0, 'silver': 1, 'bronze': 2}


@dataclass
class PerformanceMetrics:
    """
    Advanced performance analytics for an athlete
    Saudi-focused metrics for performance analysis
    """
    athlete_id: str
    analysis_date: datetime

    # Current form (last 6 months)
    recent_win_rate: float = 0.0
    recent_matches: int = 0
    recent_wins: int = 0
    recent_losses: int = 0

    # Competition level analysis
    olympic_matches: int = 0
    olympic_win_rate: float = 0.0
    world_champs_matches: int = 0
    world_champs_win_rate: float = 0.0
    grand_prix_matches: int = 0
    grand_prix_win_rate: float = 0.0

    # Opponent strength
    avg_opponent_rank: float = 0.0
    wins_vs_top10: int = 0
    wins_vs_top50: int = 0
    losses_vs_lower_ranked: int = 0  # Upset losses

    # Technical performance
    avg_points_scored: float = 0.0
    avg_points_conceded: float = 0.0
    avg_point_differential: float = 0.0

    knockout_rate: float = 0.0  # % of wins by KO
    decision_rate: float = 0.0  # % of wins by decision

    # Round-by-round performance
    round1_avg_score: float = 0.0
    round2_avg_score: float = 0.0
    round3_avg_score: float = 0.0

    # Regional performance
    wins_in_asia: int = 0
    wins_in_europe: int = 0
    wins_in_americas: int = 0
    home_advantage_rate: float = 0.0

    # Head-to-head records
    common_opponents: Dict[str, Dict] = field(default_factory=dict)  # {opponent_id: {wins: X, losses: Y}}

    # Trends
    performance_trend: str = ""  # "Improving", "Stable", "Declining"
    ranking_change_6mo: int = 0
    ranking_change_12mo: int = 0


@dataclass
class SaudiTeamAnalytics:
    """
    Team-level analytics for Saudi Arabia
    Benchmark against rivals and identify development areas
    """
    analysis_date: datetime

    # Overall team metrics
    total_active_athletes: int = 0
    athletes_in_top10: int = 0
    athletes_in_top50: int = 0
    athletes_in_top100: int = 0

    # Medal counts (current year)
    total_gold: int = 0
    total_silver: int = 0
    total_bronze: int = 0

    # Weight category strength
    strongest_categories: List[str] = field(default_factory=list)
    development_categories: List[str] = field(default_factory=list)

    # Benchmarking against key rivals
    rival_comparison: Dict[str, Dict] = field(default_factory=dict)
    # Example: {'KOR': {'ranking_avg': 25.3, 'medal_count': 15}, 'GBR': {...}}

    # Competition participation
    olympic_qualifiers: int = 0
    world_champs_participants: int = 0
    grand_prix_participation_rate: float = 0.0

    # Performance by competition level
    olympic_win_rate: float = 0.0
    world_champs_win_rate: float = 0.0
    grand_prix_win_rate: float = 0.0

    # Development pipeline
    youth_athletes_u21: int = 0
    emerging_talents: List[str] = field(default_factory=list)  # Athlete IDs

    # Strategic insights
    key_strengths: List[str] = field(default_factory=list)
    areas_for_improvement: List[str] = field(default_factory=list)
    recommended_competitions: List[str] = field(default_factory=list)


def create_sample_saudi_athlete() -> Athlete:
    """Helper function to create sample athlete for testing"""
    return Athlete(
        athlete_id="KSA001",
        name="Example Saudi Athlete",
        country_code="KSA",
        country_name="Saudi Arabia",
        gender="M",
        weight_category=WeightCategory.M_68,
        world_rank=45,
        world_ranking_points=125.5,
        total_competitions=25,
        total_matches=78,
        wins=52,
        losses=26,
        gold_medals=3,
        silver_medals=5,
        bronze_medals=7
    )
