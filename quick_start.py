"""
Quick Start Script - Taekwondo Performance Analysis
Run this to get started immediately with sample analysis
"""

import os
from pathlib import Path

def print_header(text):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")


def check_environment():
    """Check if environment is set up correctly"""
    print_header("STEP 1: Environment Check")

    # Check Python packages
    required_packages = [
        'requests', 'beautifulsoup4', 'pandas', 'streamlit',
        'plotly', 'openpyxl', 'schedule'
    ]

    missing = []

    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package} installed")
        except ImportError:
            print(f"✗ {package} MISSING")
            missing.append(package)

    if missing:
        print(f"\n⚠ Missing packages: {', '.join(missing)}")
        print("Run: pip install -r requirements.txt")
        return False
    else:
        print("\n✓ All dependencies installed!")
        return True


def create_directories():
    """Create necessary directories"""
    print_header("STEP 2: Creating Directory Structure")

    dirs = ['data', 'data/competitions', 'data/athletes', 'data/rankings',
            'data/matches', 'reports', 'result_books']

    for dir_path in dirs:
        Path(dir_path).mkdir(exist_ok=True, parents=True)
        print(f"✓ Created: {dir_path}/")

    print("\n✓ Directory structure ready!")


def run_sample_scrape():
    """Run a quick data collection"""
    print_header("STEP 3: Sample Data Collection")

    print("Starting data scraper...")
    print("This will take a few minutes...\n")

    try:
        from taekwondo_scraper import TaekwondoDataScraper

        scraper = TaekwondoDataScraper(output_dir="data")

        # Just get rankings for quick start
        print("Fetching world rankings...")
        scraper.scrape_world_rankings()

        print("\n✓ Sample data collected!")
        return True

    except Exception as e:
        print(f"✗ Error during scraping: {e}")
        print("You can still continue - some features may be limited")
        return False


def run_sample_analysis():
    """Run sample analysis"""
    print_header("STEP 4: Performance Analysis")

    try:
        from performance_analyzer import TaekwondoPerformanceAnalyzer

        analyzer = TaekwondoPerformanceAnalyzer(data_dir="data")

        print("Analyzing Saudi team...")
        team_analytics = analyzer.analyze_saudi_team()

        print(f"\n📊 Team Statistics:")
        print(f"   Active Athletes: {team_analytics.total_active_athletes}")
        print(f"   Athletes in Top 50: {team_analytics.athletes_in_top50}")
        print(f"   Total Medals: {team_analytics.total_gold + team_analytics.total_silver + team_analytics.total_bronze}")

        print("\n🌍 Benchmarking against rivals...")
        rivals = analyzer.benchmark_against_rivals()

        if not rivals.empty:
            print("\nTop 5 Countries by Ranking Points:")
            print(rivals[['country', 'total_ranked_athletes', 'athletes_in_top50']].head().to_string(index=False))

        print("\n🥇 Identifying medal opportunities...")
        opportunities = analyzer.identify_medal_opportunities()

        if opportunities:
            print(f"\nTop 3 Medal Opportunities:")
            for i, opp in enumerate(opportunities[:3], 1):
                print(f"  {i}. {opp['weight_category']}: {opp['athlete_name']}")
                print(f"     Current Rank: #{opp['current_rank']} | Opportunity Score: {opp['opportunity_score']}/100")

        print("\n📄 Generating comprehensive report...")
        analyzer.export_analysis_report("reports/quick_start_report.xlsx")

        print("\n✓ Analysis complete!")
        print(f"   Report saved to: reports/quick_start_report.xlsx")

        return True

    except Exception as e:
        print(f"✗ Error during analysis: {e}")
        return False


def show_next_steps():
    """Display next steps"""
    print_header("NEXT STEPS")

    print("""
📊 Launch Interactive Dashboard:
   streamlit run dashboard.py

🔄 Run Full Data Collection:
   python taekwondo_scraper.py

📈 Generate Analysis Report:
   python performance_analyzer.py

🤖 Setup Automated Agents:
   python agents.py

📖 Read Documentation:
   See README.md for full details

---

🎯 Key Files:
   • taekwondo_scraper.py - Data collection from World Taekwondo
   • performance_analyzer.py - Analytics engine
   • dashboard.py - Interactive visualizations
   • agents.py - Automation and scheduling
   • models.py - Data structures

📁 Data Storage:
   • data/rankings/ - World rankings
   • data/athletes/ - Athlete profiles
   • data/competitions/ - Tournament results
   • reports/ - Generated analysis reports

---

💡 Tips:
   1. Run the scraper daily to keep data fresh
   2. Check reports/ folder for Excel analysis
   3. Use dashboard for interactive exploration
   4. Set up agents for automation

Happy Analyzing! 🥋
    """)


def main():
    """Main quick start workflow"""
    print("\n" + "🥋 "*20)
    print("SAUDI ARABIA TAEKWONDO PERFORMANCE ANALYSIS")
    print("Quick Start Setup")
    print("🥋 "*20)

    # Step 1: Check environment
    if not check_environment():
        print("\n⚠ Please install missing dependencies first")
        print("Run: pip install -r requirements.txt")
        return

    # Step 2: Create directories
    create_directories()

    # Step 3: Sample scrape
    print("\n⏳ This next step will scrape data from World Taekwondo...")
    user_input = input("Continue? (y/n): ").lower()

    if user_input == 'y':
        run_sample_scrape()

        # Step 4: Sample analysis
        run_sample_analysis()

    # Show next steps
    show_next_steps()

    print("\n✅ Quick start complete!")
    print("\nReady to analyze Saudi taekwondo performance! 🇸🇦\n")


if __name__ == "__main__":
    main()
