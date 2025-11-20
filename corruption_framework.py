"""
Data corruption framework for testing TabPFN detection capabilities.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import random
from datetime import datetime, timedelta
from utils import log_operation, ensure_logs_directory


class DataCorruptor:
    """
    Systematically corrupt data for testing TabPFN's detection capabilities.
    """
    
    def __init__(self, random_seed: int = 42):
        """
        Initialize the data corruptor.
        
        Args:
            random_seed: Random seed for reproducibility
        """
        self.random_seed = random_seed
        np.random.seed(random_seed)
        random.seed(random_seed)
        self.corruption_log = []
    
    def introduce_missing_values(self, df: pd.DataFrame, 
                                 missing_percentage: float = 10.0,
                                 columns: Optional[List[str]] = None,
                                 pattern: str = 'random') -> Tuple[pd.DataFrame, Dict]:
        """
        Introduce missing values into the DataFrame.
        
        Args:
            df: Input DataFrame
            missing_percentage: Percentage of values to make missing (0-100)
            columns: List of column names to corrupt (None = all columns)
            pattern: Pattern of missingness ('random', 'column_specific', 'row_specific')
            
        Returns:
            Tuple of (corrupted_dataframe, corruption_details)
        """
        corrupted_df = df.copy()
        total_cells = df.size
        
        if columns is None:
            columns = list(df.columns)
        
        corruption_details = {
            'type': 'missing_values',
            'missing_percentage': missing_percentage,
            'columns_affected': columns,
            'pattern': pattern,
            'random_seed': self.random_seed,
            'affected_cells': [],
            'original_missing': int(df.isnull().sum().sum())
        }
        
        if pattern == 'random':
            # Random missingness across all selected columns
            n_missing = int(total_cells * missing_percentage / 100)
            for col in columns:
                if col in df.columns:
                    col_missing = int(len(df) * missing_percentage / 100)
                    missing_indices = np.random.choice(
                        len(df), 
                        size=min(col_missing, len(df)), 
                        replace=False
                    )
                    corrupted_df.loc[missing_indices, col] = np.nan
                    corruption_details['affected_cells'].extend([
                        {'row': int(idx), 'column': col} for idx in missing_indices
                    ])
        
        elif pattern == 'column_specific':
            # More missing in specific columns
            for col in columns:
                if col in df.columns:
                    col_pct = missing_percentage * np.random.uniform(0.5, 1.5)
                    col_missing = int(len(df) * col_pct / 100)
                    missing_indices = np.random.choice(
                        len(df),
                        size=min(col_missing, len(df)),
                        replace=False
                    )
                    corrupted_df.loc[missing_indices, col] = np.nan
                    corruption_details['affected_cells'].extend([
                        {'row': int(idx), 'column': col} for idx in missing_indices
                    ])
        
        elif pattern == 'row_specific':
            # More missing in specific rows
            n_rows_to_corrupt = int(len(df) * missing_percentage / 100)
            rows_to_corrupt = np.random.choice(
                len(df),
                size=min(n_rows_to_corrupt, len(df)),
                replace=False
            )
            for row_idx in rows_to_corrupt:
                cols_to_corrupt = np.random.choice(
                    columns,
                    size=min(len(columns), int(len(columns) * 0.3)),
                    replace=False
                )
                for col in cols_to_corrupt:
                    if col in df.columns:
                        corrupted_df.loc[row_idx, col] = np.nan
                        corruption_details['affected_cells'].append({
                            'row': int(row_idx),
                            'column': col
                        })
        
        corruption_details['new_missing'] = int(corrupted_df.isnull().sum().sum())
        corruption_details['timestamp'] = datetime.now().isoformat()
        
        # Log the corruption
        log_file = log_operation('corruption', corruption_details)
        corruption_details['log_file'] = log_file
        self.corruption_log.append(corruption_details)
        
        return corrupted_df, corruption_details
    
    def introduce_outliers(self, df: pd.DataFrame,
                           outlier_percentage: float = 5.0,
                           columns: Optional[List[str]] = None,
                           outlier_type: str = 'statistical') -> Tuple[pd.DataFrame, Dict]:
        """
        Introduce outliers into numeric columns.
        
        Args:
            df: Input DataFrame
            outlier_percentage: Percentage of values to make outliers
            columns: List of column names to corrupt (None = all numeric columns)
            outlier_type: Type of outlier ('statistical', 'extreme', 'clinical')
            
        Returns:
            Tuple of (corrupted_dataframe, corruption_details)
        """
        corrupted_df = df.copy()
        
        if columns is None:
            columns = list(df.select_dtypes(include=[np.number]).columns)
        
        corruption_details = {
            'type': 'outliers',
            'outlier_percentage': outlier_percentage,
            'columns_affected': columns,
            'outlier_type': outlier_type,
            'random_seed': self.random_seed,
            'affected_cells': [],
            'original_values': {}
        }
        
        for col in columns:
            if col not in df.columns or df[col].dtype not in [np.number]:
                continue
            
            col_data = df[col].dropna()
            if len(col_data) == 0:
                continue
            
            mean_val = col_data.mean()
            std_val = col_data.std()
            
            n_outliers = int(len(df) * outlier_percentage / 100)
            outlier_indices = np.random.choice(
                len(df),
                size=min(n_outliers, len(df)),
                replace=False
            )
            
            for idx in outlier_indices:
                original_value = corrupted_df.loc[idx, col]
                corruption_details['original_values'][f"{idx}_{col}"] = float(original_value) if pd.notna(original_value) else None
                
                if outlier_type == 'statistical':
                    # Values beyond 3-5 standard deviations
                    multiplier = np.random.uniform(3, 5)
                    if np.random.random() > 0.5:
                        outlier_value = mean_val + multiplier * std_val
                    else:
                        outlier_value = mean_val - multiplier * std_val
                
                elif outlier_type == 'extreme':
                    # Very extreme values
                    multiplier = np.random.uniform(5, 10)
                    outlier_value = mean_val + multiplier * std_val if np.random.random() > 0.5 else mean_val - multiplier * std_val
                
                elif outlier_type == 'clinical':
                    # Clinically implausible but statistically possible
                    # For example, age > 150, negative values where not expected
                    if 'age' in col.lower():
                        outlier_value = np.random.uniform(150, 200)
                    elif 'weight' in col.lower() or 'height' in col.lower():
                        outlier_value = original_value * np.random.uniform(5, 10) if pd.notna(original_value) else mean_val * 10
                    else:
                        multiplier = np.random.uniform(4, 6)
                        outlier_value = mean_val + multiplier * std_val
                
                corrupted_df.loc[idx, col] = outlier_value
                corruption_details['affected_cells'].append({
                    'row': int(idx),
                    'column': col,
                    'original': float(original_value) if pd.notna(original_value) else None,
                    'outlier': float(outlier_value)
                })
        
        corruption_details['timestamp'] = datetime.now().isoformat()
        
        # Log the corruption
        log_file = log_operation('corruption', corruption_details)
        corruption_details['log_file'] = log_file
        self.corruption_log.append(corruption_details)
        
        return corrupted_df, corruption_details
    
    def introduce_duplicates(self, df: pd.DataFrame,
                             duplicate_percentage: float = 5.0) -> Tuple[pd.DataFrame, Dict]:
        """
        Introduce duplicate rows.
        
        Args:
            df: Input DataFrame
            duplicate_percentage: Percentage of rows to duplicate
            
        Returns:
            Tuple of (corrupted_dataframe, corruption_details)
        """
        corrupted_df = df.copy()
        
        n_duplicates = int(len(df) * duplicate_percentage / 100)
        rows_to_duplicate = np.random.choice(
            len(df),
            size=min(n_duplicates, len(df)),
            replace=False
        )
        
        duplicate_rows = df.iloc[rows_to_duplicate].copy()
        corrupted_df = pd.concat([corrupted_df, duplicate_rows], ignore_index=True)
        
        corruption_details = {
            'type': 'duplicates',
            'duplicate_percentage': duplicate_percentage,
            'rows_duplicated': [int(idx) for idx in rows_to_duplicate],
            'n_duplicates_added': len(duplicate_rows),
            'random_seed': self.random_seed,
            'timestamp': datetime.now().isoformat()
        }
        
        # Log the corruption
        log_file = log_operation('corruption', corruption_details)
        corruption_details['log_file'] = log_file
        self.corruption_log.append(corruption_details)
        
        return corrupted_df, corruption_details
    
    def introduce_inconsistencies(self, df: pd.DataFrame,
                                  inconsistency_percentage: float = 5.0,
                                  columns: Optional[List[str]] = None) -> Tuple[pd.DataFrame, Dict]:
        """
        Introduce data inconsistencies (format issues, invalid values).
        
        Args:
            df: Input DataFrame
            inconsistency_percentage: Percentage of values to corrupt
            columns: List of column names to corrupt
            
        Returns:
            Tuple of (corrupted_dataframe, corruption_details)
        """
        corrupted_df = df.copy()
        
        if columns is None:
            columns = list(df.select_dtypes(include=['object']).columns)
        
        corruption_details = {
            'type': 'inconsistencies',
            'inconsistency_percentage': inconsistency_percentage,
            'columns_affected': columns,
            'random_seed': self.random_seed,
            'affected_cells': []
        }
        
        for col in columns:
            if col not in df.columns:
                continue
            
            n_inconsistent = int(len(df) * inconsistency_percentage / 100)
            inconsistent_indices = np.random.choice(
                len(df),
                size=min(n_inconsistent, len(df)),
                replace=False
            )
            
            for idx in inconsistent_indices:
                original_value = corrupted_df.loc[idx, col]
                
                # Introduce format inconsistencies
                if pd.notna(original_value):
                    # Add random characters, change case, etc.
                    if isinstance(original_value, str):
                        corrupted_value = original_value.upper() + "###" if np.random.random() > 0.5 else original_value.lower() + "!!!"
                    else:
                        corrupted_value = str(original_value) + "INVALID"
                else:
                    corrupted_value = "MISSING_VALUE"
                
                corrupted_df.loc[idx, col] = corrupted_value
                corruption_details['affected_cells'].append({
                    'row': int(idx),
                    'column': col,
                    'original': str(original_value) if pd.notna(original_value) else None,
                    'corrupted': str(corrupted_value)
                })
        
        corruption_details['timestamp'] = datetime.now().isoformat()
        
        # Log the corruption
        log_file = log_operation('corruption', corruption_details)
        corruption_details['log_file'] = log_file
        self.corruption_log.append(corruption_details)
        
        return corrupted_df, corruption_details
    
    def apply_maximum_corruption(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
        """
        Apply all corruption types at maximum levels for testing.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Tuple of (corrupted_dataframe, all_corruption_details)
        """
        corrupted_df = df.copy()
        all_details = {
            'type': 'maximum_combined_corruption',
            'corruptions_applied': [],
            'timestamp': datetime.now().isoformat()
        }
        
        # Apply all corruption types
        corrupted_df, missing_details = self.introduce_missing_values(
            corrupted_df, missing_percentage=30.0, pattern='random'
        )
        all_details['corruptions_applied'].append(missing_details)
        
        corrupted_df, outlier_details = self.introduce_outliers(
            corrupted_df, outlier_percentage=10.0, outlier_type='statistical'
        )
        all_details['corruptions_applied'].append(outlier_details)
        
        corrupted_df, duplicate_details = self.introduce_duplicates(
            corrupted_df, duplicate_percentage=10.0
        )
        all_details['corruptions_applied'].append(duplicate_details)
        
        corrupted_df, inconsistency_details = self.introduce_inconsistencies(
            corrupted_df, inconsistency_percentage=10.0
        )
        all_details['corruptions_applied'].append(inconsistency_details)
        
        # Log combined corruption
        log_file = log_operation('corruption', all_details)
        all_details['log_file'] = log_file
        
        return corrupted_df, all_details
    
    def get_corruption_summary(self) -> Dict:
        """
        Get a summary of all corruptions applied.
        
        Returns:
            Dictionary with corruption summary
        """
        return {
            'total_corruptions': len(self.corruption_log),
            'corruption_types': list(set([c['type'] for c in self.corruption_log])),
            'corruption_log': self.corruption_log
        }

