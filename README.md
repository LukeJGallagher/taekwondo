# Saudi Arabia Taekwondo Performance Analysis System

A comprehensive data science platform for analyzing taekwondo performance with a focus on Saudi Arabian athletes. This system scrapes World Taekwondo data, performs advanced analytics, and provides actionable insights for performance improvement and strategic planning.

## Features

### 1. Data Collection (Web Scraping)
- **World Rankings**: Automated scraping of current world rankings across all weight categories
- **Competition Results**: Detailed match data, brackets, and tournament results
- **Athlete Profiles**: Individual athlete statistics, competition history, and achievements
- **Saudi Focus**: Dedicated tracking of all Saudi Arabian athletes

### 2. Performance Analytics
- **Individual Analysis**: Comprehensive metrics for each athlete
  - Win/loss records and trends
  - Performance by competition level
  - Head-to-head records
  - Technical statistics (when available)

- **Team Analytics**: National team insights
  - Ranking distribution
  - Medal counts and trends
  - Weight category strength analysis
  - Development pipeline tracking

- **Benchmarking**: Comparison against rival nations
  - South Korea, Iran, Jordan, Turkey, China, UK, France, Mexico
  - Ranking metrics
  - Medal comparisons
  - Competitive positioning

### 3. Strategic Intelligence
- **Medal Opportunities**: Identification of weight categories with highest medal potential
- **Competition Planning**: Recommendations on which tournaments to prioritize
- **Ranking Point Optimization**: Strategic guidance for ranking point accumulation
- **Opponent Analysis**: Insights on common competitors

### 4. Visualization Dashboard
- Interactive Streamlit dashboard
- Real-time metrics and KPIs
- Comparative visualizations
- Exportable reports

### 5. Automation Agents
- Scheduled data collection
- Automated reporting
- Ranking change alerts
- Urgent opportunity identification

## Project Structure

```
Taekwondo/
├── taekwondo_scraper.py      # Main scraper for World Taekwondo data
├── models.py                  # Data models and schemas
├── performance_analyzer.py    # Analytics engine
├── dashboard.py              # Streamlit visualization dashboard
├── agents.py                 # Automation and scheduling
├── requirements.txt          # Python dependencies
├── data/                     # Scraped data storage
│   ├── competitions/
│   ├── athletes/
│   ├── rankings/
│   └── matches/
├── reports/                  # Generated analysis reports
└── result_books/            # Downloaded PDFs (legacy)
```

## Installation

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Verify Installation**
```bash
python -c "import requests, pandas, streamlit; print('All dependencies installed!')"
```

## Quick Start

### Step 1: Collect Data

```bash
# Run the scraper to collect current data
python taekwondo_scraper.py
```

This will:
- Scrape world rankings for all weight categories
- Collect Saudi athlete profiles
- Download recent competition results
- Save data to `data/` directory

### Step 2: Run Analysis

```bash
# Generate performance analysis
python performance_analyzer.py
```

This will:
- Analyze team performance
- Benchmark against rivals
- Identify medal opportunities
- Export comprehensive Excel report

### Step 3: Launch Dashboard

```bash
# Start interactive dashboard
streamlit run dashboard.py
```

Open browser to `http://localhost:8501` to view:
- Team overview
- Individual athlete analysis
- Rival comparisons
- Medal opportunity analysis
- Competition planning

### Step 4: Setup Automation (Optional)

```bash
# Run automated agents
python agents.py
```

For continuous monitoring, configure as a scheduled task or service.

## Usage Examples

### Analyze Specific Athlete

```python
from performance_analyzer import TaekwondoPerformanceAnalyzer

analyzer = TaekwondoPerformanceAnalyzer(data_dir="data")

# Get metrics for a Saudi athlete
metrics = analyzer.analyze_saudi_athlete("Athlete Name")

print(f"Recent Win Rate: {metrics.recent_win_rate}%")
print(f"Matches: {metrics.recent_matches}")
```

### Compare with Rivals

```python
# Benchmark against key competitors
rivals_df = analyzer.benchmark_against_rivals()
print(rivals_df)
```

### Identify Medal Opportunities

```python
# Find best medal chances
opportunities = analyzer.identify_medal_opportunities()

for opp in opportunities[:5]:
    print(f"{opp['weight_category']}: {opp['athlete_name']}")
    print(f"  Current Rank: #{opp['current_rank']}")
    print(f"  Opportunity Score: {opp['opportunity_score']}/100")
```

### Export Full Report

```python
# Generate comprehensive Excel report
analyzer.export_analysis_report("saudi_analysis.xlsx")
```

## Data Models

### Athlete
- Personal information (name, country, birth date)
- Physical attributes (weight category, height, reach)
- Rankings and points
- Career statistics (matches, wins, losses, medals)
- Competition history

### Match
- Competition and date
- Opponent details
- Round-by-round scoring
- Win type (points, knockout, etc.)
- Technical statistics (kicks, punches, penalties)

### Competition
- Event details (name, level, dates, location)
- Participating athletes and countries
- Match results
- Medal table

### Performance Metrics
- Recent form (6-month window)
- Competition level performance
- Opponent strength analysis
- Technical performance metrics
- Trends and trajectories

## Saudi-Specific Focus

This system is optimized for Saudi Arabia's national taekwondo program:

1. **All Saudi Athletes**: Comprehensive tracking of every Saudi competitor
2. **Regional Context**: Analysis within Asian and Middle Eastern context
3. **Strategic Rivals**: Focus on key competitor nations (Iran, Jordan, etc.)
4. **Olympic Qualification**: Tracking paths to Olympic qualification
5. **Development Pipeline**: Identifying and monitoring emerging talent
6. **Competition Strategy**: Optimal tournament selection for ranking points

## Key Insights Provided

### Team Level
- Current strength distribution across weight categories
- Ranking trends over time
- Medal performance vs. targets
- Comparison with regional and global competitors
- Development areas requiring investment

### Athlete Level
- Form and momentum analysis
- Optimal competition schedule
- Strengths and weaknesses
- Head-to-head records
- Training focus recommendations

### Strategic
- Medal opportunity ranking by category
- Competition prioritization (Olympic qualifiers, Worlds, Grand Prix, etc.)
- Ranking point optimization strategies
- Opponent scouting intelligence

## Competition Levels (Prioritization)

1. **Olympic Games** - Maximum priority, qualification critical
2. **World Championships** - Highest ranking points, global prestige
3. **Grand Prix/Grand Slam** - Strong ranking points, international exposure
4. **Continental Championships** - Regional dominance, qualification pathway
5. **President's Cup/Opens** - Development opportunities, experience building

## Weight Categories Tracked

**Men's Categories:**
- -54kg, -58kg, -63kg, -68kg, -74kg, -80kg, -87kg, +87kg

**Women's Categories:**
- -46kg, -49kg, -53kg, -57kg, -62kg, -67kg, -73kg, +73kg

## Automation Schedule

Default agent schedules:

- **Daily 06:00** - Update world rankings and Saudi profiles
- **Daily 07:00** - Generate performance report
- **Daily 08:00** - Check upcoming competitions
- **Weekly Monday 05:00** - Deep scrape (all competitions and matches)
- **Weekly Monday 09:00** - Identify urgent opportunities

## Output Reports

### Daily Report (Excel)
- Team Overview sheet
- Rival Comparison sheet
- Medal Opportunities sheet
- Recommended Competitions sheet
- Current Saudi Rankings sheet

### Dashboard Views
1. Team Overview - KPIs, medal distribution, ranking breakdown
2. Athlete Analysis - Individual performance metrics
3. Rival Comparison - Benchmarking visualization
4. Medal Opportunities - Ranked opportunities with scores
5. Competition Planning - Strategic recommendations

## Data Sources

- **World Taekwondo**: https://www.worldtaekwondo.org
  - Official rankings
  - Competition results
  - Athlete profiles
  - Result books

## Troubleshooting

### No Data Showing in Dashboard
- Run `python taekwondo_scraper.py` first to collect data
- Check `data/` directory for CSV files

### Scraper Not Finding Athletes
- World Taekwondo website structure may have changed
- Check `agents.log` for error details
- May need to update CSS selectors in scraper

### Missing Rankings
- Rankings updated weekly by World Taekwondo
- Run scraper on Monday-Tuesday for latest data

## Future Enhancements

- [ ] PDF result book parsing for historical data
- [ ] Machine learning predictions (match outcomes, ranking trajectories)
- [ ] Social media sentiment analysis
- [ ] Injury tracking and availability
- [ ] Training load integration
- [ ] Video analysis integration
- [ ] Mobile app version
- [ ] Real-time competition tracking
- [ ] Automated alerts (email/SMS/WhatsApp)

## License

Internal use for Saudi Arabia Sports Authority / Team Saudi

## Contact & Support

For questions or support, contact the Sports Analytics team.

---

**Built for Saudi Arabia Taekwondo National Team**
*Data-driven performance excellence*
