"""
Data Validation and Quality Checks
Ensures scraped data meets quality standards
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class DataQualityIssue(Enum):
    """Types of data quality issues"""
    MISSING_VALUE = "Missing required value"
    INVALID_FORMAT = "Invalid data format"
    OUTLIER = "Statistical outlier detected"
    DUPLICATE = "Duplicate record"
    STALE_DATA = "Data is outdated"


class AthleteValidator(BaseModel):
    """Pydantic model for athlete data validation"""
    athlete_id: str = Field(..., min_length=1, description="Unique athlete identifier")
    name: str = Field(..., min_length=2, description="Athlete full name")
    country: str = Field(..., min_length=2, max_length=3, description="ISO country code")
    gender: str = Field(..., regex="^[MF]$", description="M or F")
    weight_category: Optional[str] = None
    rank: Optional[int] = Field(None, ge=1, le=1000, description="World rank 1-1000")
    points: Optional[float] = Field(None, ge=0, description="Ranking points (non-negative)")

    @validator('country')
    def country_must_be_uppercase(cls, v):
        return v.upper()

    @validator('rank', 'points')
    def check_consistency(cls, v, values):
        """Rank and points should be consistent"""
        # If rank is very low (good), points should be high
        if 'rank' in values and values['rank'] and v:
            rank = values['rank']
            points = v if 'points' in values else 0

            # Basic sanity check
            if rank == 1 and points < 100:
                raise ValueError("Rank #1 should have >100 points")

        return v


class MatchValidator(BaseModel):
    """Pydantic model for match data validation"""
    match_id: str
    athlete1_id: str
    athlete2_id: str
    winner_id: str
    athlete1_score: int = Field(..., ge=0, le=100, description="Score 0-100")
    athlete2_score: int = Field(..., ge=0, le=100, description="Score 0-100")
    date: datetime

    @validator('winner_id')
    def winner_must_be_participant(cls, v, values):
        """Winner must be one of the two athletes"""
        if 'athlete1_id' in values and 'athlete2_id' in values:
            if v not in [values['athlete1_id'], values['athlete2_id']]:
                raise ValueError("Winner must be athlete1 or athlete2")
        return v

    @validator('athlete2_score')
    def check_score_logic(cls, v, values):
        """Winner should have higher score (unless KO/DQ)"""
        if 'athlete1_score' in values and 'winner_id' in values:
            athlete1_score = values['athlete1_score']

            # If scores are equal, something is wrong
            if v == athlete1_score:
                raise ValueError("Scores cannot be equal (no ties in taekwondo)")

        return v


class DataQualityChecker:
    """
    Comprehensive data quality checking system
    Identifies and reports data issues
    """

    def __init__(self, logger=None):
        self.issues = []
        self.logger = logger

    def validate_athlete_data(self, athlete_dict: dict) -> tuple[bool, List[str]]:
        """
        Validate single athlete record

        Returns:
            (is_valid, list_of_errors)
        """
        try:
            AthleteValidator(**athlete_dict)
            return True, []

        except Exception as e:
            errors = [str(e)]
            self.issues.append({
                'type': DataQualityIssue.INVALID_FORMAT,
                'record': athlete_dict,
                'error': str(e)
            })
            return False, errors

    def validate_match_data(self, match_dict: dict) -> tuple[bool, List[str]]:
        """
        Validate single match record

        Returns:
            (is_valid, list_of_errors)
        """
        try:
            MatchValidator(**match_dict)
            return True, []

        except Exception as e:
            errors = [str(e)]
            self.issues.append({
                'type': DataQualityIssue.INVALID_FORMAT,
                'record': match_dict,
                'error': str(e)
            })
            return False, errors

    def check_missing_values(self, df, required_columns: List[str]) -> List[dict]:
        """Check for missing required values in DataFrame"""
        missing_issues = []

        for col in required_columns:
            if col in df.columns:
                missing_count = df[col].isna().sum()

                if missing_count > 0:
                    missing_issues.append({
                        'type': DataQualityIssue.MISSING_VALUE,
                        'column': col,
                        'count': int(missing_count),
                        'percentage': round((missing_count / len(df)) * 100, 2)
                    })

        return missing_issues

    def check_duplicates(self, df, id_column: str) -> List[dict]:
        """Check for duplicate records"""
        duplicate_issues = []

        if id_column in df.columns:
            duplicates = df[df.duplicated(subset=[id_column], keep=False)]

            if not duplicates.empty:
                duplicate_issues.append({
                    'type': DataQualityIssue.DUPLICATE,
                    'column': id_column,
                    'count': len(duplicates),
                    'duplicate_ids': duplicates[id_column].unique().tolist()
                })

        return duplicate_issues

    def check_outliers(self, df, column: str, std_threshold: float = 3.0) -> List[dict]:
        """Detect statistical outliers using z-score method"""
        outlier_issues = []

        if column in df.columns and df[column].dtype in ['int64', 'float64']:
            mean = df[column].mean()
            std = df[column].std()

            if std > 0:  # Avoid division by zero
                z_scores = ((df[column] - mean) / std).abs()
                outliers = df[z_scores > std_threshold]

                if not outliers.empty:
                    outlier_issues.append({
                        'type': DataQualityIssue.OUTLIER,
                        'column': column,
                        'count': len(outliers),
                        'mean': round(mean, 2),
                        'std': round(std, 2),
                        'outlier_values': outliers[column].tolist()
                    })

        return outlier_issues

    def check_data_freshness(self, df, date_column: str, max_age_days: int = 7) -> List[dict]:
        """Check if data is recent enough"""
        freshness_issues = []

        if date_column in df.columns:
            df[date_column] = pd.to_datetime(df[date_column], errors='coerce')
            latest_date = df[date_column].max()

            if pd.notna(latest_date):
                age_days = (datetime.now() - latest_date).days

                if age_days > max_age_days:
                    freshness_issues.append({
                        'type': DataQualityIssue.STALE_DATA,
                        'column': date_column,
                        'latest_date': latest_date.isoformat(),
                        'age_days': age_days,
                        'threshold_days': max_age_days
                    })

        return freshness_issues

    def run_full_quality_check(self, df, config: dict) -> dict:
        """
        Run comprehensive quality checks

        Args:
            df: DataFrame to check
            config: {
                'required_columns': [...],
                'id_column': 'athlete_id',
                'date_column': 'scraped_date',
                'numeric_columns': ['rank', 'points'],
                'max_age_days': 7
            }

        Returns:
            Quality report dictionary
        """
        report = {
            'total_records': len(df),
            'timestamp': datetime.now().isoformat(),
            'issues': {
                'missing_values': [],
                'duplicates': [],
                'outliers': [],
                'stale_data': []
            },
            'quality_score': 100.0
        }

        # Check missing values
        if 'required_columns' in config:
            report['issues']['missing_values'] = self.check_missing_values(
                df, config['required_columns']
            )

        # Check duplicates
        if 'id_column' in config:
            report['issues']['duplicates'] = self.check_duplicates(
                df, config['id_column']
            )

        # Check outliers
        if 'numeric_columns' in config:
            for col in config['numeric_columns']:
                outliers = self.check_outliers(df, col)
                report['issues']['outliers'].extend(outliers)

        # Check data freshness
        if 'date_column' in config:
            report['issues']['stale_data'] = self.check_data_freshness(
                df, config['date_column'], config.get('max_age_days', 7)
            )

        # Calculate quality score
        total_issues = sum(len(v) for v in report['issues'].values())
        issue_penalty = min(total_issues * 5, 50)  # Max 50% penalty
        report['quality_score'] = max(0, 100 - issue_penalty)

        return report

    def print_quality_report(self, report: dict):
        """Print formatted quality report"""
        print("\n" + "="*70)
        print("DATA QUALITY REPORT")
        print("="*70)
        print(f"\nTotal Records: {report['total_records']}")
        print(f"Quality Score: {report['quality_score']:.1f}/100")
        print(f"Timestamp: {report['timestamp']}\n")

        for issue_type, issues in report['issues'].items():
            if issues:
                print(f"\n{issue_type.upper().replace('_', ' ')}:")
                for issue in issues:
                    print(f"  - {issue}")

        if report['quality_score'] >= 90:
            print("\n✅ EXCELLENT - Data quality is very high")
        elif report['quality_score'] >= 70:
            print("\n⚠️  GOOD - Minor quality issues detected")
        elif report['quality_score'] >= 50:
            print("\n⚠️  FAIR - Moderate quality issues, review recommended")
        else:
            print("\n❌ POOR - Significant quality issues, immediate attention required")

        print("="*70 + "\n")


# Example usage
if __name__ == "__main__":
    import pandas as pd

    # Example athlete data validation
    checker = DataQualityChecker()

    athlete = {
        'athlete_id': 'KSA001',
        'name': 'Ahmed Ali',
        'country': 'ksa',  # Will be auto-converted to uppercase
        'gender': 'M',
        'rank': 45,
        'points': 125.5
    }

    is_valid, errors = checker.validate_athlete_data(athlete)
    print(f"Athlete valid: {is_valid}")
    if errors:
        print(f"Errors: {errors}")

    # Example DataFrame quality check
    sample_df = pd.DataFrame([
        {'athlete_id': 'KSA001', 'name': 'Ahmed', 'rank': 45, 'points': 125.5},
        {'athlete_id': 'KSA002', 'name': 'Fahad', 'rank': 67, 'points': 98.2},
        {'athlete_id': 'KSA001', 'name': 'Ahmed', 'rank': 45, 'points': 125.5},  # Duplicate
    ])

    config = {
        'required_columns': ['athlete_id', 'name', 'rank'],
        'id_column': 'athlete_id',
        'numeric_columns': ['rank', 'points']
    }

    report = checker.run_full_quality_check(sample_df, config)
    checker.print_quality_report(report)
