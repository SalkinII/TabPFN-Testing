"""
Utility functions for the TabPFN Data Quality Assessment Dashboard.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import json
import os


def validate_csv_file(file_path: str) -> Tuple[bool, str]:
    """
    Validate that a file is a valid CSV file.
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Try to read the first few rows
        df = pd.read_csv(file_path, nrows=5)
        if df.empty:
            return False, "CSV file is empty"
        return True, ""
    except Exception as e:
        return False, f"Error reading CSV file: {str(e)}"


def get_data_types(df: pd.DataFrame) -> Dict[str, str]:
    """
    Get data types for each column in a DataFrame.
    
    Args:
        df: Input DataFrame
        
    Returns:
        Dictionary mapping column names to data types
    """
    type_mapping = {
        'int64': 'integer',
        'float64': 'float',
        'object': 'string',
        'bool': 'boolean',
        'datetime64[ns]': 'datetime',
        'category': 'categorical'
    }
    
    return {col: type_mapping.get(str(dtype), 'unknown') 
            for col, dtype in df.dtypes.items()}


def calculate_basic_stats(df: pd.DataFrame) -> Dict:
    """
    Calculate basic statistics for a DataFrame.
    
    Args:
        df: Input DataFrame
        
    Returns:
        Dictionary with basic statistics
    """
    stats = {
        'total_rows': len(df),
        'total_columns': len(df.columns),
        'total_cells': df.size,
        'missing_values': int(df.isnull().sum().sum()),
        'missing_percentage': float(df.isnull().sum().sum() / df.size * 100),
        'duplicate_rows': int(df.duplicated().sum()),
        'duplicate_percentage': float(df.duplicated().sum() / len(df) * 100) if len(df) > 0 else 0.0
    }
    
    # Column-level stats
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) > 0:
        stats['numeric_columns'] = len(numeric_cols)
        stats['numeric_missing'] = int(df[numeric_cols].isnull().sum().sum())
    else:
        stats['numeric_columns'] = 0
        stats['numeric_missing'] = 0
    
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns
    if len(categorical_cols) > 0:
        stats['categorical_columns'] = len(categorical_cols)
        stats['categorical_missing'] = int(df[categorical_cols].isnull().sum().sum())
    else:
        stats['categorical_columns'] = 0
        stats['categorical_missing'] = 0
    
    return stats


def ensure_logs_directory(subfolder: Optional[str] = None) -> str:
    """
    Ensure the logs directory exists, optionally in a subfolder.
    
    Args:
        subfolder: Optional subfolder name (e.g., 'dev', 'prod')
        
    Returns:
        Path to the logs directory
    """
    logs_dir = os.path.join(os.path.dirname(__file__), 'logs')
    if subfolder:
        logs_dir = os.path.join(logs_dir, subfolder)
    os.makedirs(logs_dir, exist_ok=True)
    return logs_dir


def log_operation(operation_type: str, details: Dict, log_dir: Optional[str] = None, 
                  subfolder: Optional[str] = None) -> str:
    """
    Log an operation to a JSON file.
    
    Args:
        operation_type: Type of operation (e.g., 'corruption', 'assessment')
        details: Dictionary with operation details
        log_dir: Directory to save logs (defaults to logs/ or logs/{subfolder})
        subfolder: Optional subfolder name (e.g., 'dev', 'prod')
        
    Returns:
        Path to the log file
    """
    if log_dir is None:
        log_dir = ensure_logs_directory(subfolder)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"{operation_type}_{timestamp}.json")
    
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'operation_type': operation_type,
        'details': details
    }
    
    with open(log_file, 'w') as f:
        json.dump(log_entry, f, indent=2)
    
    return log_file


def log_dev_event(event_type: str, message: str, details: Optional[Dict] = None) -> str:
    """
    Log a development event to logs/dev/ folder.
    
    Args:
        event_type: Type of event (e.g., 'startup', 'error', 'file_upload')
        message: Human-readable message
        details: Optional additional details dictionary
        
    Returns:
        Path to the log file
    """
    log_details = {
        'message': message,
        **(details or {})
    }
    return log_operation(event_type, log_details, subfolder='dev')


def log_error(error: Exception, context: Optional[Dict] = None) -> str:
    """
    Log an error to logs/dev/ folder.
    
    Args:
        error: Exception object
        context: Optional context dictionary
        
    Returns:
        Path to the log file
    """
    error_details = {
        'error_type': type(error).__name__,
        'error_message': str(error),
        'context': context or {}
    }
    return log_dev_event('error', f"{type(error).__name__}: {str(error)}", error_details)


def format_quality_score(score: float) -> Tuple[str, str]:
    """
    Format a quality score with color coding.
    
    Args:
        score: Quality score (0-100)
        
    Returns:
        Tuple of (formatted_score, color_class)
    """
    if score >= 80:
        color = "success"  # Green
    elif score >= 60:
        color = "warning"  # Yellow
    elif score >= 40:
        color = "info"  # Blue
    else:
        color = "danger"  # Red
    
    return f"{score:.1f}", color


def get_dataset_info(df: pd.DataFrame) -> Dict:
    """
    Extract dataset information for logging purposes.
    
    Args:
        df: Input DataFrame
        
    Returns:
        Dictionary with dataset characteristics
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns
    
    return {
        'rows': len(df),
        'columns': len(df.columns),
        'numeric_columns': len(numeric_cols),
        'categorical_columns': len(categorical_cols),
        'missing_cells': int(df.isnull().sum().sum()),
        'missing_percentage': float(df.isnull().sum().sum() / df.size * 100) if df.size > 0 else 0.0
    }


def log_tabpfn_fallback(reason: str, context: Dict, dataset_info: Optional[Dict] = None) -> str:
    """
    Log when TabPFN falls back to statistical methods.
    
    Args:
        reason: Reason for fallback (e.g., 'no_numeric_columns', 'initialization_failure', 'processing_exception')
        context: Context dictionary with method, fallback_method, error details, etc.
        dataset_info: Optional dataset information dictionary
        
    Returns:
        Path to the log file
    """
    log_entry = {
        'event_type': 'tabpfn_fallback',
        'reason': reason,
        'context': context,
        'dataset_info': dataset_info or {}
    }
    return log_operation('tabpfn_fallback', log_entry, subfolder='dev')


def log_tabpfn_error(error: Exception, context: Dict, dataset_info: Optional[Dict] = None) -> str:
    """
    Log TabPFN-specific errors.
    
    Args:
        error: Exception object
        context: Context dictionary with method, operation, etc.
        dataset_info: Optional dataset information dictionary
        
    Returns:
        Path to the log file
    """
    error_details = {
        'event_type': 'tabpfn_error',
        'error_type': type(error).__name__,
        'error_message': str(error),
        'context': context,
        'dataset_info': dataset_info or {}
    }
    return log_operation('tabpfn_error', error_details, subfolder='dev')


def log_tabpfn_success(method: str, dataset_info: Optional[Dict] = None, metrics: Optional[Dict] = None) -> str:
    """
    Log successful TabPFN usage.
    
    Args:
        method: Method used (e.g., 'outlier_detection', 'anomaly_detection')
        dataset_info: Optional dataset information dictionary
        metrics: Optional metrics dictionary (e.g., processing time, scores)
        
    Returns:
        Path to the log file
    """
    log_entry = {
        'event_type': 'tabpfn_success',
        'method': method,
        'dataset_info': dataset_info or {},
        'metrics': metrics or {}
    }
    return log_operation('tabpfn_success', log_entry, subfolder='dev')
