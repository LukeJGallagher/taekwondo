# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## System Overview

This is a **Saudi Arabia-focused Taekwondo Performance Analytics Platform** designed to support the national team's development under Vision 2030. The system scrapes World Taekwondo data, processes it into actionable insights, and provides automated analysis for Olympic qualification and medal opportunities.

**Core Data Pipeline**: Web Scraping → Validation → Storage (CSV/JSON) → Analysis → Dashboard/Reports/Alerts

## Essential Commands

### Initial Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Optional: PDF parsing for historical data
pip install camelot-py[cv] PyPDF2 tabula-py

# Configure environment (required for alerts)
copy .env.template .env
# Edit .env with SendGrid API key and alert emails
```

### Data Collection

**RECOMMENDED: Master Interface** (interactive menu):
```bash
python run_scraper_agent.py
# Select option 2: Incremental Update (fast, smart)
```

**Smart incremental updates** (10 seconds if unchanged, 90% faster):
```bash
python scraper_agent_incremental.py
# Only scrapes changed data with 30-day lookback
```

**Quick scrape** (1 minute, top 3 categories):
```bash
python scraper_agent_complete.py --max-pages 3
```

**Full autonomous scrape** (5 minutes, all categories):
```bash
python scraper_agent_complete.py
```

**Diagnostic testing** (visible browser, troubleshooting):
```bash
python scraper_diagnostic_agent.py --visible
```

**Populate dashboard data** (from scraped sources):
```bash
python populate_dashboard_data.py
```

**Legacy scrapers** (older, slower methods):
```bash
# First-time comprehensive scrape (20-40 minutes)
python scrape_all_categories.py

# Smart updates with auto-detection (1-5 minutes)
python scrape_all_data.py

# Force full refresh
python scrape_all_data.py --force-full --year-from 2020
```

### Analysis and Visualization

**Generate performance analysis** (Excel report with team analytics, benchmarking, opportunities):
```bash
python performance_analyzer.py
```

**Head-to-head matchup analysis**:
```bash
python head_to_head.py
```

**Data quality validation**:
```bash
python data_validator.py
```

**Launch interactive dashboard** (7 views with Saudi Olympic Committee theme):
```bash
streamlit run dashboard.py
# Opens browser at http://localhost:8501
# Views: Team Overview, Athlete Analysis, Rival Comparison,
# Medal Opportunities, Olympic Qualification, Ranking Trends, Competition Planning
```

### Automation

**Run automated agents** (continuous monitoring, scheduled scraping, automated reports):
```bash
python agents.py
```

**Test alert system**:
```bash
python alerts.py
```

**Free version** (no SendGrid required):
```bash
python alerts_free.py
```

### Quick Start

**Interactive setup wizard**:
```bash
python quick_start.py
```

## High-Level Architecture

### Data Flow

```
World Taekwondo Sources (Website/API/PDFs)
    ↓
Scraping Layer (scrape_all_categories.py, scrape_wt_detailed.py)
    ↓
Validation Layer (data_validator.py, Pydantic models)
    ↓
Storage Layer (CSV/JSON organized by category)
    ↓
Analysis Engine (performance_analyzer.py, head_to_head.py)
    ↓
Output Layer (dashboard.py, alerts.py, Excel reports)
```

### Component Architecture

**1. Scraping Layer**

*Autonomous Scraping Agents (Recommended):*
- `run_scraper_agent.py`: Master control interface for all agents
- `scraper_agent_incremental.py`: Smart incremental updates (90% faster, hash-based change detection, 30-day lookback)
- `scraper_agent_complete.py`: Production autonomous scraper with priority-based category scraping
- `scraper_diagnostic_agent.py`: Diagnostic agent for testing and troubleshooting
- `scraper_fix_agent.py`: Enhanced scraper with adaptive waits and fallback methods
- `download_all_taekwondo_data_fixed.py`: File downloader with 8-minute timeout protection
- `populate_dashboard_data.py`: Extracts athletes/matches from scraped data for dashboard

*Legacy Scrapers:*
- `scrape_all_categories.py`: Original master scraper for 24 categories
- `scrape_wt_detailed.py`: Detailed competition scraper using WT API
- `scrape_all_data.py`: Smart update system with incremental vs full logic
- `download_pdfs.py` & `extract_taekwondo_pdfs.py`: PDF result book processing

**2. Data Models** (`models.py`)
- Core entities: Athlete, Match, Competition, PerformanceMetrics, SaudiTeamAnalytics
- Weight categories: Men (8 categories: -54kg to +87kg), Women (8 categories: -46kg to +73kg)
- Dataclass-based with type hints for validation

**3. Analysis Engine** (`performance_analyzer.py`)
- Individual athlete performance analysis
- Saudi team analytics and benchmarking
- Rival country comparisons (Korea, Iran, Jordan, Turkey, China, UK, France, Mexico, UAE, Thailand)
- Medal opportunity identification with 0-100 scoring
- Analysis windows: 180-day recent form, 365-day trends

**4. Visualization** (`dashboard.py`)
- Interactive Streamlit dashboard with 7 views
- Saudi Olympic Committee theme colors (teal #007167, gold #a08e66)
- Plotly for dynamic charts with branded color palettes
- Excel export for comprehensive reports
- Real-time data updates with caching

**5. Automation** (`agents.py`)
- DataCollectionAgent: Daily rankings (06:00), weekly deep scrape (Monday 05:00)
- AnalysisAgent: Daily reports (07:00), ranking monitoring (07:15)
- CompetitionMonitorAgent: Deadline alerts (7/14/30 days before events)

**6. Alerts** (`alerts.py`)
- Email via SendGrid API
- Alert types: Ranking changes (±5 positions), medal opportunities (score ≥75), competition deadlines, upset losses
- Free version available (`alerts_free.py`) for logging without email

**7. Data Validation** (`data_validator.py`)
- Pydantic models for schema validation
- Great Expectations for data quality checks
- Quality scoring (0-100 scale)

### Data Storage Organization

**data/** - Dashboard-ready data (current):
- `athletes/` - Athlete records (from rankings)
  - `athletes_from_rankings.csv` - All ranked athletes
  - `saudi_athletes.csv` - Saudi-specific tracking
- `matches/` - Match records (from competitions)
  - `all_matches.csv` - Combined match data (10,831+ matches)
- `rankings/` - World rankings snapshots
  - `world_rankings_latest.csv` - Most recent rankings
- `competitions/` - Competition result files (44+ competitions)

**data_incremental/** - Incremental scraper output (recommended):
- `rankings/`, `olympics/`, `world_champs_senior/` - Category folders with timestamped CSVs
- `.scrape_history.json` - Metadata tracking last scrape/change per category
- `update_report_YYYYMMDD_HHMMSS.json` - Run statistics with change detection

**data_scraped/** - Autonomous agent output:
- Category folders: `rankings/`, `olympics/`, `world_champs_senior/`, `grand_prix/`, `grand_slam/`
- `scraping_report_*.json` - Run statistics

**data_all_categories/** - Legacy scraper output (24 category folders):
- `rankings/` - Current world rankings
- `olympics/` - Olympic Games results (2000-2024)
- `world_champs_senior/` - Senior World Championships (1973-2025)
- `grand_prix/`, `grand_slam/` - Major series events
- Youth: `world_champs_junior/`, `world_champs_u21/`, `world_champs_cadet/`, `world_champs_children/`
- Para: `paralympics/`, `world_champs_para/`
- Plus 10 more specialized categories

**data_wt_detailed/** - Individual competition files (48+ files):
- `{competition-slug}_results_table_0.csv` - Match results
- `{competition-slug}_medalists_table_0.csv` - Medal winners
- `{competition-slug}_data.json` - Competition metadata
- `scraping_summary.json` - Collection summary

**scraper_diagnostics/** - Diagnostic agent output:
- Screenshots, sample CSVs, diagnostic reports

**File naming convention**: Timestamped `{category}_{YYYYMMDD}.csv` or competition-based `{event-name-year}_data.json`

### Configuration

**config.py** - Centralized configuration:
- URLs for World Taekwondo endpoints
- Rival countries list (KOR, IRI, JOR, TUR, CHN, GBR, FRA, MEX, UAE, THA)
- Weight categories for all age groups
- Analysis windows and thresholds (180-day form, ±5 rank alert, 75+ opportunity score)
- Agent schedules
- Competition ranking points

**dashboard.py** - Theme colors (Saudi Olympic Committee branding):
- Primary teal: #007167, #096c64
- Gold accents: #a08e66, #9d8e65
- Chart palette: Teal/gold combinations

**.env** - Environment-specific settings (optional, required for alerts):
- SENDGRID_API_KEY - Email service
- ALERT_EMAILS - Comma-separated recipients
- Configurable thresholds (ranking change, opportunity score, data quality)

## Key Development Patterns

### Code Conventions
- **Dataclass-based models** - Use Python dataclasses with type hints for all data structures
- **Configuration centralization** - All settings in `config.py`, overridable via `.env`
- **Modular architecture** - Strict separation: scraping → validation → storage → analysis → output
- **Saudi-first focus** - KSA-specific features throughout (dedicated tracking, regional rivals, Vision 2030 alignment)

### Data Patterns
- **Timestamped files** - All data files include YYYYMMDD timestamp
- **Incremental updates** - Smart scraping with hash-based change detection (`.scrape_history.json` in `data_incremental/`)
- **30-day lookback** - Incremental scraper checks back 30 days for corrections/updates
- **Multiple formats** - CSV for tabular, JSON for structured/summary data
- **Hierarchical organization** - Category → Competition → Year → Data
- **Column name flexibility** - Code handles both `country`/`MEMBER NATION`, `rank`/`RANK` variations

### Analysis Patterns
- **Recent form window** - 180-day lookback for current performance
- **Opportunity scoring** - Weighted algorithm: rank (60%) + competition density (30%) + form (10%)
- **Rival benchmarking** - Fixed list of 10 key competitor nations
- **Quality thresholds** - Minimum 70/100 quality score for data acceptance

### Naming Conventions
- Classes: PascalCase (TaekwondoPerformanceAnalyzer)
- Functions: snake_case (analyze_saudi_athlete)
- Constants: UPPER_SNAKE_CASE (RIVAL_COUNTRIES)
- Files: snake_case.py (performance_analyzer.py)

## Important Context

### Data Volumes
- 2,077 total athlete records
- 464 unique athletes
- 128 countries
- 50+ years of World Championship history (1973-2025)
- 7 Olympic Games complete (Sydney 2000 - Paris 2024)
- 20+ Grand Prix/Grand Slam events

### Saudi Arabia Focus
The system is specifically designed for Saudi Arabian national team development:
- KSA athlete tracking and monitoring
- Regional rival benchmarking (Iran, Jordan, UAE, Turkey)
- Olympic qualification pathway tracking (LA 2028)
- Vision 2030 KPI alignment
- Arabic language support (planned)
- Budget/ROI optimization for competition selection

### Competition Tier Priority
The system prioritizes competitions by ranking points and strategic value:
1. Olympic Games (Priority: 1000)
2. World Championships (Priority: 950)
3. Grand Prix/Grand Slam (Priority: 800-900)
4. Continental Championships (Priority: 700-750)
5. President's Cup & Opens (Priority: 500-600)

### Weight Categories
Olympic categories are limited to 8 total (4 men, 4 women), while other competitions have 16 categories (8 per gender). The system handles both formats.

## Common Workflows

### Adding a New Scraper
1. Define data source in `config.py` (add URL endpoint)
2. Create scraper file following pattern: `scrape_{category}.py`
3. Use existing scrapers as templates (prefer `scrape_wt_detailed.py`)
4. Add validation using models from `models.py`
5. Store data following naming convention: `data_all_categories/{category}/`
6. Update `scrape_all_data.py` to include new category

### Adding a New Analysis
1. Import models from `models.py`
2. Load data from appropriate `data_all_categories/` subfolder
3. Use Pandas for data processing
4. Follow analysis window conventions (180-day form, 365-day trends)
5. Output to Excel or JSON following existing patterns
6. Add visualization to `dashboard.py` if needed

### Adding a New Alert Type
1. Define alert condition in `alerts.py`
2. Create alert message template
3. Add to appropriate agent in `agents.py` (DataCollection, Analysis, or CompetitionMonitor)
4. Test with `alerts_free.py` first (no email required)
5. Configure SendGrid for production email delivery

### Updating Dashboard
1. Dashboard uses Streamlit with 7 views (Team Overview, Athlete Analysis, Rival Comparison, Medal Opportunities, Olympic Qualification, Ranking Trends, Competition Planning)
2. Add new tab or section to existing view
3. Use Plotly for interactive charts with `THEME_COLORS` palette (teal/gold)
4. Follow Saudi Olympic Committee branding (primary: #007167, gold: #a08e66)
5. Handle column name variations (`country_col = 'country' if 'country' in df.columns else 'MEMBER NATION'`)
6. Ensure mobile-responsive design
7. Test with `streamlit run dashboard.py`
8. Always use UTF-8 encoding wrapper for Windows compatibility

### Populating Dashboard Data
After scraping, populate dashboard-ready data:
```bash
python populate_dashboard_data.py
```
This extracts:
- Athletes from `data/rankings/world_rankings_latest.csv` → `data/athletes/`
- Matches from `data/competitions/*results*.csv` → `data/matches/all_matches.csv`
- Saudi athlete tracking → `data/athletes/saudi_athletes.csv`

## Documentation References

The repository includes comprehensive documentation:
- **README.md** - Complete system overview and usage guide
- **QUICK_START_GUIDE.md** - 3-step getting started tutorial
- **TAEKWONDO_CONTEXT.md** - Deep dive into taekwondo sport structure, ranking system, and strategic context (essential reading for understanding analysis metrics)
- **IMPROVEMENT_ROADMAP.md** - Detailed 12-month enhancement plan (6 phases)
- **COMPLETE_SOLUTION.md** - Comprehensive solution architecture
- **FREE_SETUP_COMPLETE.md** - Setup guide without paid services
- **FINAL_SETUP_COMPLETE.md** - Complete setup summary with all 5 scraper agents
- **WEB_SCRAPER_README.md** - Quick start guide for scraper agents
- **SCRAPER_AGENT_SUMMARY.md** - Complete technical documentation for all agents
- **INCREMENTAL_SCRAPER_GUIDE.md** - Detailed guide for incremental scraper (recommended)
- **DASHBOARD_THEME_UPDATE.md** - Saudi Olympic Committee branding guide

## Known Issues and Considerations

### Scraping
- **Incremental scraper recommended** - Use `scraper_agent_incremental.py` for daily updates (90% faster)
- **Iframe handling** - Rankings use SimplyCompete iframe (2s optimal wait time)
- **Selenium required** - Chrome/Chromium browser needed for JavaScript-heavy pages
- **Rate limiting** - Default 1-second delay between requests (configurable)
- **Change detection** - Hash-based comparison prevents unnecessary saves
- **Metadata tracking** - `.scrape_history.json` in `data_incremental/` (delete to force re-scrape)
- **Timeout protection** - File downloader has 8-minute max runtime
- **Column name handling** - Always check for both `country`/`MEMBER NATION` variations

### Data Quality
- Minimum quality score: 70/100 (configurable)
- Data freshness threshold: 7 days (configurable)
- Validation runs automatically during scraping if `data_validator.py` is integrated
- Check `scraping_summary.json` for collection status

### Performance
- **Incremental scraper**: 10 seconds (no changes), ~1 minute (with changes)
- **Full autonomous scraper**: ~5 minutes for all categories
- **Legacy scrapers**: 20-40 minutes for comprehensive scrape
- **Dashboard load time**: 2-5 seconds for 10,831+ matches, 25+ athletes
- **Storage requirement**: ~500MB for comprehensive data
- **Performance gains**: 90% faster daily updates with incremental scraper

### Environment Setup
- **SendGrid API key** - Required for email alerts (optional - use `alerts_free.py` alternative)
- **Selenium** - Requires Chrome/Chromium browser (auto-downloads ChromeDriver for Chrome 142+)
- **PDF parsing** - Optional dependencies (camelot-py, tabula-py) for historical data
- **Windows encoding** - Always add UTF-8 wrapper to avoid Unicode errors:
  ```python
  import sys
  import io
  sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
  ```
- **Cross-platform** - Code handles both Windows backslashes and Unix forward slashes

## Testing

**Quick system health check**:
```bash
python quick_test.py
```

**Test data collection** (sample only):
```bash
python quick_start.py
```

**Validate data quality**:
```bash
python data_validator.py
```

**Test alerts** (without sending email):
```bash
python alerts_free.py
```

## Future Enhancements (Roadmap)

The system has a 6-phase improvement plan:
- **Phase 1** (Months 1-2): Enhanced validation, alerts, head-to-head, PDF parsing, Arabic support
- **Phase 2** (Months 3-4): ML predictions (XGBoost), ranking forecasting, competition optimizer
- **Phase 3** (Months 5-6): PostgreSQL migration, REST API (FastAPI), PowerPoint export
- **Phase 4** (Months 7-9): Azure deployment, Gracenote integration, budget optimization
- **Phase 5** (Months 10-12): Ranking simulation, network analysis, talent ID, mobile app
- **Phase 6** (12+ months): Live tracking, video analysis (CV), performance peak timing, AI coaching

When implementing new features, refer to IMPROVEMENT_ROADMAP.md for detailed specifications and prioritization.
