"""
System Test Script
Verifies that all components of the Taekwondo Analytics system are working
"""

import sys
from pathlib import Path

def test_imports():
    """Test that all required modules can be imported"""
    print("\n" + "="*80)
    print("1. TESTING IMPORTS")
    print("="*80)
    
    try:
        import streamlit
        print("  OK: streamlit")
    except ImportError as e:
        print(f"  ERROR: streamlit - {e}")
        return False
    
    try:
        import pandas
        print("  OK: pandas")
    except ImportError as e:
        print(f"  ERROR: pandas - {e}")
        return False
    
    try:
        import plotly
        print("  OK: plotly")
    except ImportError as e:
        print(f"  ERROR: plotly - {e}")
        return False
    
    try:
        import schedule
        print("  OK: schedule")
    except ImportError as e:
        print(f"  ERROR: schedule - {e}")
        return False
    
    try:
        from dotenv import load_dotenv
        print("  OK: python-dotenv")
    except ImportError as e:
        print(f"  ERROR: python-dotenv - {e}")
        return False
    
    return True


def test_modules():
    """Test that all custom modules can be imported"""
    print("\n" + "="*80)
    print("2. TESTING CUSTOM MODULES")
    print("="*80)
    
    try:
        from models import Athlete, WeightCategory
        print("  OK: models.py")
    except ImportError as e:
        print(f"  ERROR: models.py - {e}")
        return False
    
    try:
        from performance_analyzer import TaekwondoPerformanceAnalyzer
        print("  OK: performance_analyzer.py")
    except ImportError as e:
        print(f"  ERROR: performance_analyzer.py - {e}")
        return False
    
    try:
        from taekwondo_scraper import TaekwondoDataScraper
        print("  OK: taekwondo_scraper.py")
    except ImportError as e:
        print(f"  ERROR: taekwondo_scraper.py - {e}")
        return False
    
    try:
        from agents import AgentOrchestrator
        print("  OK: agents.py")
    except ImportError as e:
        print(f"  ERROR: agents.py - {e}")
        return False
    
    try:
        from alerts_free import AlertSystemFree
        print("  OK: alerts_free.py")
    except ImportError as e:
        print(f"  ERROR: alerts_free.py - {e}")
        return False
    
    try:
        import dashboard
        print("  OK: dashboard.py")
    except ImportError as e:
        print(f"  ERROR: dashboard.py - {e}")
        return False
    
    return True


def test_directories():
    """Test that required directories exist"""
    print("\n" + "="*80)
    print("3. TESTING DIRECTORY STRUCTURE")
    print("="*80)
    
    required_dirs = [
        "data",
        "data/athletes",
        "data/rankings",
        "data/competitions",
        "data/matches"
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists():
            print(f"  OK: {dir_path}/")
        else:
            print(f"  ERROR: {dir_path}/ does not exist")
            all_exist = False
    
    return all_exist


def test_config():
    """Test that configuration files exist"""
    print("\n" + "="*80)
    print("4. TESTING CONFIGURATION")
    print("="*80)
    
    config_files = [
        ".env",
        "requirements.txt",
        "models.py",
        "config.py" if Path("config.py").exists() else None
    ]
    
    all_exist = True
    for file_path in config_files:
        if file_path is None:
            continue
        path = Path(file_path)
        if path.exists():
            print(f"  OK: {file_path}")
        else:
            print(f"  WARNING: {file_path} not found")
            if file_path == ".env":
                all_exist = False
    
    return all_exist


def test_functionality():
    """Test basic functionality"""
    print("\n" + "="*80)
    print("5. TESTING FUNCTIONALITY")
    print("="*80)
    
    try:
        from performance_analyzer import TaekwondoPerformanceAnalyzer
        analyzer = TaekwondoPerformanceAnalyzer(data_dir="data")
        print("  OK: Performance analyzer initialization")
        
        team_analytics = analyzer.analyze_saudi_team()
        print(f"  OK: Team analytics (found {team_analytics.total_active_athletes} athletes)")
        
    except Exception as e:
        print(f"  ERROR: Performance analyzer - {e}")
        return False
    
    try:
        from alerts_free import AlertSystemFree
        alert_system = AlertSystemFree()
        print("  OK: Alert system initialization")
    except Exception as e:
        print(f"  ERROR: Alert system - {e}")
        return False
    
    return True


def main():
    """Run all tests"""
    print("\n" + "#"*80)
    print("# SAUDI ARABIA TAEKWONDO ANALYTICS - SYSTEM TEST")
    print("#"*80)
    
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("Custom Modules", test_modules()))
    results.append(("Directory Structure", test_directories()))
    results.append(("Configuration", test_config()))
    results.append(("Functionality", test_functionality()))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    all_passed = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        symbol = "OK" if passed else "!!"
        print(f"  [{symbol}] {name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "="*80)
    if all_passed:
        print("SUCCESS: All tests passed!")
        print("\nNext steps:")
        print("  1. Run a scraper to collect data:")
        print("     python scrape_all_data.py")
        print("\n  2. Launch the dashboard:")
        print("     streamlit run dashboard.py")
        print("\n  3. Or run automated agents:")
        print("     python agents.py")
    else:
        print("WARNING: Some tests failed. Please address the errors above.")
        return 1
    
    print("="*80)
    return 0


if __name__ == "__main__":
    sys.exit(main())
