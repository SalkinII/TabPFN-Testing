"""
Clinical-specific data quality checks.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime


class ClinicalQualityChecker:
    """
    Check for clinical-specific data quality issues.
    """
    
    def __init__(self):
        """Initialize the clinical quality checker."""
        pass
    
    def check_impossible_values(self, df: pd.DataFrame) -> Dict:
        """
        Check for impossible value combinations.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Dictionary with impossible value checks
        """
        issues = []
        
        # Check for impossible ages
        age_columns = [col for col in df.columns if 'age' in col.lower()]
        for col in age_columns:
            if df[col].dtype in [np.number]:
                impossible_ages = df[df[col] > 150][col]
                if len(impossible_ages) > 0:
                    issues.append({
                        'type': 'impossible_age',
                        'column': col,
                        'count': len(impossible_ages),
                        'values': impossible_ages.tolist()[:10]  # First 10
                    })
                
                negative_ages = df[df[col] < 0][col]
                if len(negative_ages) > 0:
                    issues.append({
                        'type': 'negative_age',
                        'column': col,
                        'count': len(negative_ages),
                        'values': negative_ages.tolist()[:10]
                    })
        
        # Check for impossible dates (future dates for birth, etc.)
        date_columns = [col for col in df.columns if 'date' in col.lower() or 'birth' in col.lower()]
        current_date = datetime.now()
        
        for col in date_columns:
            try:
                if df[col].dtype == 'object':
                    date_series = pd.to_datetime(df[col], errors='coerce')
                    future_dates = date_series[date_series > current_date]
                    if len(future_dates) > 0:
                        issues.append({
                            'type': 'future_date',
                            'column': col,
                            'count': len(future_dates)
                        })
            except:
                pass
        
        return {
            'total_issues': len(issues),
            'issues': issues,
            'has_issues': len(issues) > 0
        }
    
    def check_temporal_consistency(self, df: pd.DataFrame,
                                   start_col: Optional[str] = None,
                                   end_col: Optional[str] = None) -> Dict:
        """
        Check for temporal inconsistencies (e.g., discharge before admission).
        
        Args:
            df: Input DataFrame
            start_col: Column name for start date/time
            end_col: Column name for end date/time
            
        Returns:
            Dictionary with temporal consistency checks
        """
        issues = []
        
        # Try to find date columns automatically
        if start_col is None or end_col is None:
            date_cols = [col for col in df.columns if 'date' in col.lower() or 'time' in col.lower()]
            
            # Look for common patterns
            start_keywords = ['start', 'begin', 'admission', 'admit']
            end_keywords = ['end', 'finish', 'discharge', 'discharge']
            
            for col in date_cols:
                col_lower = col.lower()
                if any(kw in col_lower for kw in start_keywords):
                    start_col = col
                if any(kw in col_lower for kw in end_keywords):
                    end_col = col
        
        if start_col and end_col and start_col in df.columns and end_col in df.columns:
            try:
                start_dates = pd.to_datetime(df[start_col], errors='coerce')
                end_dates = pd.to_datetime(df[end_col], errors='coerce')
                
                invalid = (end_dates < start_dates) & start_dates.notna() & end_dates.notna()
                
                if invalid.sum() > 0:
                    issues.append({
                        'type': 'end_before_start',
                        'start_column': start_col,
                        'end_column': end_col,
                        'count': int(invalid.sum()),
                        'rows': df[invalid].index.tolist()[:10]
                    })
            except Exception as e:
                issues.append({
                    'type': 'temporal_check_error',
                    'error': str(e)
                })
        
        return {
            'total_issues': len(issues),
            'issues': issues,
            'has_issues': len(issues) > 0
        }
    
    def check_referential_integrity(self, df: pd.DataFrame,
                                   id_column: Optional[str] = None) -> Dict:
        """
        Check referential integrity (e.g., missing IDs, orphaned records).
        
        Args:
            df: Input DataFrame
            id_column: Column name for ID (if None, tries to find automatically)
            
        Returns:
            Dictionary with referential integrity checks
        """
        issues = []
        
        # Find ID column
        if id_column is None:
            id_candidates = [col for col in df.columns if 'id' in col.lower() or 'key' in col.lower()]
            if id_candidates:
                id_column = id_candidates[0]
        
        if id_column and id_column in df.columns:
            # Check for missing IDs
            missing_ids = df[id_column].isnull().sum()
            if missing_ids > 0:
                issues.append({
                    'type': 'missing_ids',
                    'column': id_column,
                    'count': int(missing_ids)
                })
            
            # Check for duplicate IDs
            duplicate_ids = df[id_column].duplicated().sum()
            if duplicate_ids > 0:
                issues.append({
                    'type': 'duplicate_ids',
                    'column': id_column,
                    'count': int(duplicate_ids)
                })
        
        return {
            'total_issues': len(issues),
            'issues': issues,
            'has_issues': len(issues) > 0
        }
    
    def check_clinical_plausibility(self, df: pd.DataFrame) -> Dict:
        """
        Check for clinically implausible values.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Dictionary with clinical plausibility checks
        """
        issues = []
        
        # Check BMI if weight and height exist
        weight_cols = [col for col in df.columns if 'weight' in col.lower()]
        height_cols = [col for col in df.columns if 'height' in col.lower()]
        
        if weight_cols and height_cols:
            weight_col = weight_cols[0]
            height_col = height_cols[0]
            
            if df[weight_col].dtype in [np.number] and df[height_col].dtype in [np.number]:
                # Calculate BMI (assuming height in meters or convert from cm)
                height_m = df[height_col] / 100 if df[height_col].max() > 3 else df[height_col]
                bmi = df[weight_col] / (height_m ** 2)
                
                # Check for implausible BMI values
                implausible_bmi = bmi[(bmi < 10) | (bmi > 60)]
                if len(implausible_bmi) > 0:
                    issues.append({
                        'type': 'implausible_bmi',
                        'count': len(implausible_bmi),
                        'values': implausible_bmi.tolist()[:10]
                    })
        
        # Check for negative values where not expected
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if 'count' in col.lower() or 'number' in col.lower():
                negative_values = df[df[col] < 0][col]
                if len(negative_values) > 0:
                    issues.append({
                        'type': 'negative_count',
                        'column': col,
                        'count': len(negative_values)
                    })
        
        return {
            'total_issues': len(issues),
            'issues': issues,
            'has_issues': len(issues) > 0
        }
    
    def run_all_checks(self, df: pd.DataFrame) -> Dict:
        """
        Run all clinical quality checks.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Dictionary with all check results
        """
        results = {
            'impossible_values': self.check_impossible_values(df),
            'temporal_consistency': self.check_temporal_consistency(df),
            'referential_integrity': self.check_referential_integrity(df),
            'clinical_plausibility': self.check_clinical_plausibility(df)
        }
        
        total_issues = sum([
            results['impossible_values']['total_issues'],
            results['temporal_consistency']['total_issues'],
            results['referential_integrity']['total_issues'],
            results['clinical_plausibility']['total_issues']
        ])
        
        results['total_issues'] = total_issues
        results['has_issues'] = total_issues > 0
        
        return results

