"""
Configuration file for Taekwondo Performance Analysis System
Customize settings here
"""

# === DATA COLLECTION SETTINGS ===

# Scraping parameters
SCRAPE_CONFIG = {
    'start_year': 2020,  # How far back to scrape competitions
    'focus_saudi': True,  # Prioritize Saudi athlete data
    'max_competitions_per_run': 50,  # Limit to avoid overwhelming
    'delay_between_requests': 1.0,  # Seconds to wait (be nice to servers)
    'timeout': 30,  # Request timeout in seconds
}

# World Taekwondo URLs
WT_URLS = {
    'base': 'https://www.worldtaekwondo.org',
    'rankings': 'https://www.worldtaekwondo.org/competition/ranking.html',
    'competitions': 'https://www.worldtaekwondo.org/competition/list.html',
    'athletes': 'https://www.worldtaekwondo.org/athlete/list.html',
    'search_saudi': 'https://www.worldtaekwondo.org/athlete/list.html?country=KSA',
}

# === ANALYSIS SETTINGS ===

# Countries to benchmark against (Global)
RIVAL_COUNTRIES = [
    'KOR',  # South Korea - Global powerhouse
    'IRI',  # Iran - Regional rival
    'JOR',  # Jordan - Regional rival
    'TUR',  # Turkey - Regional competitor
    'CHN',  # China - Asian powerhouse
    'GBR',  # Great Britain - European leader
    'FRA',  # France - European power
    'MEX',  # Mexico - Americas leader
    'UAE',  # UAE - Gulf competitor
    'THA',  # Thailand - Asian competitor
]

# Asian rivals specifically (for Asian Games focus)
ASIAN_RIVALS = [
    'KOR',  # South Korea - Dominant force
    'CHN',  # China - Major contender
    'IRI',  # Iran - Regional powerhouse
    'JPN',  # Japan - Host nation 2026
    'JOR',  # Jordan - Regional rival
    'UZB',  # Uzbekistan - Rising power
    'THA',  # Thailand - Consistent performer
    'KAZ',  # Kazakhstan - Strong program
    'TPE',  # Chinese Taipei - Competitive
    'VIE',  # Vietnam - Emerging
]

# All Asian countries (for continental rankings)
ASIAN_COUNTRIES = [
    'KOR', 'CHN', 'IRI', 'JPN', 'JOR', 'UZB', 'THA', 'KAZ', 'TPE', 'VIE',
    'KSA', 'UAE', 'KUW', 'QAT', 'BRN', 'OMA', 'IND', 'PAK', 'MAS', 'SIN',
    'IDN', 'PHI', 'MGL', 'PRK', 'HKG', 'MAC', 'MYA', 'LAO', 'CAM', 'BRU',
    'TJK', 'KGZ', 'TKM', 'AFG', 'NPL', 'BAN', 'SRI', 'MDV'
]

# Weight categories (all 16)
WEIGHT_CATEGORIES = {
    'M': ['-54kg', '-58kg', '-63kg', '-68kg', '-74kg', '-80kg', '-87kg', '+87kg'],
    'F': ['-46kg', '-49kg', '-53kg', '-57kg', '-62kg', '-67kg', '-73kg', '+73kg']
}

# Olympic weight categories (only 8 total at Olympics)
OLYMPIC_CATEGORIES = {
    'M': ['-58kg', '-68kg', '-80kg', '+80kg'],
    'F': ['-49kg', '-57kg', '-67kg', '+67kg']
}

# Performance analysis windows
ANALYSIS_WINDOWS = {
    'recent_form': 180,  # Days for "recent form" (6 months)
    'trend_short': 180,  # Short-term trend (6 months)
    'trend_long': 365,   # Long-term trend (12 months)
}

# Medal opportunity scoring
OPPORTUNITY_CONFIG = {
    'rank_weight': 0.6,        # How much ranking matters (0-1)
    'competition_weight': 0.3,  # How much competition density matters
    'form_weight': 0.1,        # How much recent form matters
    'min_rank_for_opportunity': 30,  # Don't show opportunities beyond rank 30
}

# === DASHBOARD SETTINGS ===

DASHBOARD_CONFIG = {
    'title': 'Saudi Arabia Taekwondo Analytics',
    'icon': '🥋',
    'theme': 'green',  # Saudi colors
    'refresh_interval': 3600,  # Seconds between auto-refresh
    'top_n_opportunities': 10,  # Show top N medal opportunities
}

# Colors (Saudi Arabia theme)
COLORS = {
    'primary': '#1e4d2b',      # Saudi green
    'secondary': '#ffffff',     # White
    'gold': '#FFD700',
    'silver': '#C0C0C0',
    'bronze': '#CD7F32',
    'success': '#28a745',
    'warning': '#ffc107',
    'danger': '#dc3545',
    'info': '#17a2b8',
}

# === AUTOMATION SETTINGS ===

AGENT_SCHEDULE = {
    'daily_scrape': '06:00',           # Daily data update
    'daily_analysis': '07:00',         # Daily report generation
    'ranking_check': '07:15',          # Check for ranking changes
    'weekly_deep_scrape': 'MON 05:00', # Weekly comprehensive scrape
    'weekly_insights': 'MON 09:00',    # Weekly strategic insights
}

# === REPORTING SETTINGS ===

REPORT_CONFIG = {
    'output_format': 'excel',  # 'excel', 'pdf', 'both'
    'include_charts': True,
    'include_raw_data': True,
    'highlight_improvements': True,
    'highlight_concerns': True,
}

# Report distribution (future feature)
DISTRIBUTION = {
    'email_enabled': False,
    'recipients': [
        # 'coach@example.com',
        # 'analyst@example.com',
    ],
    'email_subject': 'Daily Taekwondo Performance Report',
}

# === DATA STORAGE ===

DATA_DIRS = {
    'base': 'data',
    'competitions': 'data/competitions',
    'athletes': 'data/athletes',
    'rankings': 'data/rankings',
    'matches': 'data/matches',
    'reports': 'reports',
    'logs': 'logs',
}

# === ALERTS & NOTIFICATIONS ===

ALERTS = {
    'ranking_change_threshold': 5,     # Alert if rank changes by more than this
    'new_opportunity_threshold': 75,   # Alert if opportunity score above this
    'upset_loss_alert': True,          # Alert on loss to lower-ranked opponent
    'medal_alert': True,               # Alert on any medal won
}

# === ADVANCED SETTINGS ===

# Competition level ranking points (relative scale)
COMPETITION_RANKING_POINTS = {
    'Olympic Games': 100,
    'World Championships': 95,
    'Grand Prix': 80,
    'Grand Slam': 80,
    "President's Cup": 70,
    'Continental Championships': 75,
    'Open': 50,
    'National Championships': 20,
}

# Match statistics to track (if available)
MATCH_STATS = [
    'head_kicks',
    'body_kicks',
    'punches',
    'spinning_kicks',
    'penalties',
    'knockdowns',
    'video_replays',
]

# === DEBUGGING ===

DEBUG = {
    'verbose_logging': False,
    'save_raw_html': False,  # Save scraped HTML for debugging
    'test_mode': False,      # Limit scraping for testing
    'test_limit': 5,         # Number of items to process in test mode
}

# === ASIAN GAMES 2026 CONFIGURATION ===

ASIAN_GAMES_2026 = {
    'name': 'Asian Games 2026',
    'host_city': 'Nagoya',
    'host_country': 'Japan',
    'start_date': '2026-09-19',
    'end_date': '2026-10-04',
    'qualification_deadline': '2026-07-01',  # Estimated
    'weight_categories': {
        'M': ['-54kg', '-58kg', '-63kg', '-68kg', '-74kg', '-80kg', '-87kg', '+87kg'],
        'F': ['-46kg', '-49kg', '-53kg', '-57kg', '-62kg', '-67kg', '-73kg', '+73kg']
    },
    # Qualification quotas (estimated based on previous games)
    'quotas': {
        'total_per_country': 8,  # Max athletes per NOC
        'per_category': 1,       # 1 athlete per weight category
    },
    # Key qualifying events
    'qualifying_events': [
        'Asian Championships 2025',
        'Asian Championships 2026',
        'Asian Qualification Tournament',
    ]
}

# LA 2028 Olympics Configuration
LA_2028_OLYMPICS = {
    'name': 'LA 2028 Olympics',
    'host_city': 'Los Angeles',
    'host_country': 'USA',
    'start_date': '2028-07-14',
    'end_date': '2028-07-30',
    'qualification_deadline': '2028-06-30',
    'weight_categories': {
        'M': ['-58kg', '-68kg', '-80kg', '+80kg'],
        'F': ['-49kg', '-57kg', '-67kg', '+67kg']
    },
    # Qualification paths
    'qualification_paths': {
        'automatic': {'min_rank': 5, 'spots': 5},      # Top 5 world ranking
        'continental': {'spots_per_continent': 2},     # Continental qualification
        'tripartite': {'spots': 2},                    # Wild card invitation
    }
}

# Dual-track timeline milestones
DUAL_TRACK_MILESTONES = [
    # Asian Games Track
    {'event': 'Asian Championships 2025', 'date': '2025-05-01', 'track': 'asian_games', 'importance': 'high'},
    {'event': 'Grand Prix Series 2025', 'date': '2025-06-01', 'track': 'both', 'importance': 'high'},
    {'event': 'World Championships 2025', 'date': '2025-09-01', 'track': 'both', 'importance': 'critical'},
    {'event': 'Asian Championships 2026', 'date': '2026-05-01', 'track': 'asian_games', 'importance': 'critical'},
    {'event': 'Asian Games Qualification Deadline', 'date': '2026-07-01', 'track': 'asian_games', 'importance': 'critical'},
    {'event': 'Asian Games 2026', 'date': '2026-09-19', 'track': 'asian_games', 'importance': 'critical'},

    # Olympics Track
    {'event': 'Grand Prix Series 2026', 'date': '2026-03-01', 'track': 'olympics', 'importance': 'high'},
    {'event': 'World Championships 2027', 'date': '2027-09-01', 'track': 'olympics', 'importance': 'critical'},
    {'event': 'Grand Prix Series 2027', 'date': '2027-03-01', 'track': 'olympics', 'importance': 'high'},
    {'event': 'Grand Prix Series 2028', 'date': '2028-01-01', 'track': 'olympics', 'importance': 'high'},
    {'event': 'Olympic Qualification Deadline', 'date': '2028-06-30', 'track': 'olympics', 'importance': 'critical'},
    {'event': 'LA 2028 Olympics', 'date': '2028-07-14', 'track': 'olympics', 'importance': 'critical'},
]

# === VERSION INFO ===

VERSION = '2.0.0'
LAST_UPDATED = '2026-01-20'
AUTHOR = 'Saudi Arabia Sports Analytics Team'
