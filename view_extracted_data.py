"""
Taekwondo PDF Data Viewer
Interactive viewer for extracted PDF data with category dropdowns
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import json

# Page config
st.set_page_config(
    page_title="Taekwondo Data Viewer",
    page_icon="🥋",
    layout="wide"
)

st.title("🥋 Taekwondo Competition Data Viewer")
st.markdown("View extracted PDF data by category with competition names and age brackets")

# Load extraction summary
summary_file = Path("extracted_data/extraction_summary_20251113_073827.json")
with open(summary_file, 'r') as f:
    summary_data = json.load(f)

# Sidebar - Category Selection
st.sidebar.header("Filter Options")

# Create category dropdown with readable names
category_mapping = {
    'beach_championships': '🏖️ Beach Championships',
    'grand_prix': '🏆 Grand Prix',
    'grand_prix_challenge': '🎯 Grand Prix Challenge',
    'grand_prix_final': '🥇 Grand Prix Final',
    'grand_slam': '💥 Grand Slam',
    'poomsae': '📋 Poomsae (Recognized)',
    'poomsae_para': '♿ Poomsae Para',
    'womens_open': '👩 Women\'s Open',
    'world_champs_cadet': '👦 World Championships - Cadet',
    'world_champs_junior': '🧒 World Championships - Junior',
    'world_champs_para': '♿ World Championships - Para',
    'world_champs_senior': '🥋 World Championships - Senior',
    'world_champs_u21': '🎓 World Championships - U21',
    'world_champs_veterans': '👴 World Championships - Veterans',
    'youth_olympics': '🏅 Youth Olympics'
}

# Get available categories
available_categories = {item['category']: category_mapping.get(item['category'], item['category'])
                       for item in summary_data['details']}

# Category selector
selected_display = st.sidebar.selectbox(
    "Select Category:",
    options=list(available_categories.values()),
    index=0
)

# Get actual category key
selected_category = [k for k, v in available_categories.items() if v == selected_display][0]

# Find category details
category_details = next(item for item in summary_data['details'] if item['category'] == selected_category)

# Display category stats
st.sidebar.markdown("---")
st.sidebar.subheader("Category Stats")
st.sidebar.metric("PDFs Processed", category_details['files_processed'])
st.sidebar.metric("Tables Extracted", category_details['tables_extracted'])
st.sidebar.metric("Total Rows", category_details['total_rows'])

# Main content area
st.header(f"{selected_display}")

# Load the category data
csv_path = Path(category_details['output_file'])
if csv_path.exists():
    df = pd.read_csv(csv_path)

    # Show metadata summary
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Records", len(df))

    with col2:
        if 'age_bracket' in df.columns:
            age_brackets = df['age_bracket'].dropna().unique()
            st.metric("Age Brackets", len(age_brackets))
            if len(age_brackets) > 0:
                st.caption(", ".join(str(ab).title() for ab in age_brackets[:3]))

    with col3:
        if 'year' in df.columns:
            years = df['year'].dropna().unique()
            st.metric("Years", len(years))
            if len(years) > 0:
                st.caption(", ".join(str(int(y)) for y in sorted(years)))

    with col4:
        if 'location' in df.columns:
            locations = df['location'].dropna().unique()
            st.metric("Locations", len(locations))
            if len(locations) > 0:
                st.caption(", ".join(str(loc) for loc in locations[:2]))

    st.markdown("---")

    # Filters
    with st.expander("🔍 Advanced Filters", expanded=False):
        filter_col1, filter_col2, filter_col3 = st.columns(3)

        with filter_col1:
            if 'competition_name' in df.columns:
                comp_names = ['All'] + sorted(df['competition_name'].dropna().unique().tolist())
                selected_comp = st.selectbox("Competition Name:", comp_names)
                if selected_comp != 'All':
                    df = df[df['competition_name'] == selected_comp]

        with filter_col2:
            if 'year' in df.columns:
                years = ['All'] + sorted([int(y) for y in df['year'].dropna().unique()])
                selected_year = st.selectbox("Year:", years)
                if selected_year != 'All':
                    df = df[df['year'] == selected_year]

        with filter_col3:
            if 'location' in df.columns:
                locations = ['All'] + sorted(df['location'].dropna().unique().tolist())
                selected_loc = st.selectbox("Location:", locations)
                if selected_loc != 'All':
                    df = df[df['location'] == selected_loc]

    # Display options
    display_option = st.radio(
        "Display Mode:",
        ["📊 Interactive Table", "📄 Full Data", "📈 Summary Stats"],
        horizontal=True
    )

    if display_option == "📊 Interactive Table":
        # Show key columns only
        key_cols = ['competition_name', 'location', 'year', 'age_bracket', 'source_file']
        display_cols = [col for col in key_cols if col in df.columns]

        if display_cols:
            st.dataframe(
                df[display_cols].head(100),
                use_container_width=True,
                height=500
            )
        else:
            st.dataframe(df.head(100), use_container_width=True, height=500)

        st.caption(f"Showing first 100 of {len(df)} rows")

    elif display_option == "📄 Full Data":
        st.dataframe(df, use_container_width=True, height=600)

        # Download button
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"{selected_category}_data.csv",
            mime="text/csv"
        )

    else:  # Summary Stats
        st.subheader("Data Summary")

        # Show value counts for key columns
        if 'competition_name' in df.columns:
            st.write("**Competition Names:**")
            st.write(df['competition_name'].value_counts().head(10))

        if 'age_bracket' in df.columns:
            st.write("**Age Brackets:**")
            st.write(df['age_bracket'].value_counts())

        if 'year' in df.columns:
            st.write("**Years:**")
            st.write(df['year'].value_counts())

        if 'location' in df.columns:
            st.write("**Locations:**")
            st.write(df['location'].value_counts())

else:
    st.error(f"Data file not found: {csv_path}")

# Footer
st.markdown("---")
st.caption("Data extracted from World Taekwondo PDFs")
