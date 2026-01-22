"""
Streamlit Dashboard for Taekwondo Performance Analysis
Interactive visualizations and insights for Saudi Arabia team
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime
import json
import base64

from performance_analyzer import TaekwondoPerformanceAnalyzer
from models import WeightCategory
from advanced_kpis import AdvancedKPIAnalyzer
from ranking_tracker import RankingHistoryTracker
from config import ASIAN_RIVALS, ASIAN_COUNTRIES, ASIAN_GAMES_2026, LA_2028_OLYMPICS, DUAL_TRACK_MILESTONES

# Theme assets path
THEME_PATH = Path(r"C:\Users\l.gallagher\OneDrive - Team Saudi\Documents\Performance Analysis\Theme")

def get_image_base64(image_path):
    """Convert image to base64 for embedding in HTML"""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception:
        return None

# Team Saudi Theme Colors - Matching Logo Green
THEME_COLORS = {
    'primary_green': '#1E5631',      # Dark forest green (logo match)
    'secondary_green': '#2D5A3D',    # Lighter forest green
    'gold': '#a08e66',               # Gold accent
    'secondary_gold': '#9d8e65',
    'medal_gold': '#FFD700',
    'medal_silver': '#C0C0C0',
    'medal_bronze': '#CD7F32',
    'chart_palette': ['#1E5631', '#a08e66', '#2D5A3D', '#9d8e65', '#163d24', '#8a7a58']
}

# Page configuration
st.set_page_config(
    page_title="Saudi Taekwondo Analytics",
    page_icon="🥋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS - Saudi Olympic Committee Theme
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1E5631;
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #1E5631 0%, #2D5A3D 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .metric-card {
        background: linear-gradient(135deg, #1E5631 0%, #2D5A3D 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .ksa-teal { color: #1E5631; }
    .ksa-gold { color: #a08e66; }
    .gold { color: #FFD700; }
    .silver { color: #C0C0C0; }
    .bronze { color: #CD7F32; }
    .stButton>button {
        background-color: #1E5631;
        color: white;
        border-radius: 5px;
        border: none;
        padding: 0.5rem 1rem;
    }
    .stButton>button:hover {
        background-color: #2D5A3D;
    }
    /* Sidebar teal gradient styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1E5631 0%, #163d24 100%);
    }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
        color: white !important;
    }
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] span {
        color: white !important;
    }
    [data-testid="stSidebar"] .stRadio > label {
        color: white !important;
    }
    [data-testid="stSidebar"] [data-baseweb="radio"] {
        background-color: rgba(255,255,255,0.1);
        border-radius: 8px;
        padding: 8px;
        margin: 4px 0;
    }
    [data-testid="stSidebar"] [data-baseweb="radio"]:hover {
        background-color: rgba(255,255,255,0.2);
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_analyzer():
    """Load performance analyzer with caching"""
    return TaekwondoPerformanceAnalyzer(data_dir="data")


def main():
    """Main dashboard application"""

    # Load theme images
    banner_b64 = get_image_base64(THEME_PATH / "team_saudi_banner.jpg")
    logo_b64 = get_image_base64(THEME_PATH / "team_saudi_logo.jpg")

    # Header with Banner
    if banner_b64:
        st.markdown(f'''
        <div style="position: relative; border-radius: 12px; overflow: hidden; margin-bottom: 1.5rem;
             box-shadow: 0 8px 25px rgba(0, 113, 103, 0.25);">
            <img src="data:image/jpeg;base64,{banner_b64}" style="width: 100%; height: 180px; object-fit: cover; filter: brightness(0.7);">
            <div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; display: flex; align-items: center; justify-content: center;">
                <div style="text-align: center;">
                    <h1 style="color: white; font-size: 2.2rem; margin: 0; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);">
                        Saudi Arabia Taekwondo Analytics
                    </h1>
                    <p style="color: #a08e66; font-size: 1.1rem; margin: 0.5rem 0 0 0; text-shadow: 1px 1px 2px rgba(0,0,0,0.5);">
                        Performance Intelligence for Asian Games 2026 & LA 2028
                    </p>
                </div>
            </div>
            <div style="position: absolute; bottom: 0; left: 0; right: 0; height: 4px; background: linear-gradient(90deg, #1E5631 0%, #a08e66 50%, #163d24 100%);"></div>
        </div>
        ''', unsafe_allow_html=True)
    else:
        st.markdown('<div class="main-header">🥋 Saudi Arabia Taekwondo Performance Dashboard</div>',
                    unsafe_allow_html=True)
        st.markdown("---")

    # Initialize analyzer
    try:
        analyzer = load_analyzer()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.info("Please run the scraper first to collect data.")
        return

    # Sidebar with Logo
    if logo_b64:
        st.sidebar.markdown(f'''
        <div style="text-align: center; padding: 1rem 0; margin-bottom: 1rem;">
            <img src="data:image/jpeg;base64,{logo_b64}" style="width: 180px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.3);">
        </div>
        ''', unsafe_allow_html=True)

    st.sidebar.title("Navigation")

    # Group navigation by category
    st.sidebar.markdown("### HP Director Views")
    page = st.sidebar.radio(
        "Select View",
        [
            "Coaching Dashboard",
            "Team Overview",
            "Athlete Analysis",
            "Squad Management",
        ],
        label_visibility="collapsed"
    )

    st.sidebar.markdown("### Strategic Planning")
    page2 = st.sidebar.radio(
        "Strategic",
        [
            "Asian Games 2026",
            "LA 2028 Olympics",
            "Points Simulator",
            "Tactical Scouting",
        ],
        label_visibility="collapsed",
        key="strategic"
    )

    st.sidebar.markdown("### Analysis")
    page3 = st.sidebar.radio(
        "Analysis",
        [
            "Rival Comparison",
            "Medal Opportunities",
            "Ranking Trends",
            "Competition Planning",
        ],
        label_visibility="collapsed",
        key="analysis"
    )

    # Determine which page is selected
    if page2 and page2 != page:
        page = page2
    if page3 and page3 != page:
        page = page3

    # === COACHING DASHBOARD (HP Director View) ===
    if page == "Coaching Dashboard":
        show_coaching_dashboard(analyzer)

    # === TEAM OVERVIEW ===
    elif page == "Team Overview":
        show_team_overview(analyzer)

    # === ATHLETE ANALYSIS ===
    elif page == "Athlete Analysis":
        show_athlete_analysis(analyzer)

    # === SQUAD MANAGEMENT ===
    elif page == "Squad Management":
        show_squad_management(analyzer)

    # === RIVAL COMPARISON ===
    elif page == "Rival Comparison":
        show_rival_comparison(analyzer)

    # === MEDAL OPPORTUNITIES ===
    elif page == "Medal Opportunities":
        show_medal_opportunities(analyzer)

    # === RANKING TRENDS ===
    elif page == "Ranking Trends":
        show_ranking_trends(analyzer)

    # === COMPETITION PLANNING ===
    elif page == "Competition Planning":
        show_competition_planning(analyzer)

    # === ASIAN GAMES 2026 ===
    elif page == "Asian Games 2026":
        show_asian_games_command_center(analyzer)

    # === LA 2028 OLYMPICS ===
    elif page == "LA 2028 Olympics":
        show_olympic_qualification_tracker(analyzer)

    # === POINTS SIMULATOR ===
    elif page == "Points Simulator":
        show_points_simulator(analyzer)

    # === TACTICAL SCOUTING ===
    elif page == "Tactical Scouting":
        show_tactical_scouting(analyzer)


def show_team_overview(analyzer):
    """Display team overview dashboard"""
    st.header("🇸🇦 Saudi Arabia Team Overview")

    # Get team analytics
    team_analytics = analyzer.analyze_saudi_team()

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Active Athletes",
            value=team_analytics.total_active_athletes,
            delta=None
        )

    with col2:
        st.metric(
            label="Athletes in Top 50",
            value=team_analytics.athletes_in_top50,
            delta=None
        )

    with col3:
        st.metric(
            label="Total Medals (2024)",
            value=team_analytics.total_gold + team_analytics.total_silver + team_analytics.total_bronze,
            delta=None
        )

    with col4:
        st.metric(
            label="Olympic Qualifiers",
            value=team_analytics.olympic_qualifiers,
            delta=None
        )

    st.markdown("---")

    # Medal breakdown
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Medal Distribution")

        medal_data = pd.DataFrame({
            'Medal Type': ['Gold', 'Silver', 'Bronze'],
            'Count': [
                team_analytics.total_gold,
                team_analytics.total_silver,
                team_analytics.total_bronze
            ],
            'Color': ['#FFD700', '#C0C0C0', '#CD7F32']
        })

        fig = px.bar(
            medal_data,
            x='Medal Type',
            y='Count',
            color='Medal Type',
            color_discrete_map={
                'Gold': '#FFD700',
                'Silver': '#C0C0C0',
                'Bronze': '#CD7F32'
            },
            title="Medals Won"
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Ranking Distribution")

        ranking_dist = pd.DataFrame({
            'Category': ['Top 10', 'Top 50', 'Top 100', 'Other'],
            'Athletes': [
                team_analytics.athletes_in_top10,
                team_analytics.athletes_in_top50 - team_analytics.athletes_in_top10,
                team_analytics.athletes_in_top100 - team_analytics.athletes_in_top50,
                team_analytics.total_active_athletes - team_analytics.athletes_in_top100
            ]
        })

        fig = px.pie(
            ranking_dist,
            names='Category',
            values='Athletes',
            title="World Ranking Distribution",
            color_discrete_sequence=THEME_COLORS['chart_palette']
        )
        st.plotly_chart(fig, use_container_width=True)

    # Rankings table
    st.markdown("---")
    st.subheader("Current Saudi Rankings by Category")

    if analyzer.rankings_df is not None:
        # Handle both 'country' and 'MEMBER NATION' column names
        country_col = 'country' if 'country' in analyzer.rankings_df.columns else 'MEMBER NATION'
        saudi_rankings = analyzer.rankings_df[
            analyzer.rankings_df[country_col].str.upper().str.contains('KSA', na=False)
        ].copy()

        if not saudi_rankings.empty:
            # Clean up display
            display_cols = ['rank', 'athlete_name', 'weight_category', 'points']
            available_cols = [col for col in display_cols if col in saudi_rankings.columns]

            saudi_rankings = saudi_rankings[available_cols].sort_values(
                'rank' if 'rank' in available_cols else available_cols[0]
            )

            st.dataframe(
                saudi_rankings,
                use_container_width=True,
                height=400
            )
        else:
            st.info("No Saudi athlete rankings available. Run scraper to update data.")
    else:
        st.info("No ranking data available. Please run the scraper first.")


def show_athlete_analysis(analyzer):
    """Display individual athlete analysis"""
    st.header("👤 Individual Athlete Analysis")

    if analyzer.athletes_df is None or analyzer.athletes_df.empty:
        st.warning("No athlete data available. Please run the scraper first.")
        return

    # Athlete selector
    saudi_athletes = analyzer.athletes_df[
        analyzer.athletes_df['country'].str.upper().str.contains('KSA', na=False)
    ] if 'country' in analyzer.athletes_df.columns else analyzer.athletes_df

    if not saudi_athletes.empty:
        athlete_names = saudi_athletes['athlete_name'].unique() if 'athlete_name' in saudi_athletes.columns else []

        selected_athlete = st.selectbox(
            "Select Athlete",
            athlete_names if len(athlete_names) > 0 else ["No athletes found"]
        )

        if selected_athlete and selected_athlete != "No athletes found":
            # Get athlete metrics
            metrics = analyzer.analyze_saudi_athlete(selected_athlete)

            if metrics:
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("Recent Matches", metrics.recent_matches)

                with col2:
                    st.metric("Win Rate", f"{metrics.recent_win_rate:.1f}%")

                with col3:
                    st.metric("Recent Wins", metrics.recent_wins)

                with col4:
                    st.metric("Recent Losses", metrics.recent_losses)

                # Performance trend
                st.markdown("---")
                st.subheader("Performance Trend")

                # Placeholder for match history chart
                st.info("Match history visualization will be available after collecting more match data.")

            else:
                st.warning(f"No detailed metrics available for {selected_athlete}")
    else:
        st.info("No Saudi athletes found in database.")


def show_rival_comparison(analyzer):
    """Display comparison with rival nations"""
    st.header("🌍 International Benchmarking")

    # Get rival comparison
    rivals_df = analyzer.benchmark_against_rivals()

    if rivals_df.empty:
        st.warning("No ranking data available for comparison.")
        return

    # Display comparison table
    st.subheader("Performance vs Key Rivals")

    # Highlight Saudi row
    def highlight_saudi(row):
        if row['country'] == 'KSA':
            return [f'background-color: {THEME_COLORS["primary_teal"]}; color: white'] * len(row)
        return [''] * len(row)

    st.dataframe(
        rivals_df.style.apply(highlight_saudi, axis=1),
        use_container_width=True
    )

    # Visualization
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Athletes in Top 50")

        fig = px.bar(
            rivals_df,
            x='country',
            y='athletes_in_top50',
            title="Top 50 Ranked Athletes by Country",
            color='country',
            color_discrete_map={'KSA': THEME_COLORS['primary_teal']},
            color_discrete_sequence=THEME_COLORS['chart_palette']
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Average World Ranking")

        fig = px.bar(
            rivals_df,
            x='country',
            y='average_rank',
            title="Average Athlete Ranking (Lower is Better)",
            color='country',
            color_discrete_map={'KSA': THEME_COLORS['primary_teal']},
            color_discrete_sequence=THEME_COLORS['chart_palette']
        )
        fig.update_yaxes(autorange="reversed")  # Invert axis
        st.plotly_chart(fig, use_container_width=True)


def show_medal_opportunities(analyzer):
    """Display medal opportunity analysis with advanced KPI scoring"""
    st.header("🥇 Medal Opportunity Analysis")

    st.info("""
    **Research-Validated Scoring Formula:**
    Medal Opportunity Score = (Rank Score × 60%) + (Competition Density × 30%) + (Form × 10%)

    - **85-100**: CRITICAL - Immediate action required
    - **75-84**: HIGH - Prioritize resources
    - **60-74**: MEDIUM - Monitor closely
    - **<60**: DEVELOPMENT - Long-term investment
    """)

    opportunities = analyzer.identify_medal_opportunities()

    if not opportunities:
        st.info("""
        📋 **No medal opportunities identified yet.**

        This typically means weight category data is not available in the current rankings.

        **To enable medal opportunity analysis:**
        1. Run the comprehensive scraper to get all weight categories
        2. The scraper will collect rankings for all 16 weight categories (8 men, 8 women)

        ```bash
        python scraper_agent_complete.py
        ```
        """)
        return

    st.subheader("Top Medal Opportunities for Saudi Athletes")

    # Create DataFrame
    opp_df = pd.DataFrame(opportunities)

    # Color code by opportunity score
    def color_score(val):
        if val >= 85:
            return 'background-color: #d4edda; color: #155724; font-weight: bold'
        elif val >= 75:
            return 'background-color: #cfe2ff; color: #084298'
        elif val >= 60:
            return 'background-color: #fff3cd; color: #856404'
        else:
            return 'background-color: #f8d7da; color: #721c24'

    styled_df = opp_df.style.applymap(
        color_score,
        subset=['opportunity_score']
    )

    st.dataframe(styled_df, use_container_width=True, height=400)

    # Visualization
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Opportunity Score by Weight Category")

        fig = px.bar(
            opp_df.head(10),  # Top 10
            x='weight_category',
            y='opportunity_score',
            color='opportunity_score',
            title="Medal Opportunity Score (Top 10 Categories)",
            color_continuous_scale=[[0, THEME_COLORS['secondary_gold']], [1, THEME_COLORS['primary_teal']]],
            text='athlete_name'
        )
        fig.update_traces(textposition='outside')
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Priority Distribution")

        # Calculate priority levels
        priority_counts = {
            'CRITICAL (85+)': len([o for o in opportunities if o['opportunity_score'] >= 85]),
            'HIGH (75-84)': len([o for o in opportunities if 75 <= o['opportunity_score'] < 85]),
            'MEDIUM (60-74)': len([o for o in opportunities if 60 <= o['opportunity_score'] < 75]),
            'DEVELOPMENT (<60)': len([o for o in opportunities if o['opportunity_score'] < 60])
        }

        priority_df = pd.DataFrame({
            'Priority': list(priority_counts.keys()),
            'Count': list(priority_counts.values())
        })

        fig = px.pie(
            priority_df,
            names='Priority',
            values='Count',
            title="Athletes by Priority Level",
            color_discrete_sequence=[THEME_COLORS['primary_teal'], THEME_COLORS['gold'],
                                   THEME_COLORS['secondary_teal'], THEME_COLORS['secondary_gold']]
        )
        st.plotly_chart(fig, use_container_width=True)

    # Insights
    st.markdown("---")
    st.subheader("💡 Key Insights")

    top_opportunity = opportunities[0] if opportunities else None

    if top_opportunity:
        col1, col2, col3 = st.columns(3)

        with col1:
            st.success(f"**Best Opportunity:** {top_opportunity['weight_category']}")
            st.write(f"Athlete: {top_opportunity['athlete_name']}")

        with col2:
            st.info(f"**Current Rank:** #{top_opportunity['current_rank']}")
            st.write(f"Gap to medals: {top_opportunity['gap_to_medals']} positions")

        with col3:
            priority_color = "🔴" if top_opportunity['opportunity_score'] >= 85 else "🟡" if top_opportunity['opportunity_score'] >= 75 else "🟢"
            st.warning(f"**Opportunity Score:** {priority_color} {top_opportunity['opportunity_score']}/100")


def show_olympic_qualification_tracker(analyzer):
    """Display Olympic qualification probability tracking"""
    st.header("🏅 LA 2028 Olympic Qualification Tracker")

    # Initialize advanced KPI analyzer
    kpi_analyzer = AdvancedKPIAnalyzer(
        matches_df=analyzer.matches_df,
        rankings_df=analyzer.rankings_df
    )

    # LA 2028 countdown
    olympic_deadline = datetime(2028, 6, 30)
    days_remaining = (olympic_deadline - datetime.now()).days

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Days to Qualification Deadline", days_remaining,
                 delta=None, delta_color="off")

    with col2:
        st.metric("Target Deadline", "June 30, 2028",
                 delta=None, delta_color="off")

    with col3:
        years_remaining = days_remaining / 365
        st.metric("Years Remaining", f"{years_remaining:.1f}",
                 delta=None, delta_color="off")

    st.markdown("---")

    # Qualification paths
    st.subheader("📋 Qualification Pathways")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.success("""
        **Path A: Automatic Qualification**
        - Top 5 world ranking (Jan 2028)
        - Highest certainty
        - Requires consistent Grand Prix attendance
        """)

    with col2:
        st.info("""
        **Path B: Continental Qualification**
        - 2-3 spots per continent
        - Asian Championships performance
        - Backup to automatic qualification
        """)

    with col3:
        st.warning("""
        **Path C: Tripartite Commission**
        - Wild card invitation
        - Least reliable
        - Last resort option
        """)

    st.markdown("---")

    # Saudi athletes qualification analysis
    st.subheader("🇸🇦 Saudi Athletes Qualification Analysis")

    if analyzer.rankings_df is None or analyzer.rankings_df.empty:
        st.warning("No ranking data available for qualification analysis.")
        return

    # Handle both 'country' and 'MEMBER NATION' column names
    country_col = 'country' if 'country' in analyzer.rankings_df.columns else 'MEMBER NATION'
    saudi_rankings = analyzer.rankings_df[
        analyzer.rankings_df[country_col].str.upper().str.contains('KSA', na=False)
    ].copy()

    if saudi_rankings.empty:
        st.info("No Saudi athletes found in rankings. Please update data.")
        return

    # Convert rank to numeric
    saudi_rankings['rank'] = pd.to_numeric(saudi_rankings['rank'], errors='coerce')

    # Analyze each athlete
    qualification_data = []

    for _, athlete_row in saudi_rankings.iterrows():
        athlete_name = athlete_row['athlete_name']
        current_rank = athlete_row['rank']
        weight_category = athlete_row.get('weight_category', 'Unknown')

        if pd.notna(current_rank):
            # Use advanced KPI analyzer
            qual_analysis = kpi_analyzer.analyze_olympic_qualification_probability(
                athlete_name=athlete_name,
                current_rank=int(current_rank),
                weight_category=weight_category,
                recent_trend='stable'  # Default, could be enhanced with historical data
            )

            qualification_data.append({
                'Athlete': athlete_name,
                'Category': weight_category,
                'Current Rank': int(current_rank),
                'Target Rank': qual_analysis.target_rank,
                'Rank Gap': qual_analysis.rank_gap,
                'Qualification %': f"{qual_analysis.qualification_probability}%",
                'Primary Path': qual_analysis.path,
                'Days Remaining': qual_analysis.days_to_deadline
            })

    if qualification_data:
        qual_df = pd.DataFrame(qualification_data)

        # Sort by qualification probability
        qual_df['Qual_Numeric'] = qual_df['Qualification %'].str.rstrip('%').astype(float)
        qual_df = qual_df.sort_values('Qual_Numeric', ascending=False)
        qual_df = qual_df.drop('Qual_Numeric', axis=1)

        st.dataframe(qual_df, use_container_width=True, height=400)

        # Visualization
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Qualification Probability Distribution")

            prob_data = pd.DataFrame(qualification_data)
            prob_data['Probability'] = prob_data['Qualification %'].str.rstrip('%').astype(float)

            fig = px.bar(
                prob_data.sort_values('Probability', ascending=False).head(10),
                x='Athlete',
                y='Probability',
                color='Probability',
                title="Top 10 Athletes by Qualification Probability",
                color_continuous_scale=[[0, THEME_COLORS['secondary_gold']], [1, THEME_COLORS['primary_teal']]],
                labels={'Probability': 'Qualification Probability (%)'}
            )
            fig.update_xaxis(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Rank Gap Analysis")

            fig = px.scatter(
                prob_data,
                x='Current Rank',
                y='Rank Gap',
                size='Probability',
                color='Probability',
                hover_data=['Athlete', 'Category'],
                title="Current Rank vs Gap to Target",
                color_continuous_scale=[[0, THEME_COLORS['secondary_gold']], [1, THEME_COLORS['primary_teal']]]
            )
            st.plotly_chart(fig, use_container_width=True)

        # Strategic recommendations
        st.markdown("---")
        st.subheader("🎯 Strategic Recommendations")

        # Find top candidate
        top_candidate = prob_data.sort_values('Probability', ascending=False).iloc[0]

        col1, col2 = st.columns(2)

        with col1:
            st.success(f"""
            **Priority Athlete: {top_candidate['Athlete']}**
            - Category: {top_candidate['Category']}
            - Qualification Probability: {top_candidate['Qualification %']}
            - Current Rank: #{top_candidate['Current Rank']}
            - Target Rank: #{top_candidate['Target Rank']}

            **Action Plan:**
            - Dedicated coaching resources
            - ALL Grand Prix attendance
            - Asian Championships prioritization
            """)

        with col2:
            # Count athletes by pathway
            path_counts = prob_data['Primary Path'].value_counts()

            st.info(f"""
            **Team Qualification Landscape:**
            - Automatic qualification track: {path_counts.get('automatic', 0) + path_counts.get('automatic_attainable', 0)} athletes
            - Continental qualification track: {path_counts.get('continental', 0) + path_counts.get('continental_difficult', 0)} athletes
            - Total qualifying potential: {len(prob_data[prob_data['Probability'] > 20])} athletes

            **Next 90 Days:**
            - Update world rankings weekly
            - Monitor rival nations' movements
            - Optimize competition calendar
            """)


def show_ranking_trends(analyzer):
    """Display historical ranking trends using ranking tracker"""
    st.header("📈 Ranking History & Trend Analysis")

    # Initialize ranking tracker
    tracker = RankingHistoryTracker()

    st.info("""
    **Historical Ranking Analysis**
    This view shows ranking changes over time to identify trends, detect improvements/declines,
    and forecast future performance.
    """)

    # Check if historical data exists
    try:
        saudi_trends = tracker.get_saudi_ranking_trends(days=365)

        if saudi_trends.empty:
            st.warning("""
            No historical ranking data available yet.

            The system will automatically collect ranking snapshots daily.
            Check back after a few days to see trend analysis.

            To manually record current rankings, run: `python ranking_tracker.py`
            """)
            return

        st.success(f"Loaded {len(saudi_trends)} historical ranking records for Saudi athletes")

        # Display athletes with historical data
        athletes_with_history = saudi_trends['athlete_name'].unique()

        selected_athlete = st.selectbox(
            "Select Athlete for Trend Analysis",
            athletes_with_history
        )

        if selected_athlete:
            # Get athlete history
            athlete_history = tracker.get_athlete_history(selected_athlete, days=365)

            if not athlete_history.empty:
                # Calculate trend
                trend_analysis = tracker.calculate_trend(selected_athlete, days=180)

                # Display metrics
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("Current Rank", trend_analysis['current_rank'])

                with col2:
                    trend_emoji = "📈" if trend_analysis['trend'] == 'improving' else "📉" if trend_analysis['trend'] == 'declining' else "➡️"
                    st.metric("Trend", f"{trend_emoji} {trend_analysis['trend'].upper()}")

                with col3:
                    change_color = "normal" if trend_analysis['change'] == 0 else "inverse" if trend_analysis['change'] < 0 else "off"
                    st.metric("Rank Change (6mo)", trend_analysis['change'], delta_color=change_color)

                with col4:
                    st.metric("Data Points", trend_analysis['data_points'])

                # Visualization
                st.subheader(f"Ranking History: {selected_athlete}")

                # Convert date to datetime
                athlete_history['date'] = pd.to_datetime(athlete_history['date'])

                fig = px.line(
                    athlete_history.sort_values('date'),
                    x='date',
                    y='rank',
                    title=f"{selected_athlete} - World Ranking Over Time",
                    labels={'rank': 'World Rank', 'date': 'Date'},
                    markers=True,
                    color_discrete_sequence=[THEME_COLORS['primary_teal']]
                )

                # Invert y-axis (lower rank = better)
                fig.update_yaxes(autorange="reversed")

                # Add trend line
                fig.add_scatter(
                    x=athlete_history['date'],
                    y=athlete_history['rank'],
                    mode='lines',
                    name='Trend',
                    line=dict(dash='dash', color=THEME_COLORS['gold'])
                )

                st.plotly_chart(fig, use_container_width=True)

                # Points history if available
                if 'points' in athlete_history.columns:
                    st.subheader("Ranking Points History")

                    fig = px.line(
                        athlete_history.sort_values('date'),
                        x='date',
                        y='points',
                        title=f"{selected_athlete} - Ranking Points Over Time",
                        labels={'points': 'Ranking Points', 'date': 'Date'},
                        markers=True,
                        color_discrete_sequence=[THEME_COLORS['gold']]
                    )
                    st.plotly_chart(fig, use_container_width=True)

        # Team-level trends
        st.markdown("---")
        st.subheader("🇸🇦 Saudi Team Ranking Trends")

        # Group by date and calculate team metrics
        team_trends = saudi_trends.groupby('date').agg({
            'athlete_name': 'count',
            'rank': 'mean',
            'points': 'sum' if 'points' in saudi_trends.columns else 'count'
        }).reset_index()

        team_trends.columns = ['Date', 'Active Athletes', 'Average Rank', 'Total Points']
        team_trends['Date'] = pd.to_datetime(team_trends['Date'])

        col1, col2 = st.columns(2)

        with col1:
            fig = px.line(
                team_trends,
                x='Date',
                y='Active Athletes',
                title="Saudi Active Athletes Over Time",
                markers=True,
                color_discrete_sequence=[THEME_COLORS['primary_teal']]
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.line(
                team_trends,
                x='Date',
                y='Average Rank',
                title="Team Average Ranking Over Time",
                markers=True,
                color_discrete_sequence=[THEME_COLORS['gold']]
            )
            fig.update_yaxes(autorange="reversed")
            st.plotly_chart(fig, use_container_width=True)

        # Recent changes detection
        st.markdown("---")
        st.subheader("🔔 Recent Ranking Changes")

        recent_changes = tracker.detect_rank_changes(days=7, min_change=5)

        if recent_changes:
            changes_df = pd.DataFrame(recent_changes)

            # Filter for Saudi athletes
            saudi_changes = changes_df[
                changes_df['country'].str.upper().str.contains('KSA', na=False)
            ] if 'country' in changes_df.columns else changes_df

            if not saudi_changes.empty:
                st.dataframe(saudi_changes, use_container_width=True)
            else:
                st.info("No significant ranking changes for Saudi athletes in the past 7 days.")
        else:
            st.info("No significant ranking changes detected in the past 7 days.")

    except Exception as e:
        st.error(f"Error loading ranking history: {e}")
        st.info("""
        Historical ranking tracking is not yet active.

        To start tracking:
        1. Run `python ranking_tracker.py` to initialize the database
        2. The system will automatically record rankings daily
        3. Return here after a few days for trend analysis
        """)


def show_competition_planning(analyzer):
    """Display competition recommendations"""
    st.header("📅 Competition Planning & Strategy")

    recommendations = analyzer.generate_competition_recommendations()

    st.subheader("Recommended Competition Priorities")

    rec_df = pd.DataFrame(recommendations)

    # Display as cards
    for _, rec in rec_df.iterrows():
        with st.container():
            col1, col2, col3 = st.columns([3, 1, 1])

            with col1:
                st.markdown(f"### {rec['name']}")
                st.write(rec['reasoning'])

            with col2:
                st.metric("Priority", f"{rec['priority']}/100")

            with col3:
                st.metric("Ranking Points", rec['ranking_points'])

            st.markdown("---")

    # Strategic recommendations
    st.subheader("🎯 Strategic Recommendations")

    st.info("""
    **Priority Focus Areas:**
    1. **Olympic Qualification** - Ensure all top athletes participate in qualifying events
    2. **Grand Prix Series** - Maximize participation for ranking points and international exposure
    3. **Asian Championships** - Target regional dominance
    4. **Development Pipeline** - Enter emerging athletes in Open tournaments for experience
    """)

    # Calendar planning
    st.subheader("Competition Calendar Optimization")

    st.success("""
    **Optimal Competition Strategy:**
    - **Q1**: Focus on Olympic qualifiers and World Championships preparation
    - **Q2**: Grand Prix participation for ranking points accumulation
    - **Q3**: Continental championships for regional medals
    - **Q4**: Strategic recovery and training, select Open tournaments for emerging athletes
    """)


def show_asian_games_command_center(analyzer):
    """Display Asian Games 2026 Command Center - Continental focus for Nagoya"""
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1E5631 0%, #163d24 100%); padding: 1.5rem; border-radius: 10px; margin-bottom: 1.5rem;">
        <h1 style="color: white; margin: 0;">🏆 Asian Games 2026 Command Center</h1>
        <p style="color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0; font-size: 1.1rem;">
            Nagoya, Japan | September 19 - October 4, 2026
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Countdown
    asian_games_date = datetime.strptime(ASIAN_GAMES_2026['start_date'], '%Y-%m-%d')
    qualification_deadline = datetime.strptime(ASIAN_GAMES_2026['qualification_deadline'], '%Y-%m-%d')
    days_to_games = (asian_games_date - datetime.now()).days
    days_to_deadline = (qualification_deadline - datetime.now()).days

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Days to Asian Games", days_to_games, delta=None)

    with col2:
        st.metric("Days to Qualification Deadline", days_to_deadline,
                 delta="URGENT" if days_to_deadline < 180 else None,
                 delta_color="inverse" if days_to_deadline < 180 else "off")

    with col3:
        st.metric("Host Nation", "Japan 🇯🇵")

    with col4:
        st.metric("Weight Categories", "16 total")

    st.markdown("---")

    # Qualification Status Panel
    st.subheader("📋 KSA Qualification Status")

    if analyzer.rankings_df is None or analyzer.rankings_df.empty:
        st.warning("No ranking data available. Please run the scraper first.")
        return

    # Get Asian rankings
    rankings_df = analyzer.rankings_df.copy()

    # Normalize column names
    if 'MEMBER NATION' in rankings_df.columns:
        rankings_df = rankings_df.rename(columns={'MEMBER NATION': 'country', 'RANK': 'rank', 'NAME': 'athlete_name'})

    # Handle POINTS column
    if 'POINTS' in rankings_df.columns and 'points' not in rankings_df.columns:
        rankings_df = rankings_df.rename(columns={'POINTS': 'points'})

    # Ensure country column exists
    if 'country' not in rankings_df.columns:
        st.warning("Country column not found in rankings data. Please check data format.")
        return

    # Filter to Asian countries only
    asian_rankings = rankings_df[
        rankings_df['country'].str.upper().isin(ASIAN_COUNTRIES)
    ].copy()

    if asian_rankings.empty:
        st.info("No Asian athlete data found. Showing global rankings instead.")
        asian_rankings = rankings_df.copy()

    # Calculate Asian rank for each athlete
    asian_rankings['rank'] = pd.to_numeric(asian_rankings['rank'], errors='coerce')

    # Handle missing weight_category - if not present, calculate Asian rank globally
    if 'weight_category' in asian_rankings.columns:
        asian_rankings = asian_rankings.sort_values(['weight_category', 'rank'])
        asian_rankings['asian_rank'] = asian_rankings.groupby('weight_category').cumcount() + 1
    else:
        # No weight category - just sort by rank and assign global Asian rank
        asian_rankings = asian_rankings.sort_values('rank')
        asian_rankings['asian_rank'] = range(1, len(asian_rankings) + 1)
        st.info("📋 Note: Showing overall Asian rankings (weight category data not available). For category-specific rankings, run the full scraper.")

    # Get Saudi athletes
    saudi_asian = asian_rankings[
        asian_rankings['country'].str.upper().str.contains('KSA|SAUDI', na=False)
    ].copy()

    if saudi_asian.empty:
        st.info("No Saudi athletes found in Asian rankings.")
    else:
        # Qualification status logic (top 8 per category typically qualify)
        saudi_asian['qualification_status'] = saudi_asian['asian_rank'].apply(
            lambda x: '✅ Qualified' if x <= 8 else '🟡 Bubble (9-12)' if x <= 12 else '🔴 Outside'
        )

        # Display qualification table
        display_cols = ['athlete_name', 'weight_category', 'rank', 'asian_rank', 'qualification_status']
        available_cols = [c for c in display_cols if c in saudi_asian.columns]

        st.dataframe(
            saudi_asian[available_cols].rename(columns={
                'athlete_name': 'Athlete',
                'weight_category': 'Category',
                'rank': 'World Rank',
                'asian_rank': 'Asian Rank',
                'qualification_status': 'Status'
            }),
            use_container_width=True,
            hide_index=True
        )

        # Summary metrics
        qualified = len(saudi_asian[saudi_asian['asian_rank'] <= 8])
        bubble = len(saudi_asian[(saudi_asian['asian_rank'] > 8) & (saudi_asian['asian_rank'] <= 12)])
        outside = len(saudi_asian[saudi_asian['asian_rank'] > 12])

        col1, col2, col3 = st.columns(3)
        with col1:
            st.success(f"**Qualified:** {qualified} athletes")
        with col2:
            st.warning(f"**Bubble:** {bubble} athletes")
        with col3:
            st.error(f"**Outside:** {outside} athletes")

    st.markdown("---")

    # Asian Rivals Analysis
    st.subheader("🌏 Asian Rivals Comparison")

    rival_data = []
    for country in ASIAN_RIVALS:
        country_athletes = asian_rankings[
            asian_rankings['country'].str.upper().str.contains(country, na=False)
        ]

        if not country_athletes.empty:
            rival_data.append({
                'Country': country,
                'Total Athletes': len(country_athletes),
                'In Top 8 (Asian)': len(country_athletes[country_athletes['asian_rank'] <= 8]),
                'In Top 16 (Asian)': len(country_athletes[country_athletes['asian_rank'] <= 16]),
                'Best Asian Rank': int(country_athletes['asian_rank'].min()),
                'Avg Asian Rank': round(country_athletes['asian_rank'].mean(), 1)
            })

    # Add KSA
    if not saudi_asian.empty:
        rival_data.append({
            'Country': 'KSA 🇸🇦',
            'Total Athletes': len(saudi_asian),
            'In Top 8 (Asian)': len(saudi_asian[saudi_asian['asian_rank'] <= 8]),
            'In Top 16 (Asian)': len(saudi_asian[saudi_asian['asian_rank'] <= 16]),
            'Best Asian Rank': int(saudi_asian['asian_rank'].min()) if not saudi_asian.empty else 0,
            'Avg Asian Rank': round(saudi_asian['asian_rank'].mean(), 1) if not saudi_asian.empty else 0
        })

    if rival_data:
        rivals_df = pd.DataFrame(rival_data)
        rivals_df = rivals_df.sort_values('In Top 8 (Asian)', ascending=False)

        # Highlight KSA row
        def highlight_ksa(row):
            if 'KSA' in str(row['Country']):
                return ['background-color: rgba(0, 113, 103, 0.2); font-weight: bold'] * len(row)
            return [''] * len(row)

        st.dataframe(
            rivals_df.style.apply(highlight_ksa, axis=1),
            use_container_width=True,
            hide_index=True
        )

        # Visualization
        col1, col2 = st.columns(2)

        with col1:
            fig = px.bar(
                rivals_df,
                x='Country',
                y='In Top 8 (Asian)',
                title="Athletes in Qualifying Position (Top 8 Asian)",
                color='In Top 8 (Asian)',
                color_continuous_scale=[[0, THEME_COLORS['secondary_gold']], [1, THEME_COLORS['primary_teal']]]
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.bar(
                rivals_df.sort_values('Avg Asian Rank'),
                x='Country',
                y='Avg Asian Rank',
                title="Average Asian Rank (Lower is Better)",
                color='Avg Asian Rank',
                color_continuous_scale=[[0, THEME_COLORS['primary_teal']], [1, THEME_COLORS['secondary_gold']]]
            )
            fig.update_yaxes(autorange="reversed")
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Category-by-Category Analysis
    st.subheader("📊 Medal Opportunities by Category")

    st.info("""
    **Medal Probability Legend:**
    - 🥇 **High** (Asian Rank 1-3): Strong medal chance
    - 🥈 **Medium** (Asian Rank 4-6): Potential medal with good performance
    - 🥉 **Low** (Asian Rank 7-10): Needs breakthrough performance
    """)

    if not saudi_asian.empty:
        category_analysis = []

        for _, athlete in saudi_asian.iterrows():
            asian_rank = athlete['asian_rank']

            if asian_rank <= 3:
                medal_prob = '🥇 High'
                color = 'success'
            elif asian_rank <= 6:
                medal_prob = '🥈 Medium'
                color = 'warning'
            elif asian_rank <= 10:
                medal_prob = '🥉 Low'
                color = 'info'
            else:
                medal_prob = '⬜ Development'
                color = 'secondary'

            category_analysis.append({
                'Category': athlete['weight_category'],
                'Athlete': athlete['athlete_name'],
                'Asian Rank': int(asian_rank),
                'World Rank': int(athlete['rank']) if pd.notna(athlete['rank']) else 'N/A',
                'Medal Probability': medal_prob,
                'Gap to Medal': max(0, int(asian_rank) - 3)
            })

        analysis_df = pd.DataFrame(category_analysis)
        analysis_df = analysis_df.sort_values('Asian Rank')

        st.dataframe(analysis_df, use_container_width=True, hide_index=True)

    # Key Competitions
    st.markdown("---")
    st.subheader("🗓️ Key Qualifying Events")

    events = [
        {'Event': 'Asian Championships 2025', 'Date': 'May 2025', 'Importance': '⭐⭐⭐ Critical', 'Points': 'High'},
        {'Event': 'Asian Open Series', 'Date': 'Throughout 2025-2026', 'Importance': '⭐⭐ Important', 'Points': 'Medium'},
        {'Event': 'Asian Championships 2026', 'Date': 'May 2026', 'Importance': '⭐⭐⭐ Critical', 'Points': 'High'},
        {'Event': 'Asian Qualification Tournament', 'Date': 'June 2026', 'Importance': '⭐⭐⭐ Critical', 'Points': 'Final Chance'},
    ]

    st.dataframe(pd.DataFrame(events), use_container_width=True, hide_index=True)

    # Strategic Recommendations
    st.markdown("---")
    st.subheader("🎯 Strategic Recommendations for Asian Games")

    col1, col2 = st.columns(2)

    with col1:
        st.success("""
        **Priority Actions:**
        1. Focus on athletes in Asian Rank 4-8 (bubble positions)
        2. Attend ALL Asian Open events for ranking points
        3. Study Japanese opponents (host nation advantage)
        4. Peak training cycle for September 2026
        """)

    with col2:
        st.info("""
        **Key Rivals to Monitor:**
        - 🇰🇷 South Korea: Traditional powerhouse
        - 🇮🇷 Iran: Strong in men's categories
        - 🇨🇳 China: Deep talent pool
        - 🇯🇵 Japan: Home advantage in 2026
        """)


def show_points_simulator(analyzer):
    """Display Points Simulator - What-if scenario planning"""
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1E5631 0%, #163d24 100%); padding: 1.5rem; border-radius: 10px; margin-bottom: 1.5rem;">
        <h1 style="color: white; margin: 0;">📊 Points Simulator</h1>
        <p style="color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0;">
            Model "what if" scenarios for competition attendance decisions
        </p>
    </div>
    """, unsafe_allow_html=True)

    try:
        from points_simulator import PointsSimulator, SimulationScenario, UPCOMING_COMPETITIONS

        simulator = PointsSimulator()

        # Get available competitions using the correct method
        available_competitions = simulator.get_available_competitions()

        # Athlete selection
        col1, col2 = st.columns([1, 2])

        with col1:
            st.subheader("Athlete Setup")

            athlete_name = st.text_input("Athlete Name", value="Saudi Athlete")
            current_points = st.number_input("Current Points", min_value=0.0, value=100.0, step=10.0)
            current_rank = st.number_input("Current World Rank", min_value=1, value=25, step=1)

            weight_category = st.selectbox(
                "Weight Category",
                options=['-54kg', '-58kg', '-63kg', '-68kg', '-74kg', '-80kg', '-87kg', '+87kg',
                         '-46kg', '-49kg', '-53kg', '-57kg', '-62kg', '-67kg', '-73kg', '+73kg']
            )

            expected_finish = st.selectbox(
                "Expected Average Finish",
                options=['gold', 'silver', 'bronze', 'r16', 'r32'],
                index=2  # Default to bronze
            )

        with col2:
            st.subheader("Select Competitions to Simulate")

            if available_competitions:
                selected_comp_names = []
                for comp in available_competitions[:10]:  # Show next 10 competitions
                    col_check, col_name, col_pts = st.columns([1, 3, 1])
                    with col_check:
                        selected = st.checkbox("", key=f"comp_{comp.name}", value=False)
                    with col_name:
                        st.write(f"**{comp.name}** ({comp.date})")
                    with col_pts:
                        st.write(f"G: {comp.points_gold}pts")

                    if selected:
                        selected_comp_names.append(comp.name)
            else:
                st.info("No upcoming competitions found in calendar.")
                selected_comp_names = []

        st.markdown("---")

        # Competition Calendar DataFrame
        st.subheader("📅 Full Competition Calendar")
        calendar_df = simulator.get_competition_calendar_df()
        st.dataframe(calendar_df, use_container_width=True, hide_index=True)

        st.markdown("---")

        # Run simulation
        if st.button("🎯 Run Simulation", type="primary"):
            if selected_comp_names:
                # Create expected finishes dict
                expected_finishes = {name: expected_finish for name in selected_comp_names}

                # Run simulation using correct method signature
                result = simulator.simulate_scenario(
                    athlete_name=athlete_name,
                    current_rank=current_rank,
                    current_points=current_points,
                    competitions=selected_comp_names,
                    expected_finishes=expected_finishes,
                    weight_category=weight_category
                )

                # Display results
                st.subheader("Simulation Results")

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    points_gained = result.projected_points - current_points
                    st.metric(
                        "Projected Points",
                        f"{result.projected_points:.1f}",
                        f"+{points_gained:.1f}"
                    )

                with col2:
                    rank_change = current_rank - result.projected_world_rank
                    st.metric(
                        "Projected Rank",
                        f"#{result.projected_world_rank}",
                        f"+{rank_change}" if rank_change > 0 else str(rank_change)
                    )

                with col3:
                    st.metric(
                        "Total Cost",
                        f"${result.total_cost:,.0f}",
                        f"{len(selected_comp_names)} events"
                    )

                with col4:
                    st.metric(
                        "ROI Score",
                        f"{result.roi_score:.0f}/100",
                        "Good" if result.roi_score >= 70 else "Fair"
                    )

                # Asian Games & Olympic Status
                col1, col2 = st.columns(2)
                with col1:
                    ag_color = "#28a745" if result.asian_games_status == "QUALIFIED" else "#ffc107" if result.asian_games_status == "BUBBLE" else "#dc3545"
                    st.markdown(f"""
                    <div style="background: {ag_color}; padding: 1rem; border-radius: 8px; text-align: center;">
                        <p style="color: white; margin: 0; font-size: 0.9rem;">Asian Games 2026</p>
                        <p style="color: white; margin: 0; font-size: 1.3rem; font-weight: bold;">
                            {result.asian_games_status} (Asian #{result.projected_asian_rank})
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

                with col2:
                    oly_color = "#1E5631" if result.olympic_probability >= 0.5 else "#a08e66" if result.olympic_probability >= 0.25 else "#6c757d"
                    st.markdown(f"""
                    <div style="background: {oly_color}; padding: 1rem; border-radius: 8px; text-align: center;">
                        <p style="color: white; margin: 0; font-size: 0.9rem;">LA 2028 Probability</p>
                        <p style="color: white; margin: 0; font-size: 1.3rem; font-weight: bold;">
                            {result.olympic_probability:.0%}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

                # Detailed breakdown
                st.subheader("Competition Breakdown")
                breakdown_data = []
                for comp_name in selected_comp_names:
                    comp = simulator.competitions.get(comp_name)
                    if comp:
                        finish_points = simulator.calculate_points_for_finish(comp_name, expected_finish)
                        breakdown_data.append({
                            'Competition': comp.name,
                            'Date': comp.date,
                            'Tier': comp.tier.replace('_', ' ').title(),
                            'Expected Finish': expected_finish.title(),
                            'Points': finish_points,
                            'Cost': f"${comp.estimated_cost_usd:,}"
                        })

                st.dataframe(pd.DataFrame(breakdown_data), use_container_width=True, hide_index=True)

                # Recommendation
                if result.roi_score >= 80:
                    st.success("**Recommendation:** Strongly recommend attending these competitions. High ROI and good qualification impact.")
                elif result.roi_score >= 60:
                    st.info("**Recommendation:** Good value - consider attending based on athlete's form and budget.")
                else:
                    st.warning("**Recommendation:** Review alternatives for better ROI. Consider prioritizing higher-value events.")

            else:
                st.warning("Please select at least one competition to simulate.")

    except ImportError as e:
        st.warning(f"Points simulator module not available: {e}")
        st.info("Run: `pip install -r requirements.txt` to install dependencies.")


def show_tactical_scouting(analyzer):
    """Display Tactical Scouting Hub"""
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1E5631 0%, #163d24 100%); padding: 1.5rem; border-radius: 10px; margin-bottom: 1.5rem;">
        <h1 style="color: white; margin: 0;">🎯 Tactical Scouting Hub</h1>
        <p style="color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0;">
            Deep opponent intelligence for match preparation
        </p>
    </div>
    """, unsafe_allow_html=True)

    try:
        from scouting_manager import ScoutingManager, render_opponent_card, ThreatLevel

        scout = ScoutingManager()

        # Navigation tabs
        tab1, tab2, tab3 = st.tabs(["🔍 Opponent Search", "📊 Category Rankings", "📋 Scouting Report"])

        with tab1:
            st.subheader("Search Opponent Profile")

            col1, col2 = st.columns([2, 1])
            with col1:
                opponent_name = st.text_input("Opponent Name", placeholder="Enter athlete name...")
            with col2:
                country_filter = st.selectbox(
                    "Country (optional)",
                    options=['Any', 'KOR', 'IRI', 'CHN', 'JPN', 'JOR', 'TUR', 'GBR', 'FRA', 'MEX', 'UZB', 'THA', 'KAZ']
                )

            if opponent_name:
                with st.spinner("Loading opponent profile..."):
                    country = None if country_filter == 'Any' else country_filter
                    profile = scout.get_opponent_profile(athlete_name=opponent_name, country=country)

                    if profile:
                        st.markdown(render_opponent_card(profile), unsafe_allow_html=True)

                        # Head-to-head section
                        st.markdown("---")
                        st.subheader("Head-to-Head Analysis")

                        ksa_athlete = st.text_input("KSA Athlete for H2H", placeholder="Enter KSA athlete name...")

                        if ksa_athlete:
                            h2h = scout.head_to_head(ksa_athlete, opponent_name)
                            if h2h and h2h.total_meetings > 0:
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric(f"{ksa_athlete} Wins", h2h.athlete1_wins)
                                with col2:
                                    st.metric("Meetings", h2h.total_meetings)
                                with col3:
                                    st.metric(f"{opponent_name} Wins", h2h.athlete2_wins)

                                # Match history
                                if h2h.matches:
                                    st.write("**Match History:**")
                                    for match in h2h.matches[-5:]:  # Last 5 matches
                                        result_color = "#28a745" if match.result == 'W' else "#dc3545"
                                        st.markdown(f"- <span style='color:{result_color}'>{match.result}</span> {match.competition} ({match.date}) - {match.score}",
                                                  unsafe_allow_html=True)
                            else:
                                st.info("No head-to-head matches found between these athletes.")
                    else:
                        st.warning(f"No profile found for '{opponent_name}'")

        with tab2:
            st.subheader("Category Rankings")

            weight_category = st.selectbox(
                "Select Weight Category",
                options=['-54kg', '-58kg', '-63kg', '-68kg', '-74kg', '-80kg', '-87kg', '+87kg',
                         '-46kg', '-49kg', '-53kg', '-57kg', '-62kg', '-67kg', '-73kg', '+73kg']
            )

            col1, col2 = st.columns([1, 1])
            with col1:
                show_asian_only = st.checkbox("Asian athletes only", value=False)
            with col2:
                limit = st.slider("Show top", min_value=5, max_value=30, value=15)

            rankings = scout.get_category_rankings(weight_category, limit=limit * 2)

            if rankings:
                # Filter to Asian if selected
                if show_asian_only:
                    from config import ASIAN_COUNTRIES
                    rankings = [r for r in rankings if scout._get_country_code(r.get('country', r.get('MEMBER NATION', ''))) in ASIAN_COUNTRIES]

                rankings = rankings[:limit]

                # Display as cards
                for i, athlete in enumerate(rankings, 1):
                    name = athlete.get('athlete_name', athlete.get('NAME', 'Unknown'))
                    country = athlete.get('country', athlete.get('MEMBER NATION', '?'))
                    rank = athlete.get('rank', athlete.get('RANK', '?'))
                    points = athlete.get('points', athlete.get('POINTS', 0))

                    country_code = scout._get_country_code(country)

                    # Color code by threat level - Team Saudi palette
                    if rank <= 5:
                        bg_color = "rgba(220, 53, 69, 0.1)"  # Critical - red tint
                        border_color = "#dc3545"
                    elif rank <= 10:
                        bg_color = "rgba(160, 142, 102, 0.15)"  # High - gold tint
                        border_color = "#a08e66"
                    else:
                        bg_color = "rgba(0, 113, 103, 0.08)"  # Normal - teal tint
                        border_color = "#1E5631"

                    st.markdown(f"""
                    <div style="background: {bg_color}; border-left: 4px solid {border_color}; padding: 10px 15px; margin: 5px 0; border-radius: 5px;">
                        <strong>#{rank}</strong> | {name} ({country_code}) | {points} pts
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No rankings data available for this category.")

        with tab3:
            st.subheader("Generate Scouting Report")

            col1, col2 = st.columns(2)
            with col1:
                athlete_name = st.text_input("KSA Athlete", placeholder="Enter athlete name for report...")
            with col2:
                report_category = st.selectbox(
                    "Weight Category",
                    options=['-54kg', '-58kg', '-63kg', '-68kg', '-74kg', '-80kg', '-87kg', '+87kg',
                             '-46kg', '-49kg', '-53kg', '-57kg', '-62kg', '-67kg', '-73kg', '+73kg'],
                    key="report_category"
                )

            competition = st.text_input("Target Competition", value="Asian Games 2026")

            if st.button("Generate Scouting Report", type="primary"):
                if athlete_name:
                    with st.spinner("Generating scouting report..."):
                        report = scout.generate_scouting_report(
                            athlete_name=athlete_name,
                            weight_category=report_category,
                            competition=competition
                        )

                        st.success(f"Report generated for {athlete_name}")

                        # Medal probability
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Medal Probability", f"{report.medal_probability:.0%}")
                        with col2:
                            st.metric("Gold Probability", f"{report.gold_probability:.0%}")

                        # Key threats
                        if report.key_threats:
                            st.subheader("Key Threats")
                            for threat in report.key_threats:
                                st.markdown(f"- {threat}")

                        # Likely opponents
                        if report.likely_opponents:
                            st.subheader(f"Top Opponents ({len(report.likely_opponents)})")
                            for opp in report.likely_opponents[:5]:
                                with st.expander(f"{opp.name} ({opp.country_code}) - Rank #{opp.world_rank}"):
                                    st.markdown(render_opponent_card(opp), unsafe_allow_html=True)

                        # Tactical recommendations
                        if report.recommendations:
                            st.subheader("Tactical Recommendations")
                            for rec in report.recommendations:
                                st.info(rec)

                        # Export option
                        if st.button("Export Report to JSON"):
                            output_path = scout.export_scouting_report(report)
                            st.success(f"Report saved to: {output_path}")
                else:
                    st.warning("Please enter an athlete name.")

    except ImportError as e:
        st.warning(f"Scouting manager module not available: {e}")

        # Fallback to head-to-head module
        st.markdown("---")
        st.subheader("Head-to-Head Analysis (Basic)")

        try:
            from head_to_head import HeadToHeadAnalyzer
            h2h_analyzer = HeadToHeadAnalyzer(data_dir="data")

            if h2h_analyzer.matches_df is not None and not h2h_analyzer.matches_df.empty:
                st.success(f"Loaded {len(h2h_analyzer.matches_df):,} matches for head-to-head analysis")
                opponent_name = st.text_input("Search for opponent:", placeholder="Enter opponent name...")
                if opponent_name:
                    st.write(f"Searching for matches involving: {opponent_name}")
            else:
                st.warning("No match data available for head-to-head analysis.")
        except ImportError:
            st.warning("Head-to-head module not available.")


def show_coaching_dashboard(analyzer):
    """Display HP Director Coaching Dashboard - Executive overview for leadership."""
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1E5631 0%, #163d24 100%); padding: 1.5rem; border-radius: 10px; margin-bottom: 1.5rem;">
        <h1 style="color: white; margin: 0;">HP Director Dashboard</h1>
        <p style="color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0;">
            Executive overview for High Performance leadership decisions
        </p>
    </div>
    """, unsafe_allow_html=True)

    try:
        from coaching_insights import CoachingInsights, render_squad_card, render_competition_card

        insights = CoachingInsights()

        # Team Saudi Brand Colors
        TEAL_PRIMARY = '#1E5631'
        GOLD_ACCENT = '#a08e66'
        TEAL_DARK = '#163d24'
        TEAL_LIGHT = '#009688'

        # Key metrics row
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, {TEAL_PRIMARY} 0%, {TEAL_DARK} 100%); padding: 1.2rem; border-radius: 10px; text-align: center;">
                <p style="color: rgba(255,255,255,0.8); margin: 0; font-size: 0.85rem;">Days to Asian Games</p>
                <p style="color: white; margin: 0.25rem 0 0 0; font-size: 2rem; font-weight: bold;">{insights.days_to_asian_games}</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div style="background: {GOLD_ACCENT}; padding: 1.2rem; border-radius: 10px; text-align: center;">
                <p style="color: rgba(255,255,255,0.8); margin: 0; font-size: 0.85rem;">Days to LA 2028</p>
                <p style="color: white; margin: 0.25rem 0 0 0; font-size: 2rem; font-weight: bold;">{insights.days_to_olympics}</p>
            </div>
            """, unsafe_allow_html=True)

        # Get squad overview
        squad = insights.get_squad_overview()

        with col3:
            st.markdown(f"""
            <div style="background: {TEAL_LIGHT}; padding: 1.2rem; border-radius: 10px; text-align: center;">
                <p style="color: rgba(255,255,255,0.8); margin: 0; font-size: 0.85rem;">Squad Ready</p>
                <p style="color: white; margin: 0.25rem 0 0 0; font-size: 2rem; font-weight: bold;">{squad.ready_count}/{squad.total_athletes}</p>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            st.markdown(f"""
            <div style="background: {TEAL_PRIMARY}; padding: 1.2rem; border-radius: 10px; text-align: center;">
                <p style="color: rgba(255,255,255,0.8); margin: 0; font-size: 0.85rem;">Avg Form Score</p>
                <p style="color: white; margin: 0.25rem 0 0 0; font-size: 2rem; font-weight: bold;">{squad.avg_form_score:.0f}</p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # Two-column layout: Weekly Report + Priority Actions
        col1, col2 = st.columns([3, 2])

        with col1:
            st.subheader("Weekly Executive Summary")

            report = insights.generate_weekly_report()

            # Highlights
            st.markdown("**Key Highlights**")
            for h in report.key_highlights:
                st.success(h)

            # Concerns
            if report.concerns:
                st.markdown("**Attention Required**")
                for c in report.concerns:
                    st.warning(c)

            # Action items
            st.markdown("**Action Items**")
            for a in report.action_items:
                st.checkbox(a, key=f"action_{a[:20]}")

        with col2:
            st.subheader("Upcoming Competitions")

            comps = insights.get_competition_opportunities(months_ahead=4)
            for comp in comps[:3]:
                st.markdown(render_competition_card(comp), unsafe_allow_html=True)

        st.markdown("---")

        # Target tracking
        st.subheader("Target Tracking")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Asian Games 2026 Targets", squad.asian_games_targets, "athletes")

        with col2:
            st.metric("LA 2028 Olympics Targets", squad.olympics_targets, "athletes")

        with col3:
            budget = insights.generate_competition_calendar().get('budget_estimate', 0)
            st.metric("Est. Competition Budget", f"${budget:,.0f}", "next 12 months")

        # Development pathways
        st.markdown("---")
        st.subheader("Development Pathways")

        pathways = insights.get_development_pathways()

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown("**Medal Contenders**")
            st.markdown(f"_{len(pathways['medal_contenders'])} athletes_")
            for a in pathways['medal_contenders'][:3]:
                st.write(f"- {a.name} (#{a.world_rank})")

        with col2:
            st.markdown("**Qualification Track**")
            st.markdown(f"_{len(pathways['qualification_track'])} athletes_")
            for a in pathways['qualification_track'][:3]:
                st.write(f"- {a.name} (#{a.world_rank})")

        with col3:
            st.markdown("**Development Pool**")
            st.markdown(f"_{len(pathways['development_pool'])} athletes_")
            for a in pathways['development_pool'][:3]:
                st.write(f"- {a.name} (#{a.world_rank})")

        with col4:
            st.markdown("**Emerging Talent**")
            st.markdown(f"_{len(pathways['emerging_talent'])} athletes_")
            for a in pathways['emerging_talent'][:3]:
                st.write(f"- {a.name} (#{a.world_rank})")

    except ImportError as e:
        st.warning(f"Coaching insights module not available: {e}")
        st.info("The coaching_insights.py module provides HP Director focused analytics.")


def show_squad_management(analyzer):
    """Display Squad Management view for coaches."""
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1E5631 0%, #163d24 100%); padding: 1.5rem; border-radius: 10px; margin-bottom: 1.5rem;">
        <h1 style="color: white; margin: 0;">Squad Management</h1>
        <p style="color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0;">
            Individual athlete tracking, readiness, and development planning
        </p>
    </div>
    """, unsafe_allow_html=True)

    try:
        from coaching_insights import CoachingInsights, render_squad_card

        insights = CoachingInsights()
        squad = insights.get_squad_overview()

        # Filter controls
        col1, col2, col3 = st.columns(3)

        with col1:
            priority_filter = st.selectbox(
                "Priority Level",
                options=['All', 'A - Top Priority', 'B - Development', 'C - Emerging']
            )

        with col2:
            readiness_filter = st.selectbox(
                "Readiness Status",
                options=['All', 'Ready', 'Caution', 'Unavailable']
            )

        with col3:
            category_filter = st.selectbox(
                "Weight Category",
                options=['All'] + [a.weight_category for a in squad.athletes if a.weight_category]
            )

        st.markdown("---")

        # Apply filters
        filtered_athletes = squad.athletes

        if priority_filter != 'All':
            priority_code = priority_filter[0]  # Extract 'A', 'B', or 'C'
            filtered_athletes = [a for a in filtered_athletes if a.priority_level == priority_code]

        if readiness_filter != 'All':
            filtered_athletes = [a for a in filtered_athletes if a.readiness == readiness_filter]

        if category_filter != 'All':
            filtered_athletes = [a for a in filtered_athletes if a.weight_category == category_filter]

        # Display athletes
        st.subheader(f"Athletes ({len(filtered_athletes)})")

        if filtered_athletes:
            # Sort by priority then rank
            filtered_athletes.sort(key=lambda a: (a.priority_level, a.world_rank))

            for athlete in filtered_athletes:
                st.markdown(render_squad_card(athlete), unsafe_allow_html=True)

                # Expandable section for training recommendations
                with st.expander(f"Training Recommendations for {athlete.name}"):
                    recs = insights.get_training_recommendations(athlete.name)

                    if 'error' not in recs:
                        col1, col2 = st.columns(2)

                        with col1:
                            st.markdown("**Focus Areas:**")
                            for area in recs.get('focus_areas', []):
                                st.write(f"- {area}")

                            st.markdown("**Competition Strategy:**")
                            st.info(recs.get('competition_strategy', 'No specific strategy'))

                        with col2:
                            st.markdown("**Technical Priorities:**")
                            for tech in recs.get('technical_priorities', []):
                                st.write(f"- {tech}")

                            st.markdown("**Mental Priorities:**")
                            for mental in recs.get('mental_priorities', []):
                                st.write(f"- {mental}")
                    else:
                        st.warning("Could not generate recommendations")
        else:
            st.info("No athletes match the selected filters.")

        # Summary statistics
        st.markdown("---")
        st.subheader("Squad Summary")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Athletes", squad.total_athletes)

        with col2:
            priority_a = len([a for a in squad.athletes if a.priority_level == 'A'])
            st.metric("Priority A", priority_a)

        with col3:
            st.metric("Competition Ready", squad.ready_count)

        with col4:
            if squad.concerns:
                st.metric("Requiring Attention", len(squad.concerns))
            else:
                st.metric("Requiring Attention", 0)

    except ImportError as e:
        st.warning(f"Squad management module not available: {e}")
        st.info("The coaching_insights.py module provides squad management analytics.")


if __name__ == "__main__":
    main()
