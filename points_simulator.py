"""
Points Simulator for Taekwondo Rankings
Model "what if" scenarios for competition attendance decisions

Simulates ranking points accumulation and projects future rankings
based on different competition attendance strategies.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path

from config import (
    ASIAN_GAMES_2026, LA_2028_OLYMPICS, DUAL_TRACK_MILESTONES,
    COMPETITION_RANKING_POINTS
)


@dataclass
class Competition:
    """Competition details for simulation"""
    name: str
    date: str
    tier: str  # 'olympic', 'world_champs', 'grand_prix', 'grand_slam', 'continental', 'open'
    location: str = ""
    estimated_cost_usd: float = 0
    points_gold: int = 0
    points_silver: int = 0
    points_bronze: int = 0
    points_r16: int = 0
    points_r32: int = 0


@dataclass
class SimulationScenario:
    """A simulation scenario with projected outcomes"""
    name: str
    competitions: List[str]
    expected_finishes: Dict[str, str]  # competition_name: 'gold'/'silver'/'bronze'/'r16'/'r32'/'dnf'
    total_cost: float = 0
    projected_points: float = 0
    projected_world_rank: int = 0
    projected_asian_rank: int = 0
    asian_games_status: str = ""
    olympic_probability: float = 0
    roi_score: float = 0


@dataclass
class AthleteSimulation:
    """Simulation results for an athlete"""
    athlete_name: str
    weight_category: str
    current_rank: int
    current_points: float
    current_asian_rank: int
    scenarios: List[SimulationScenario] = field(default_factory=list)


# Competition point values (World Taekwondo standard)
COMPETITION_POINTS = {
    'olympic': {
        'gold': 200, 'silver': 150, 'bronze': 100, 'r16': 40, 'r32': 20
    },
    'world_champs': {
        'gold': 120, 'silver': 86.4, 'bronze': 60, 'r16': 24, 'r32': 12
    },
    'grand_prix': {
        'gold': 40, 'silver': 28.8, 'bronze': 20, 'r16': 8, 'r32': 4
    },
    'grand_slam': {
        'gold': 80, 'silver': 57.6, 'bronze': 40, 'r16': 16, 'r32': 8
    },
    'continental': {
        'gold': 20, 'silver': 14.4, 'bronze': 10, 'r16': 4, 'r32': 2
    },
    'open': {
        'gold': 10, 'silver': 7.2, 'bronze': 5, 'r16': 2, 'r32': 1
    }
}

# Upcoming competitions calendar (2025-2028)
UPCOMING_COMPETITIONS = [
    Competition('Grand Prix Rome 2025', '2025-03-15', 'grand_prix', 'Rome, Italy', 5000),
    Competition('Asian Championships 2025', '2025-05-10', 'continental', 'TBD, Asia', 4000),
    Competition('Grand Prix Manchester 2025', '2025-06-20', 'grand_prix', 'Manchester, UK', 5500),
    Competition('World Championships 2025', '2025-09-15', 'world_champs', 'TBD', 8000),
    Competition('Grand Slam 2025', '2025-11-01', 'grand_slam', 'TBD', 6000),
    Competition('Grand Prix Rome 2026', '2026-03-15', 'grand_prix', 'Rome, Italy', 5000),
    Competition('Asian Championships 2026', '2026-05-10', 'continental', 'TBD, Asia', 4000),
    Competition('Asian Games 2026', '2026-09-19', 'continental', 'Nagoya, Japan', 6000),
    Competition('World Championships 2026', '2026-10-15', 'world_champs', 'TBD', 8000),
    Competition('Grand Prix Series 2027', '2027-03-01', 'grand_prix', 'TBD', 5000),
    Competition('World Championships 2027', '2027-09-15', 'world_champs', 'TBD', 8000),
    Competition('Grand Prix Series 2028', '2028-01-15', 'grand_prix', 'TBD', 5000),
    Competition('Olympic Qualifier 2028', '2028-05-01', 'continental', 'TBD', 6000),
    Competition('LA Olympics 2028', '2028-07-14', 'olympic', 'Los Angeles, USA', 10000),
]


class PointsSimulator:
    """
    Simulate ranking points and project future rankings
    """

    def __init__(self, rankings_df: pd.DataFrame = None):
        self.rankings_df = rankings_df
        self.competitions = {c.name: c for c in UPCOMING_COMPETITIONS}

        # Populate point values
        for comp in UPCOMING_COMPETITIONS:
            if comp.tier in COMPETITION_POINTS:
                points = COMPETITION_POINTS[comp.tier]
                comp.points_gold = points['gold']
                comp.points_silver = points['silver']
                comp.points_bronze = points['bronze']
                comp.points_r16 = points['r16']
                comp.points_r32 = points['r32']

    def get_available_competitions(self, start_date: str = None, end_date: str = None) -> List[Competition]:
        """Get list of upcoming competitions within date range."""
        if start_date is None:
            start_date = datetime.now().strftime('%Y-%m-%d')
        if end_date is None:
            end_date = '2028-12-31'

        competitions = []
        for comp in UPCOMING_COMPETITIONS:
            comp_date = datetime.strptime(comp.date, '%Y-%m-%d')
            if start_date <= comp.date <= end_date:
                competitions.append(comp)

        return sorted(competitions, key=lambda x: x.date)

    def calculate_points_for_finish(self, competition_name: str, finish: str) -> float:
        """Calculate points earned for a given finish at a competition."""
        comp = self.competitions.get(competition_name)
        if not comp:
            return 0

        finish_map = {
            'gold': comp.points_gold,
            'silver': comp.points_silver,
            'bronze': comp.points_bronze,
            'r16': comp.points_r16,
            'r32': comp.points_r32,
            'dnf': 0,
            'dns': 0
        }

        return finish_map.get(finish.lower(), 0)

    def simulate_scenario(
        self,
        athlete_name: str,
        current_rank: int,
        current_points: float,
        competitions: List[str],
        expected_finishes: Dict[str, str],
        weight_category: str = ""
    ) -> SimulationScenario:
        """
        Simulate a scenario with given competitions and expected finishes.

        Args:
            athlete_name: Athlete name
            current_rank: Current world rank
            current_points: Current ranking points
            competitions: List of competition names to attend
            expected_finishes: Dict mapping competition name to expected finish
            weight_category: Weight category

        Returns:
            SimulationScenario with projected outcomes
        """
        scenario = SimulationScenario(
            name=f"Scenario: {len(competitions)} competitions",
            competitions=competitions,
            expected_finishes=expected_finishes
        )

        # Calculate total cost
        total_cost = 0
        for comp_name in competitions:
            comp = self.competitions.get(comp_name)
            if comp:
                total_cost += comp.estimated_cost_usd
        scenario.total_cost = total_cost

        # Calculate projected points
        total_new_points = 0
        for comp_name in competitions:
            finish = expected_finishes.get(comp_name, 'r32')
            points = self.calculate_points_for_finish(comp_name, finish)
            total_new_points += points

        scenario.projected_points = current_points + total_new_points

        # Estimate rank change (simplified model)
        # Assume average competitor gains ~30 points per year
        avg_competitor_gain = 30
        points_advantage = total_new_points - avg_competitor_gain

        # Rough estimate: every 10 points = 1 rank position
        rank_change = int(points_advantage / 10)
        scenario.projected_world_rank = max(1, current_rank - rank_change)

        # Asian rank estimate (assume similar ratio)
        current_asian_rank = self._estimate_asian_rank(current_rank)
        scenario.projected_asian_rank = max(1, current_asian_rank - int(rank_change * 0.6))

        # Asian Games qualification status
        if scenario.projected_asian_rank <= 8:
            scenario.asian_games_status = "QUALIFIED"
        elif scenario.projected_asian_rank <= 12:
            scenario.asian_games_status = "BUBBLE"
        else:
            scenario.asian_games_status = "OUTSIDE"

        # Olympic probability
        scenario.olympic_probability = self._calculate_olympic_probability(
            scenario.projected_world_rank,
            scenario.projected_asian_rank,
            weight_category
        )

        # ROI score (points per dollar, scaled)
        if total_cost > 0:
            points_per_dollar = total_new_points / total_cost
            scenario.roi_score = min(100, points_per_dollar * 1000)  # Scale to 0-100
        else:
            scenario.roi_score = 0

        return scenario

    def _estimate_asian_rank(self, world_rank: int) -> int:
        """Estimate Asian rank from world rank (rough approximation)."""
        # Assume ~40% of top 50 are Asian
        if world_rank <= 10:
            return max(1, int(world_rank * 0.4))
        elif world_rank <= 30:
            return max(1, int(world_rank * 0.5))
        else:
            return max(1, int(world_rank * 0.6))

    def _calculate_olympic_probability(
        self,
        world_rank: int,
        asian_rank: int,
        weight_category: str
    ) -> float:
        """Calculate probability of Olympic qualification."""
        # Check if Olympic category
        olympic_categories = LA_2028_OLYMPICS['weight_categories']
        is_olympic_category = (
            weight_category in olympic_categories.get('M', []) or
            weight_category in olympic_categories.get('F', [])
        )

        if not is_olympic_category:
            return 0  # Non-Olympic category

        # Base probability from world rank
        if world_rank <= 5:
            base_prob = 95  # Almost certain
        elif world_rank <= 10:
            base_prob = 70
        elif world_rank <= 15:
            base_prob = 50
        elif world_rank <= 25:
            base_prob = 30
        elif world_rank <= 50:
            base_prob = 15
        else:
            base_prob = 5

        # Adjust for continental qualification path
        if asian_rank <= 2:
            base_prob = min(100, base_prob + 20)  # Strong continental backup
        elif asian_rank <= 4:
            base_prob = min(100, base_prob + 10)

        return base_prob

    def compare_scenarios(
        self,
        athlete_name: str,
        current_rank: int,
        current_points: float,
        scenarios: List[Dict],
        weight_category: str = ""
    ) -> List[SimulationScenario]:
        """
        Compare multiple attendance scenarios.

        Args:
            athlete_name: Athlete name
            current_rank: Current world rank
            current_points: Current points
            scenarios: List of dicts with 'name', 'competitions', 'finishes'
            weight_category: Weight category

        Returns:
            List of SimulationScenario objects sorted by ROI
        """
        results = []

        for scenario_def in scenarios:
            scenario = self.simulate_scenario(
                athlete_name=athlete_name,
                current_rank=current_rank,
                current_points=current_points,
                competitions=scenario_def['competitions'],
                expected_finishes=scenario_def['finishes'],
                weight_category=weight_category
            )
            scenario.name = scenario_def.get('name', scenario.name)
            results.append(scenario)

        # Sort by ROI score
        results.sort(key=lambda x: x.roi_score, reverse=True)

        return results

    def generate_optimal_strategy(
        self,
        athlete_name: str,
        current_rank: int,
        current_points: float,
        budget: float,
        target_rank: int = None,
        weight_category: str = "",
        target_event: str = "asian_games"  # 'asian_games' or 'olympics'
    ) -> Dict:
        """
        Generate optimal competition attendance strategy within budget.

        Args:
            athlete_name: Athlete name
            current_rank: Current world rank
            current_points: Current points
            budget: Maximum budget in USD
            target_rank: Target rank to achieve (optional)
            weight_category: Weight category
            target_event: 'asian_games' or 'olympics'

        Returns:
            Dict with optimal strategy recommendation
        """
        # Get relevant competitions based on target event
        if target_event == 'asian_games':
            deadline = ASIAN_GAMES_2026['qualification_deadline']
            must_attend = ['Asian Championships 2025', 'Asian Championships 2026']
        else:
            deadline = LA_2028_OLYMPICS['qualification_deadline']
            must_attend = ['World Championships 2025', 'World Championships 2026', 'World Championships 2027']

        available_comps = self.get_available_competitions(end_date=deadline)

        # Filter by budget
        affordable_comps = []
        remaining_budget = budget

        # Prioritize must-attend events
        for comp in available_comps:
            if comp.name in must_attend and comp.estimated_cost_usd <= remaining_budget:
                affordable_comps.append(comp)
                remaining_budget -= comp.estimated_cost_usd

        # Add high-value competitions
        for comp in available_comps:
            if comp.name not in must_attend and comp.estimated_cost_usd <= remaining_budget:
                # Prioritize by tier
                if comp.tier in ['world_champs', 'grand_prix', 'grand_slam']:
                    affordable_comps.append(comp)
                    remaining_budget -= comp.estimated_cost_usd

        # Create scenarios
        conservative_finishes = {c.name: 'r16' for c in affordable_comps}
        realistic_finishes = {c.name: 'bronze' if c.tier in ['continental', 'open'] else 'r16'
                            for c in affordable_comps}
        optimistic_finishes = {c.name: 'silver' if c.tier in ['continental', 'open'] else 'bronze'
                             for c in affordable_comps}

        scenarios = [
            {'name': 'Conservative', 'competitions': [c.name for c in affordable_comps], 'finishes': conservative_finishes},
            {'name': 'Realistic', 'competitions': [c.name for c in affordable_comps], 'finishes': realistic_finishes},
            {'name': 'Optimistic', 'competitions': [c.name for c in affordable_comps], 'finishes': optimistic_finishes},
        ]

        results = self.compare_scenarios(
            athlete_name, current_rank, current_points, scenarios, weight_category
        )

        return {
            'athlete': athlete_name,
            'current_rank': current_rank,
            'budget': budget,
            'target_event': target_event,
            'recommended_competitions': [c.name for c in affordable_comps],
            'total_cost': sum(c.estimated_cost_usd for c in affordable_comps),
            'scenarios': results,
            'recommendation': results[0] if results else None
        }

    def get_competition_calendar_df(self) -> pd.DataFrame:
        """Get competitions as DataFrame for display."""
        data = []
        for comp in UPCOMING_COMPETITIONS:
            data.append({
                'Competition': comp.name,
                'Date': comp.date,
                'Tier': comp.tier.replace('_', ' ').title(),
                'Location': comp.location,
                'Est. Cost ($)': f"${comp.estimated_cost_usd:,}",
                'Gold Points': comp.points_gold,
                'Silver Points': comp.points_silver,
                'Bronze Points': comp.points_bronze
            })

        return pd.DataFrame(data)


def main():
    """Test the points simulator."""
    print("=" * 70)
    print("TAEKWONDO POINTS SIMULATOR")
    print("=" * 70)

    simulator = PointsSimulator()

    # Example simulation
    print("\nExample: Saudi Athlete M-68kg")
    print("-" * 70)

    # Define scenarios
    scenarios = [
        {
            'name': 'Full Attendance (All GP + Championships)',
            'competitions': [
                'Grand Prix Rome 2025',
                'Asian Championships 2025',
                'Grand Prix Manchester 2025',
                'World Championships 2025',
                'Grand Slam 2025',
                'Asian Championships 2026'
            ],
            'finishes': {
                'Grand Prix Rome 2025': 'r16',
                'Asian Championships 2025': 'bronze',
                'Grand Prix Manchester 2025': 'r16',
                'World Championships 2025': 'r32',
                'Grand Slam 2025': 'r16',
                'Asian Championships 2026': 'silver'
            }
        },
        {
            'name': 'Strategic (High-Value Only)',
            'competitions': [
                'Asian Championships 2025',
                'World Championships 2025',
                'Asian Championships 2026'
            ],
            'finishes': {
                'Asian Championships 2025': 'bronze',
                'World Championships 2025': 'r16',
                'Asian Championships 2026': 'silver'
            }
        },
        {
            'name': 'Minimum (Asian Focus)',
            'competitions': [
                'Asian Championships 2025',
                'Asian Championships 2026'
            ],
            'finishes': {
                'Asian Championships 2025': 'bronze',
                'Asian Championships 2026': 'silver'
            }
        }
    ]

    results = simulator.compare_scenarios(
        athlete_name="Mohammed Al-Zahrani",
        current_rank=15,
        current_points=150.0,
        scenarios=scenarios,
        weight_category="M-68kg"
    )

    print("\nCurrent: Rank #15 | 150.0 points")
    print("\n" + "=" * 70)

    for scenario in results:
        print(f"\n{scenario.name}")
        print("-" * 50)
        print(f"  Competitions: {len(scenario.competitions)}")
        print(f"  Total Cost: ${scenario.total_cost:,.0f}")
        print(f"  Projected Points: {scenario.projected_points:.1f}")
        print(f"  Projected World Rank: #{scenario.projected_world_rank}")
        print(f"  Projected Asian Rank: #{scenario.projected_asian_rank}")
        print(f"  Asian Games Status: {scenario.asian_games_status}")
        print(f"  Olympic Probability: {scenario.olympic_probability:.0f}%")
        print(f"  ROI Score: {scenario.roi_score:.1f}/100")

    # Optimal strategy
    print("\n" + "=" * 70)
    print("OPTIMAL STRATEGY (Budget: $25,000)")
    print("=" * 70)

    strategy = simulator.generate_optimal_strategy(
        athlete_name="Mohammed Al-Zahrani",
        current_rank=15,
        current_points=150.0,
        budget=25000,
        weight_category="M-68kg",
        target_event="asian_games"
    )

    print(f"\nRecommended Competitions:")
    for comp in strategy['recommended_competitions']:
        print(f"  - {comp}")
    print(f"\nTotal Cost: ${strategy['total_cost']:,.0f}")

    if strategy['recommendation']:
        rec = strategy['recommendation']
        print(f"\nRealistic Projection:")
        print(f"  Projected Rank: #{rec.projected_world_rank}")
        print(f"  Asian Games: {rec.asian_games_status}")
        print(f"  Olympic Probability: {rec.olympic_probability:.0f}%")

    # Competition calendar
    print("\n" + "=" * 70)
    print("COMPETITION CALENDAR")
    print("=" * 70)

    calendar_df = simulator.get_competition_calendar_df()
    print(calendar_df.to_string(index=False))


if __name__ == "__main__":
    main()
