"""
Advanced KPI Analysis
Research-validated performance indicators for Olympic taekwondo
Based on 2024 machine learning studies and historical data analysis
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class MedalOpportunity:
    """Medal opportunity analysis result"""
    athlete_name: str
    weight_category: str
    current_rank: int
    opportunity_score: float  # 0-100
    rank_score: float
    competition_density_score: float
    form_score: float
    recommendation: str
    priority_level: str


@dataclass
class OlympicQualificationAnalysis:
    """Olympic qualification probability analysis"""
    athlete_name: str
    weight_category: str
    current_rank: int
    qualification_probability: float  # 0-100
    path: str  # 'automatic', 'continental', 'tripartite'
    days_to_deadline: int
    target_rank: int
    rank_gap: int
    recommended_competitions: List[str]


class AdvancedKPIAnalyzer:
    """
    Advanced performance analysis using research-validated metrics
    """

    def __init__(self, matches_df: pd.DataFrame = None, rankings_df: pd.DataFrame = None):
        self.matches_df = matches_df
        self.rankings_df = rankings_df

        # Research constants
        self.OLYMPIC_DEADLINE = datetime(2028, 6, 30)
        self.OLYMPIC_AUTO_QUALIFY_RANK = 5  # Top 5 automatic
        self.CONTINENTAL_QUOTA = 2  # Approximate continental spots

    def calculate_medal_opportunity_score(
        self,
        rank: int,
        weight_category: str,
        recent_win_rate: float = None
    ) -> MedalOpportunity:
        """
        Calculate medal opportunity score using research formula

        Formula from strategic research:
        Score = (Rank Score × 0.60) + (Competition Density × 0.30) + (Form × 0.10)

        Args:
            rank: Current world ranking
            weight_category: Weight category
            recent_win_rate: Win rate last 6 months (0-100)

        Returns:
            MedalOpportunity object with detailed scoring
        """
        # Component 1: Rank Score (60% weight)
        # max(0, 100 - (rank × 4))
        rank_score = max(0, 100 - (rank * 4))

        # Component 2: Competition Density Score (30% weight)
        # Estimate based on weight category
        # Olympic categories: M-58, M-68, M-80, M+80, W-49, W-57, W-67, W+67
        high_competition_categories = ['M-68kg', 'M-58kg', 'W-57kg']
        low_competition_categories = ['M+80kg', 'W+67kg', 'M-54kg']

        if weight_category in high_competition_categories:
            competition_factor = 0.3  # High competition
        elif weight_category in low_competition_categories:
            competition_factor = 0.7  # Lower competition = better opportunity
        else:
            competition_factor = 0.5  # Medium competition

        competition_density_score = competition_factor * 100

        # Component 3: Form Score (10% weight)
        if recent_win_rate is not None:
            form_score = recent_win_rate
        else:
            form_score = 50  # Default if no data

        # Calculate total opportunity score
        opportunity_score = (
            (rank_score * 0.60) +
            (competition_density_score * 0.30) +
            (form_score * 0.10)
        )

        # Generate recommendation
        if opportunity_score >= 85:
            priority = "CRITICAL"
            recommendation = "Immediate action: Dedicated coach, all Grand Prix attendance, full resources"
        elif opportunity_score >= 75:
            priority = "HIGH"
            recommendation = "High priority: Increase training support, strategic competition selection"
        elif opportunity_score >= 60:
            priority = "MEDIUM"
            recommendation = "Monitor closely: Assess progress quarterly, targeted development"
        else:
            priority = "DEVELOPMENT"
            recommendation = "Long-term development: Youth pipeline, skill development focus"

        return MedalOpportunity(
            athlete_name="",  # To be filled by caller
            weight_category=weight_category,
            current_rank=rank,
            opportunity_score=round(opportunity_score, 1),
            rank_score=round(rank_score, 1),
            competition_density_score=round(competition_density_score, 1),
            form_score=round(form_score, 1),
            recommendation=recommendation,
            priority_level=priority
        )

    def analyze_olympic_qualification_probability(
        self,
        athlete_name: str,
        current_rank: int,
        weight_category: str,
        recent_trend: str = "stable"  # 'improving', 'stable', 'declining'
    ) -> OlympicQualificationAnalysis:
        """
        Analyze probability of Olympic qualification

        Paths to qualification:
        1. Top 5 world ranking (automatic)
        2. Continental qualification (2-3 spots)
        3. Tripartite commission (wild card)

        Args:
            athlete_name: Athlete name
            current_rank: Current world rank
            weight_category: Weight category
            recent_trend: Ranking trend

        Returns:
            OlympicQualificationAnalysis with probability and recommendations
        """
        days_remaining = (self.OLYMPIC_DEADLINE - datetime.now()).days

        # Determine qualification path and probability
        if current_rank <= self.OLYMPIC_AUTO_QUALIFY_RANK:
            path = "automatic"
            base_probability = 95  # Very high if maintaining
            target_rank = current_rank  # Maintain
            rank_gap = 0
        elif current_rank <= 12:
            path = "automatic_attainable"
            base_probability = 60  # Good chance
            target_rank = 5
            rank_gap = current_rank - 5
        elif current_rank <= 20:
            path = "continental"
            base_probability = 40  # Continental route likely
            target_rank = 12  # Improve to be safe
            rank_gap = current_rank - 12
        elif current_rank <= 50:
            path = "continental_difficult"
            base_probability = 20  # Challenging
            target_rank = 15
            rank_gap = current_rank - 15
        else:
            path = "tripartite_only"
            base_probability = 5  # Very difficult
            target_rank = 30
            rank_gap = current_rank - 30

        # Adjust for trend
        trend_adjustments = {
            'improving': +15,
            'stable': 0,
            'declining': -15
        }
        probability = min(100, max(0, base_probability + trend_adjustments.get(recent_trend, 0)))

        # Adjust for time remaining
        if days_remaining < 365:  # Less than 1 year
            probability *= 0.8  # Harder to improve

        # Recommended competitions based on gap
        if rank_gap > 10:
            competitions = ["ALL Grand Prix", "World Championships", "Asian Championships", "Continental Opens"]
        elif rank_gap > 5:
            competitions = ["ALL Grand Prix", "World Championships", "Asian Championships"]
        elif rank_gap > 0:
            competitions = ["Grand Prix (strategic)", "World Championships", "Asian Championships"]
        else:
            competitions = ["World Championships", "Strategic Grand Prix selection"]

        return OlympicQualificationAnalysis(
            athlete_name=athlete_name,
            weight_category=weight_category,
            current_rank=current_rank,
            qualification_probability=round(probability, 1),
            path=path,
            days_to_deadline=max(0, days_remaining),
            target_rank=target_rank,
            rank_gap=max(0, rank_gap),
            recommended_competitions=competitions
        )

    def calculate_performance_trend_score(
        self,
        rankings_history: pd.DataFrame
    ) -> Dict:
        """
        Calculate performance trend using ranking history

        Args:
            rankings_history: DataFrame with columns [date, rank]

        Returns:
            Dict with trend analysis
        """
        if len(rankings_history) < 2:
            return {
                'trend': 'insufficient_data',
                'trend_score': 0,
                'velocity': 0,
                'acceleration': 0
            }

        # Sort by date
        rankings_history = rankings_history.sort_values('date')

        # Calculate velocity (rank change per month)
        ranks = rankings_history['rank'].values
        first_rank = ranks[0]
        last_rank = ranks[-1]
        time_delta_days = (
            pd.to_datetime(rankings_history.iloc[-1]['date']) -
            pd.to_datetime(rankings_history.iloc[0]['date'])
        ).days

        if time_delta_days == 0:
            return {
                'trend': 'stable',
                'trend_score': 50,
                'velocity': 0,
                'acceleration': 0
            }

        months = time_delta_days / 30
        velocity = (first_rank - last_rank) / months  # Positive = improving

        # Calculate acceleration (is improvement accelerating?)
        if len(ranks) >= 3:
            mid_point = len(ranks) // 2
            first_half_velocity = (ranks[0] - ranks[mid_point]) / (months / 2)
            second_half_velocity = (ranks[mid_point] - ranks[-1]) / (months / 2)
            acceleration = second_half_velocity - first_half_velocity
        else:
            acceleration = 0

        # Categorize trend
        if velocity > 2:  # Improving >2 ranks/month
            trend = 'rapidly_improving'
            trend_score = 90
        elif velocity > 0.5:
            trend = 'improving'
            trend_score = 70
        elif velocity > -0.5:
            trend = 'stable'
            trend_score = 50
        elif velocity > -2:
            trend = 'declining'
            trend_score = 30
        else:
            trend = 'rapidly_declining'
            trend_score = 10

        return {
            'trend': trend,
            'trend_score': trend_score,
            'velocity': round(velocity, 2),
            'acceleration': round(acceleration, 2),
            'months_tracked': round(months, 1)
        }

    def analyze_competition_roi(
        self,
        competition_tier: str,
        estimated_cost: float,
        ranking_points: int,
        current_rank: int
    ) -> Dict:
        """
        Calculate ROI for competition attendance

        Args:
            competition_tier: 'grand_prix', 'world_champs', 'continental', etc.
            estimated_cost: Total cost in USD
            ranking_points: Points available
            current_rank: Athlete's current rank

        Returns:
            Dict with ROI analysis
        """
        # Estimate qualification probability based on rank and tier
        tier_difficulty = {
            'world_champs': 0.3,  # Very competitive
            'grand_prix': 0.5,   # Competitive
            'grand_slam': 0.4,
            'continental': 0.6,  # More achievable
            'open': 0.7          # Easiest
        }

        difficulty = tier_difficulty.get(competition_tier.lower(), 0.5)

        # Adjust for rank (better rank = higher success probability)
        rank_factor = max(0.2, 1 - (current_rank / 100))

        qualification_probability = difficulty * rank_factor

        # Expected points
        expected_points = ranking_points * qualification_probability

        # ROI calculation
        if estimated_cost > 0:
            roi = (expected_points / estimated_cost) * 100
        else:
            roi = 0

        # Strategic value (not just financial)
        strategic_multiplier = {
            'world_champs': 2.0,  # Extra valuable
            'grand_prix': 1.5,
            'grand_slam': 1.8,
            'continental': 1.3,
            'open': 1.0
        }

        strategic_roi = roi * strategic_multiplier.get(competition_tier.lower(), 1.0)

        return {
            'competition_tier': competition_tier,
            'estimated_cost': estimated_cost,
            'available_points': ranking_points,
            'qualification_probability': round(qualification_probability * 100, 1),
            'expected_points': round(expected_points, 1),
            'financial_roi': round(roi, 2),
            'strategic_roi': round(strategic_roi, 2),
            'recommendation': 'Attend' if strategic_roi > 50 else 'Consider alternatives'
        }


def main():
    """Example usage and testing"""
    print("Advanced KPI Analyzer - Testing")
    print("=" * 70)

    analyzer = AdvancedKPIAnalyzer()

    # Example 1: Medal Opportunity Score
    print("\n1. MEDAL OPPORTUNITY ANALYSIS")
    print("-" * 70)

    # Simulating Dunya Abutaleb (W-49kg, hypothetical rank 18)
    opportunity = analyzer.calculate_medal_opportunity_score(
        rank=18,
        weight_category="W-49kg",
        recent_win_rate=65.0
    )

    print(f"Weight Category: {opportunity.weight_category}")
    print(f"Current Rank: {opportunity.current_rank}")
    print(f"Overall Score: {opportunity.opportunity_score}/100")
    print(f"  - Rank Component: {opportunity.rank_score}/100 (60% weight)")
    print(f"  - Competition Density: {opportunity.competition_density_score}/100 (30% weight)")
    print(f"  - Form: {opportunity.form_score}/100 (10% weight)")
    print(f"Priority: {opportunity.priority_level}")
    print(f"Recommendation: {opportunity.recommendation}")

    # Example 2: Olympic Qualification Probability
    print("\n2. OLYMPIC QUALIFICATION ANALYSIS")
    print("-" * 70)

    qualification = analyzer.analyze_olympic_qualification_probability(
        athlete_name="Example Athlete",
        current_rank=18,
        weight_category="W-49kg",
        recent_trend="improving"
    )

    print(f"Athlete: {qualification.athlete_name}")
    print(f"Current Rank: {qualification.current_rank}")
    print(f"Qualification Probability: {qualification.qualification_probability}%")
    print(f"Primary Path: {qualification.path}")
    print(f"Days to Deadline: {qualification.days_to_deadline}")
    print(f"Target Rank: {qualification.target_rank}")
    print(f"Rank Gap: {qualification.rank_gap}")
    print(f"Recommended Competitions:")
    for comp in qualification.recommended_competitions:
        print(f"  - {comp}")

    # Example 3: Competition ROI
    print("\n3. COMPETITION ROI ANALYSIS")
    print("-" * 70)

    roi_analysis = analyzer.analyze_competition_roi(
        competition_tier="grand_prix",
        estimated_cost=5000,  # USD
        ranking_points=120,
        current_rank=18
    )

    print(f"Competition: {roi_analysis['competition_tier']}")
    print(f"Cost: ${roi_analysis['estimated_cost']:,}")
    print(f"Points Available: {roi_analysis['available_points']}")
    print(f"Qualification Probability: {roi_analysis['qualification_probability']}%")
    print(f"Expected Points: {roi_analysis['expected_points']}")
    print(f"Financial ROI: {roi_analysis['financial_roi']}%")
    print(f"Strategic ROI: {roi_analysis['strategic_roi']}%")
    print(f"Recommendation: {roi_analysis['recommendation']}")

    print("\n" + "=" * 70)
    print("Advanced KPI analysis ready for integration")


if __name__ == "__main__":
    main()
