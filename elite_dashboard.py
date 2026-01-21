"""
Elite Taekwondo Performance Dashboard
World-class analytics platform for high-performance taekwondo analysis
Built by experts in Streamlit, Taekwondo, and Sports Performance Analysis
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import os
from pathlib import Path
from datetime import datetime
import numpy as np
from collections import defaultdict

# ==================== PAGE CONFIGURATION ====================
st.set_page_config(
    page_title="Elite Taekwondo Analytics | Saudi Arabia",
    page_icon="🥋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CUSTOM STYLING ====================
st.markdown("""
<style>
    /* Main theme colors */
    :root {
        --saudi-green: #006C35;
        --saudi-gold: #FFD700;
        --text-dark: #1a1a1a;
        --background: #f8f9fa;
    }

    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #006C35 0%, #00943D 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 8px 16px rgba(0,108,53,0.2);
        text-align: center;
    }

    .main-header h1 {
        color: white;
        font-size: 3rem;
        font-weight: 800;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }

    .main-header p {
        color: rgba(255,255,255,0.95);
        font-size: 1.2rem;
        margin-top: 0.5rem;
    }

    /* Metric cards */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 5px solid #006C35;
        box-shadow: 0 4px 8px rgba(0,0,0,0.08);
        transition: transform 0.2s, box-shadow 0.2s;
    }

    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 16px rgba(0,0,0,0.12);
    }

    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #006C35;
        margin: 0;
    }

    .metric-label {
        font-size: 0.9rem;
        color: #6c757d;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 0.5rem;
    }

    /* Medal colors */
    .gold { color: #FFD700; font-weight: bold; }
    .silver { color: #C0C0C0; font-weight: bold; }
    .bronze { color: #CD7F32; font-weight: bold; }

    /* Highlight Saudi */
    .highlight-saudi {
        background-color: rgba(0,108,53,0.1) !important;
        font-weight: 600;
    }

    /* Section headers */
    .section-header {
        color: #006C35;
        font-size: 1.8rem;
        font-weight: 700;
        margin-top: 2rem;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 3px solid #006C35;
    }

    /* Info boxes */
    .info-box {
        background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #2e7d32;
        margin: 1rem 0;
    }

    .warning-box {
        background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #f57c00;
        margin: 1rem 0;
    }

    /* Streamlit overrides */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }

    .stTabs [data-baseweb="tab"] {
        font-size: 1.1rem;
        font-weight: 600;
        padding: 1rem 2rem;
    }

    /* Data tables */
    .dataframe {
        font-size: 0.95rem;
    }

    .dataframe thead tr th {
        background-color: #006C35 !important;
        color: white !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        font-size: 0.85rem;
        letter-spacing: 0.5px;
    }
</style>
""", unsafe_allow_html=True)

# ==================== DATA LOADING FUNCTIONS ====================

@st.cache_data(ttl=600)
def load_olympic_data():
    """Load all Olympic Games data"""
    olympics = [
        ('sydney-2000-og', 'Sydney 2000'),
        ('athens-2004-og', 'Athens 2004'),
        ('beijing-2008-og', 'Beijing 2008'),
        ('london-2012-og', 'London 2012'),
        ('rio-2016-og', 'Rio 2016'),
        ('tokyo-2020-og', 'Tokyo 2020'),
        ('2024-paris-olympic-games', 'Paris 2024')
    ]

    all_results = []
    all_medalists = []

    for slug, name in olympics:
        try:
            results_file = f'data_wt_detailed/{slug}_results_table_0.csv'
            medalists_file = f'data_wt_detailed/{slug}_medalists_table_0.csv'

            if os.path.exists(results_file):
                df = pd.read_csv(results_file)
                df['competition'] = name
                df['year'] = int(name.split()[-1])
                all_results.append(df)

            if os.path.exists(medalists_file):
                df = pd.read_csv(medalists_file)
                df['competition'] = name
                df['year'] = int(name.split()[-1])
                all_medalists.append(df)
        except Exception as e:
            st.warning(f"Could not load {name}: {e}")

    results_df = pd.concat(all_results, ignore_index=True) if all_results else pd.DataFrame()
    medalists_df = pd.concat(all_medalists, ignore_index=True) if all_medalists else pd.DataFrame()

    return results_df, medalists_df

@st.cache_data(ttl=600)
def load_world_championships_data():
    """Load World Championships data"""
    wc_files = []

    if os.path.exists('data_wt_detailed'):
        for f in os.listdir('data_wt_detailed'):
            if 'world-taekwondo-championships' in f and f.endswith('_medalists_table_0.csv'):
                wc_files.append(f.replace('_medalists_table_0.csv', ''))

    all_medalists = []

    for slug in wc_files:
        try:
            medalists_file = f'data_wt_detailed/{slug}_medalists_table_0.csv'
            if os.path.exists(medalists_file):
                df = pd.read_csv(medalists_file)
                df['competition'] = slug
                # Extract year from slug
                parts = slug.split('-')
                for part in parts:
                    if part.isdigit() and len(part) == 4:
                        df['year'] = int(part)
                        break
                all_medalists.append(df)
        except:
            pass

    return pd.concat(all_medalists, ignore_index=True) if all_medalists else pd.DataFrame()

@st.cache_data(ttl=600)
def load_competition_summary():
    """Load scraping summary to get competition list"""
    try:
        with open('data_wt_detailed/scraping_summary.json') as f:
            return json.load(f)
    except:
        return {}

@st.cache_data(ttl=600)
def load_athlete_data():
    """Load athlete database"""
    try:
        if os.path.exists('analysis_reports/athletes_list.csv'):
            return pd.read_csv('analysis_reports/athletes_list.csv')
    except:
        pass
    return pd.DataFrame()

# ==================== DATA PROCESSING FUNCTIONS ====================

def extract_country_from_name(name_str):
    """Extract 3-letter country code from athlete name string"""
    if pd.isna(name_str):
        return None

    name_str = str(name_str).strip()
    # Country codes are typically last 3 characters
    if len(name_str) >= 3:
        potential_code = name_str[-3:].strip().upper()
        # Check if it looks like a country code (all uppercase letters)
        if potential_code.isalpha() and potential_code.isupper():
            return potential_code
    return None

def extract_athlete_name(name_str):
    """Extract athlete name without country code"""
    if pd.isna(name_str):
        return None

    name_str = str(name_str).strip()
    # Remove last 3 characters if they look like country code
    if len(name_str) > 4:
        potential_code = name_str[-3:].upper()
        if potential_code.isalpha():
            return name_str[:-3].strip()
    return name_str

def process_medalists_data(df):
    """Process medalists dataframe to extract structured data"""
    if df.empty:
        return df

    # Column 1 typically has athlete name & country
    # Column 2 has weight category
    # Column 3 has medal type

    df_processed = df.copy()

    # Extract athlete and country from first name column
    if len(df.columns) > 1:
        name_col = df.columns[1]
        df_processed['athlete_country'] = df[name_col].apply(extract_country_from_name)
        df_processed['athlete_name'] = df[name_col].apply(extract_athlete_name)

    # Extract weight category
    if len(df.columns) > 2:
        df_processed['weight_category'] = df[df.columns[2]]

    # Extract medal type
    if len(df.columns) > 3:
        df_processed['medal'] = df[df.columns[3]]

    return df_processed

def calculate_medal_table(medalists_df):
    """Calculate medal table by country"""
    if medalists_df.empty:
        return pd.DataFrame()

    df = process_medalists_data(medalists_df)

    medal_counts = df.groupby(['athlete_country', 'medal']).size().unstack(fill_value=0)

    # Ensure all medal types exist
    for medal in ['Gold', 'Silver', 'Bronze']:
        if medal not in medal_counts.columns:
            medal_counts[medal] = 0

    medal_counts['Total'] = medal_counts.sum(axis=1)
    medal_counts = medal_counts.sort_values('Total', ascending=False)

    return medal_counts.reset_index()

# ==================== VISUALIZATION FUNCTIONS ====================

def create_medal_distribution_chart(medal_table, title="Medal Distribution"):
    """Create stacked bar chart of medal distribution"""
    fig = go.Figure()

    colors = {'Gold': '#FFD700', 'Silver': '#C0C0C0', 'Bronze': '#CD7F32'}

    for medal in ['Gold', 'Silver', 'Bronze']:
        if medal in medal_table.columns:
            fig.add_trace(go.Bar(
                name=medal,
                x=medal_table['athlete_country'],
                y=medal_table[medal],
                marker_color=colors[medal],
                text=medal_table[medal],
                textposition='inside',
                textfont=dict(size=12, color='black', family='Arial Black')
            ))

    fig.update_layout(
        title=title,
        barmode='stack',
        xaxis_title="Country",
        yaxis_title="Medal Count",
        height=500,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode='x unified',
        template='plotly_white'
    )

    return fig

def create_timeline_chart(medalists_df, countries=None):
    """Create timeline of medal wins"""
    df = process_medalists_data(medalists_df)

    if countries:
        df = df[df['athlete_country'].isin(countries)]

    medal_timeline = df.groupby(['year', 'athlete_country', 'medal']).size().reset_index(name='count')

    fig = px.line(
        medal_timeline,
        x='year',
        y='count',
        color='athlete_country',
        line_dash='medal',
        title="Medal Count Timeline",
        labels={'year': 'Year', 'count': 'Medal Count', 'athlete_country': 'Country'},
        height=500
    )

    fig.update_layout(
        hovermode='x unified',
        template='plotly_white'
    )

    return fig

def create_weight_category_distribution(medalists_df):
    """Analyze medal distribution by weight category"""
    df = process_medalists_data(medalists_df)

    if df.empty or 'weight_category' not in df.columns:
        return None

    weight_dist = df.groupby(['weight_category', 'medal']).size().reset_index(name='count')

    fig = px.bar(
        weight_dist,
        x='weight_category',
        y='count',
        color='medal',
        title="Medal Distribution by Weight Category",
        color_discrete_map={'Gold': '#FFD700', 'Silver': '#C0C0C0', 'Bronze': '#CD7F32'},
        height=500,
        barmode='group'
    )

    fig.update_layout(
        xaxis_title="Weight Category",
        yaxis_title="Medal Count",
        template='plotly_white'
    )

    return fig

# ==================== MAIN DASHBOARD ====================

def main():
    """Main dashboard application"""

    # ========== HEADER ==========
    st.markdown("""
    <div class="main-header">
        <h1>🥋 Elite Taekwondo Analytics</h1>
        <p>Saudi Arabia High-Performance Analysis Dashboard</p>
    </div>
    """, unsafe_allow_html=True)

    # ========== LOAD DATA ==========
    with st.spinner("Loading competition data..."):
        olympic_results, olympic_medalists = load_olympic_data()
        wc_medalists = load_world_championships_data()
        competition_summary = load_competition_summary()
        athlete_data = load_athlete_data()

    # ========== SIDEBAR ==========
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/0/0d/Flag_of_Saudi_Arabia.svg/320px-Flag_of_Saudi_Arabia.svg.png", width=280)

        st.markdown("### 🎯 Navigation")

        page = st.radio(
            "Select Analysis View",
            [
                "🏠 Executive Dashboard",
                "🥇 Olympic Analysis",
                "🌍 World Championships",
                "📊 Country Comparison",
                "👤 Athlete Performance",
                "📈 Historical Trends",
                "🎯 Strategic Insights"
            ],
            label_visibility="collapsed"
        )

        st.markdown("---")

        # Data summary
        st.markdown("### 📁 Data Summary")
        total_comps = competition_summary.get('total_competitions_scraped', 0)
        st.metric("Competitions", total_comps)
        st.metric("Olympic Games", 7)
        st.metric("World Championships", len(wc_medalists['competition'].unique()) if not wc_medalists.empty else 0)

        st.markdown("---")
        st.markdown("*Updated: " + datetime.now().strftime("%Y-%m-%d %H:%M") + "*")

    # ========== MAIN CONTENT ==========

    if "Executive Dashboard" in page:
        show_executive_dashboard(olympic_medalists, wc_medalists, competition_summary)

    elif "Olympic Analysis" in page:
        show_olympic_analysis(olympic_results, olympic_medalists)

    elif "World Championships" in page:
        show_world_championships(wc_medalists)

    elif "Country Comparison" in page:
        show_country_comparison(olympic_medalists, wc_medalists)

    elif "Athlete Performance" in page:
        show_athlete_performance(olympic_medalists, wc_medalists, athlete_data)

    elif "Historical Trends" in page:
        show_historical_trends(olympic_medalists, wc_medalists)

    elif "Strategic Insights" in page:
        show_strategic_insights(olympic_medalists, wc_medalists)

# ==================== PAGE FUNCTIONS ====================

def show_executive_dashboard(olympic_medalists, wc_medalists, comp_summary):
    """Executive summary dashboard"""

    st.markdown('<p class="section-header">📊 Executive Dashboard</p>', unsafe_allow_html=True)

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("""
        <div class="metric-card">
            <p class="metric-value">50</p>
            <p class="metric-label">Competitions Analyzed</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        total_olympic_medals = len(olympic_medalists) if not olympic_medalists.empty else 0
        st.markdown(f"""
        <div class="metric-card">
            <p class="metric-value">{total_olympic_medals}</p>
            <p class="metric-label">Olympic Medals (2000-2024)</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        olympic_countries = process_medalists_data(olympic_medalists)['athlete_country'].nunique() if not olympic_medalists.empty else 0
        st.markdown(f"""
        <div class="metric-card">
            <p class="metric-value">{olympic_countries}</p>
            <p class="metric-label">Countries with Olympic Medals</p>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        years_span = "1973-2025"
        st.markdown(f"""
        <div class="metric-card">
            <p class="metric-value">52</p>
            <p class="metric-label">Years of Data</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Main visualizations
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🏅 Olympic Medal Table (2000-2024)")
        if not olympic_medalists.empty:
            medal_table = calculate_medal_table(olympic_medalists)

            # Highlight Saudi Arabia
            def highlight_saudi(row):
                if row['athlete_country'] == 'KSA':
                    return ['background-color: rgba(0,108,53,0.2); font-weight: bold'] * len(row)
                return [''] * len(row)

            st.dataframe(
                medal_table.head(15).style.apply(highlight_saudi, axis=1),
                use_container_width=True,
                height=400
            )
        else:
            st.info("No Olympic medal data available")

    with col2:
        st.markdown("### 📊 Top 10 Medal Winners")
        if not olympic_medalists.empty:
            medal_table = calculate_medal_table(olympic_medalists)
            fig = create_medal_distribution_chart(medal_table.head(10), "Top 10 Countries")
            st.plotly_chart(fig, use_container_width=True)

    # Competition breakdown
    st.markdown("---")
    st.markdown("### 🏆 Competition Database Summary")

    if comp_summary and 'competitions' in comp_summary:
        comps_df = pd.DataFrame(comp_summary['competitions'])

        # Group by competition type
        comp_type_dist = defaultdict(int)
        for comp in comp_summary['competitions']:
            name = comp['name'].lower()
            if 'olympic' in name:
                comp_type_dist['Olympics'] += 1
            elif 'world' in name and 'championships' in name:
                comp_type_dist['World Championships'] += 1
            elif 'grand prix' in name:
                comp_type_dist['Grand Prix'] += 1
            elif 'grand slam' in name:
                comp_type_dist['Grand Slam'] += 1
            else:
                comp_type_dist['Other'] += 1

        comp_dist_df = pd.DataFrame(list(comp_type_dist.items()), columns=['Competition Type', 'Count'])

        fig = px.pie(
            comp_dist_df,
            values='Count',
            names='Competition Type',
            title="Competition Type Distribution",
            color_discrete_sequence=px.colors.sequential.Greens_r,
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)

def show_olympic_analysis(olympic_results, olympic_medalists):
    """Detailed Olympic analysis"""

    st.markdown('<p class="section-header">🥇 Olympic Games Analysis (2000-2024)</p>', unsafe_allow_html=True)

    if olympic_medalists.empty:
        st.warning("No Olympic data available")
        return

    # Olympic selector
    olympics = [
        'All Olympics',
        'Paris 2024',
        'Tokyo 2020',
        'Rio 2016',
        'London 2012',
        'Beijing 2008',
        'Athens 2004',
        'Sydney 2000'
    ]

    selected_olympic = st.selectbox("Select Olympic Games", olympics)

    # Filter data
    if selected_olympic != 'All Olympics':
        filtered_medalists = olympic_medalists[olympic_medalists['competition'] == selected_olympic]
    else:
        filtered_medalists = olympic_medalists

    # Stats
    col1, col2, col3, col4 = st.columns(4)

    processed_df = process_medalists_data(filtered_medalists)

    with col1:
        total_medals = len(filtered_medalists)
        st.metric("Total Medals", total_medals)

    with col2:
        gold_medals = len(processed_df[processed_df['medal'] == 'Gold']) if 'medal' in processed_df.columns else 0
        st.metric("Gold Medals", gold_medals)

    with col3:
        countries = processed_df['athlete_country'].nunique() if 'athlete_country' in processed_df.columns else 0
        st.metric("Countries", countries)

    with col4:
        if selected_olympic != 'All Olympics':
            year = selected_olympic.split()[-1]
            st.metric("Year", year)
        else:
            st.metric("Years", "2000-2024")

    st.markdown("---")

    # Visualizations
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🏆 Medal Table")
        medal_table = calculate_medal_table(filtered_medalists)

        # Highlight key countries
        def highlight_row(row):
            if row['athlete_country'] in ['KSA', 'SAU']:
                return ['background-color: #c8e6c9; font-weight: bold'] * len(row)
            elif row['athlete_country'] in ['IRI', 'JOR', 'UAE', 'TUR']:
                return ['background-color: #fff9c4'] * len(row)
            return [''] * len(row)

        st.dataframe(
            medal_table.head(20).style.apply(highlight_row, axis=1),
            use_container_width=True,
            height=500
        )

    with col2:
        st.markdown("### 📊 Medal Distribution")
        fig = create_medal_distribution_chart(medal_table.head(15), f"{selected_olympic} Medal Distribution")
        st.plotly_chart(fig, use_container_width=True)

    # Weight category analysis
    if selected_olympic == 'All Olympics':
        st.markdown("---")
        st.markdown("### ⚖️ Performance by Weight Category")

        weight_fig = create_weight_category_distribution(filtered_medalists)
        if weight_fig:
            st.plotly_chart(weight_fig, use_container_width=True)

    # Regional analysis
    st.markdown("---")
    st.markdown("### 🌍 Regional Performance")

    regional_rivals = ['KSA', 'IRI', 'JOR', 'UAE', 'TUR', 'EGY', 'MAR']
    regional_medalists = processed_df[processed_df['athlete_country'].isin(regional_rivals)]

    if not regional_medalists.empty:
        regional_table = calculate_medal_table(pd.DataFrame({
            df.columns[1]: regional_medalists['athlete_name'] + ' ' + regional_medalists['athlete_country'],
            df.columns[2]: regional_medalists['weight_category'],
            df.columns[3]: regional_medalists['medal']
        }))

        st.markdown("**Middle East & North Africa Performance**")
        st.dataframe(regional_table, use_container_width=True)
    else:
        st.info("No regional medal data available for selected Olympic Games")

def show_world_championships(wc_medalists):
    """World Championships analysis"""

    st.markdown('<p class="section-header">🌍 World Championships Analysis</p>', unsafe_allow_html=True)

    if wc_medalists.empty:
        st.warning("No World Championships data available")
        return

    # Stats
    col1, col2, col3, col4 = st.columns(4)

    processed_df = process_medalists_data(wc_medalists)

    with col1:
        total_championships = wc_medalists['competition'].nunique()
        st.metric("Total Championships", total_championships)

    with col2:
        if 'year' in wc_medalists.columns:
            year_range = f"{int(wc_medalists['year'].min())}-{int(wc_medalists['year'].max())}"
        else:
            year_range = "1973-2025"
        st.metric("Year Range", year_range)

    with col3:
        total_medals = len(wc_medalists)
        st.metric("Total Medals", total_medals)

    with col4:
        countries = processed_df['athlete_country'].nunique() if 'athlete_country' in processed_df.columns else 0
        st.metric("Countries", countries)

    st.markdown("---")

    # Medal table
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("### 🏆 All-Time World Championships Medal Table")
        medal_table = calculate_medal_table(wc_medalists)

        st.dataframe(
            medal_table.head(20),
            use_container_width=True,
            height=600
        )

    with col2:
        st.markdown("### 📊 Top 12 Performing Nations")
        fig = create_medal_distribution_chart(medal_table.head(12), "World Championships Medal Distribution")
        st.plotly_chart(fig, use_container_width=True)

        # Timeline
        st.markdown("### 📈 Medal Timeline (Top 8)")
        top_countries = medal_table.head(8)['athlete_country'].tolist()
        timeline_fig = create_timeline_chart(wc_medalists, top_countries)
        st.plotly_chart(timeline_fig, use_container_width=True)

def show_country_comparison(olympic_medalists, wc_medalists):
    """Country-by-country comparison"""

    st.markdown('<p class="section-header">🌐 Country Performance Comparison</p>', unsafe_allow_html=True)

    # Get all countries
    olympic_processed = process_medalists_data(olympic_medalists)
    wc_processed = process_medalists_data(wc_medalists)

    all_countries = sorted(set(
        list(olympic_processed['athlete_country'].dropna().unique()) +
        list(wc_processed['athlete_country'].dropna().unique())
    ))

    # Country selector
    st.markdown("### Select Countries to Compare")

    default_countries = ['KOR', 'CHN', 'IRI', 'GBR', 'FRA', 'USA']
    available_defaults = [c for c in default_countries if c in all_countries]

    selected_countries = st.multiselect(
        "Choose countries (default: major powers)",
        all_countries,
        default=available_defaults[:6] if available_defaults else all_countries[:6]
    )

    if not selected_countries:
        st.warning("Please select at least one country")
        return

    # Add Saudi highlight
    if 'KSA' in all_countries or 'SAU' in all_countries:
        st.info("💡 Tip: Add 'KSA' to compare Saudi Arabia's performance")

    # Filter data
    olympic_filtered = olympic_processed[olympic_processed['athlete_country'].isin(selected_countries)]
    wc_filtered = wc_processed[wc_processed['athlete_country'].isin(selected_countries)]

    # Create comparison metrics
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🥇 Olympic Performance Comparison")
        olympic_table = calculate_medal_table(pd.DataFrame({
            olympic_medalists.columns[1]: olympic_filtered['athlete_name'] + ' ' + olympic_filtered['athlete_country'],
            olympic_medalists.columns[2]: olympic_filtered['weight_category'],
            olympic_medalists.columns[3]: olympic_filtered['medal']
        }))

        if not olympic_table.empty:
            fig = create_medal_distribution_chart(olympic_table, "Olympic Medals Comparison")
            st.plotly_chart(fig, use_container_width=True)

            st.dataframe(olympic_table, use_container_width=True)
        else:
            st.info("No Olympic data for selected countries")

    with col2:
        st.markdown("### 🌍 World Championships Comparison")
        wc_table = calculate_medal_table(pd.DataFrame({
            wc_medalists.columns[1]: wc_filtered['athlete_name'] + ' ' + wc_filtered['athlete_country'],
            wc_medalists.columns[2]: wc_filtered['weight_category'],
            wc_medalists.columns[3]: wc_filtered['medal']
        }))

        if not wc_table.empty:
            fig = create_medal_distribution_chart(wc_table, "World Championships Comparison")
            st.plotly_chart(fig, use_container_width=True)

            st.dataframe(wc_table, use_container_width=True)
        else:
            st.info("No World Championships data for selected countries")

    # Combined analysis
    st.markdown("---")
    st.markdown("### 📊 Combined Performance Analysis")

    combined_data = []
    for country in selected_countries:
        olympic_medals = len(olympic_filtered[olympic_filtered['athlete_country'] == country])
        wc_medals = len(wc_filtered[wc_filtered['athlete_country'] == country])
        total = olympic_medals + wc_medals

        combined_data.append({
            'Country': country,
            'Olympic Medals': olympic_medals,
            'World Championships': wc_medals,
            'Total Medals': total
        })

    combined_df = pd.DataFrame(combined_data).sort_values('Total Medals', ascending=False)

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name='Olympic Medals',
        x=combined_df['Country'],
        y=combined_df['Olympic Medals'],
        marker_color='#FFD700'
    ))

    fig.add_trace(go.Bar(
        name='World Championships',
        x=combined_df['Country'],
        y=combined_df['World Championships'],
        marker_color='#006C35'
    ))

    fig.update_layout(
        title="Total Medal Count: Olympics + World Championships",
        barmode='group',
        height=500,
        template='plotly_white'
    )

    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(combined_df, use_container_width=True)

def show_athlete_performance(olympic_medalists, wc_medalists, athlete_data):
    """Individual athlete performance"""

    st.markdown('<p class="section-header">👤 Athlete Performance Analysis</p>', unsafe_allow_html=True)

    # Combine all medalists
    olympic_processed = process_medalists_data(olympic_medalists)
    wc_processed = process_medalists_data(wc_medalists)

    all_athletes = sorted(set(
        list(olympic_processed['athlete_name'].dropna().unique()) +
        list(wc_processed['athlete_name'].dropna().unique())
    ))

    if not all_athletes:
        st.warning("No athlete data available")
        return

    # Search functionality
    search_term = st.text_input("🔍 Search for athlete", placeholder="Enter athlete name...")

    if search_term:
        matching_athletes = [a for a in all_athletes if search_term.lower() in a.lower()]
    else:
        matching_athletes = all_athletes[:50]  # Show first 50

    selected_athlete = st.selectbox(
        "Select Athlete",
        matching_athletes if matching_athletes else ["No athletes found"]
    )

    if selected_athlete and selected_athlete != "No athletes found":
        # Get athlete data
        athlete_olympic = olympic_processed[olympic_processed['athlete_name'].str.contains(selected_athlete, case=False, na=False)]
        athlete_wc = wc_processed[wc_processed['athlete_name'].str.contains(selected_athlete, case=False, na=False)]

        # Profile
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Olympic Medals", len(athlete_olympic))

        with col2:
            st.metric("World Championship Medals", len(athlete_wc))

        with col3:
            total_gold = len(athlete_olympic[athlete_olympic['medal'] == 'Gold']) + len(athlete_wc[athlete_wc['medal'] == 'Gold'])
            st.metric("Total Gold", total_gold)

        with col4:
            if not athlete_olympic.empty:
                country = athlete_olympic['athlete_country'].iloc[0]
            elif not athlete_wc.empty:
                country = athlete_wc['athlete_country'].iloc[0]
            else:
                country = "Unknown"
            st.metric("Country", country)

        st.markdown("---")

        # Medal breakdown
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 🥇 Olympic Performance")
            if not athlete_olympic.empty:
                st.dataframe(athlete_olympic[['competition', 'weight_category', 'medal']], use_container_width=True)
            else:
                st.info("No Olympic medals")

        with col2:
            st.markdown("### 🌍 World Championships")
            if not athlete_wc.empty:
                st.dataframe(athlete_wc[['competition', 'weight_category', 'medal']].head(10), use_container_width=True)
            else:
                st.info("No World Championship medals")

def show_historical_trends(olympic_medalists, wc_medalists):
    """Historical performance trends"""

    st.markdown('<p class="section-header">📈 Historical Performance Trends</p>', unsafe_allow_html=True)

    # Olympic trends
    st.markdown("### 🥇 Olympic Medals Over Time")

    if not olympic_medalists.empty and 'year' in olympic_medalists.columns:
        olympic_processed = process_medalists_data(olympic_medalists)

        olympic_timeline = olympic_processed.groupby(['year', 'athlete_country']).size().reset_index(name='medals')
        olympic_timeline = olympic_timeline.sort_values('medals', ascending=False)

        # Top 8 countries
        top_countries = olympic_timeline.groupby('athlete_country')['medals'].sum().nlargest(8).index
        olympic_top = olympic_timeline[olympic_timeline['athlete_country'].isin(top_countries)]

        fig = px.line(
            olympic_top,
            x='year',
            y='medals',
            color='athlete_country',
            title="Olympic Medal Count by Year (Top 8 Countries)",
            markers=True,
            height=500
        )

        fig.update_layout(
            xaxis_title="Olympic Year",
            yaxis_title="Medal Count",
            hovermode='x unified',
            template='plotly_white'
        )

        st.plotly_chart(fig, use_container_width=True)

        # Medal type evolution
        st.markdown("### 🏅 Medal Type Distribution Over Time")

        medal_evolution = olympic_processed.groupby(['year', 'medal']).size().reset_index(name='count')

        fig = px.area(
            medal_evolution,
            x='year',
            y='count',
            color='medal',
            title="Medal Types Distribution Across Olympic Games",
            color_discrete_map={'Gold': '#FFD700', 'Silver': '#C0C0C0', 'Bronze': '#CD7F32'},
            height=500
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No timeline data available")

    # Emerging nations
    st.markdown("---")
    st.markdown("### 🌟 Emerging Taekwondo Nations")

    st.markdown("""
    <div class="info-box">
        <h4>Key Trends in Global Taekwondo:</h4>
        <ul>
            <li><strong>South Korea</strong> continues to dominate with 25 Olympic medals</li>
            <li><strong>China</strong> emerging as second power with 13 Olympic medals</li>
            <li><strong>European nations</strong> (GBR, FRA, TUR) showing strong growth</li>
            <li><strong>Middle East</strong> presence growing (Iran with 9 medals, Jordan's breakthrough)</li>
            <li><strong>Global spread</strong> - 48 countries have won Olympic medals</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

def show_strategic_insights(olympic_medalists, wc_medalists):
    """Strategic insights and recommendations"""

    st.markdown('<p class="section-header">🎯 Strategic Insights & Recommendations</p>', unsafe_allow_html=True)

    # Saudi Arabia analysis
    st.markdown("### 🇸🇦 Saudi Arabia Performance Analysis")

    olympic_processed = process_medalists_data(olympic_medalists)
    wc_processed = process_medalists_data(wc_medalists)

    saudi_olympic = olympic_processed[olympic_processed['athlete_country'].isin(['KSA', 'SAU'])]
    saudi_wc = wc_processed[wc_processed['athlete_country'].isin(['KSA', 'SAU'])]

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Olympic Medals", len(saudi_olympic))

    with col2:
        st.metric("World Championship Medals", len(saudi_wc))

    with col3:
        total_medals = len(saudi_olympic) + len(saudi_wc)
        st.metric("Total Medals", total_medals)

    st.markdown("---")

    # Regional comparison
    st.markdown("### 🌍 Regional Competitive Analysis")

    regional_countries = ['KSA', 'SAU', 'IRI', 'JOR', 'UAE', 'TUR', 'EGY', 'MAR']

    regional_olympic = olympic_processed[olympic_processed['athlete_country'].isin(regional_countries)]
    regional_comparison = calculate_medal_table(pd.DataFrame({
        olympic_medalists.columns[1]: regional_olympic['athlete_name'] + ' ' + regional_olympic['athlete_country'],
        olympic_medalists.columns[2]: regional_olympic['weight_category'],
        olympic_medalists.columns[3]: regional_olympic['medal']
    }))

    if not regional_comparison.empty:
        fig = create_medal_distribution_chart(regional_comparison, "Regional Olympic Performance (MENA)")
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(regional_comparison, use_container_width=True)

    # Strategic recommendations
    st.markdown("---")
    st.markdown("### 💡 Strategic Recommendations for Saudi Arabia")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="info-box">
            <h4>🎯 Immediate Focus Areas:</h4>
            <ol>
                <li><strong>Olympic Qualification</strong> - Secure spots for LA 2028</li>
                <li><strong>Grand Prix Participation</strong> - Maximize ranking points</li>
                <li><strong>Asian Championships</strong> - Target regional medals</li>
                <li><strong>Talent Identification</strong> - Expand youth pipeline</li>
                <li><strong>International Training</strong> - Partner with KOR/CHN programs</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="warning-box">
            <h4>⚠️ Key Challenges:</h4>
            <ul>
                <li><strong>Regional Competition</strong> - Iran leads MENA with 9 Olympic medals</li>
                <li><strong>Global Standards</strong> - Top 3 nations have 25+ Olympic medals</li>
                <li><strong>Consistency</strong> - Need regular podium finishes at majors</li>
                <li><strong>Weight Category Coverage</strong> - Develop athletes across all categories</li>
                <li><strong>Experience Gap</strong> - Increase international competition exposure</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    # Vision 2030 alignment
    st.markdown("---")
    st.markdown("### 🚀 Vision 2030 Goals & Milestones")

    st.markdown("""
    <div class="info-box">
        <h3>Saudi Arabia Taekwondo - Vision 2030 Roadmap</h3>

        <h4>2024-2025: Foundation Building</h4>
        <ul>
            <li>Establish comprehensive athlete database</li>
            <li>Implement data-driven training programs</li>
            <li>Increase Grand Prix participation by 50%</li>
            <li>Target 2-3 athletes in World Top 50</li>
        </ul>

        <h4>2026-2027: Regional Dominance</h4>
        <ul>
            <li>Win 5+ medals at Asian Championships</li>
            <li>Qualify 4+ athletes for LA 2028 Olympics</li>
            <li>Establish Saudi Arabia as top 3 MENA nation</li>
            <li>Host international Grand Prix event in Saudi Arabia</li>
        </ul>

        <h4>2028: Olympic Breakthrough</h4>
        <ul>
            <li>Win first Olympic medal at LA 2028</li>
            <li>Field full team (8 athletes across all categories)</li>
            <li>Achieve minimum 2 Top 8 finishes</li>
            <li>Establish Saudi Arabia as global taekwondo force</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# ==================== RUN APP ====================

if __name__ == "__main__":
    main()
