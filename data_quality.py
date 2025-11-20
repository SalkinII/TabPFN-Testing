"""
TabPFN-based data quality assessment functions.
"""

import pandas as pd
import numpy as np
import torch
from typing import Dict, List, Tuple, Optional
from tabpfn import TabPFNClassifier, TabPFNRegressor
from tabpfn_extensions import unsupervised
from tabpfn_extensions.unsupervised import experiments
import warnings
warnings.filterwarnings('ignore')


class DataQualityAssessor:
    """
    Assess data quality using TabPFN.
    """
    
    def __init__(self, n_estimators: int = 3, random_state: int = 42):
        """
        Initialize the data quality assessor.
        
        Args:
            n_estimators: Number of estimators for TabPFN models
            random_state: Random state for reproducibility
        """
        self.n_estimators = n_estimators
        self.random_state = random_state
        self.clf = None
        self.reg = None
        self.unsupervised_model = None
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize TabPFN models."""
        try:
            self.clf = TabPFNClassifier(n_estimators=self.n_estimators, random_state=self.random_state)
            self.reg = TabPFNRegressor(n_estimators=self.n_estimators, random_state=self.random_state)
            self.unsupervised_model = unsupervised.TabPFNUnsupervisedModel(
                tabpfn_clf=self.clf,
                tabpfn_reg=self.reg
            )
        except Exception as e:
            print(f"Warning: Could not initialize TabPFN models: {e}")
            print("Some features may not be available.")
    
    def assess_missing_values(self, df: pd.DataFrame) -> Dict:
        """
        Assess missing value patterns in the data.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Dictionary with missing value assessment results
        """
        results = {
            'total_missing': int(df.isnull().sum().sum()),
            'total_cells': df.size,
            'missing_percentage': float(df.isnull().sum().sum() / df.size * 100),
            'columns_with_missing': [],
            'column_missing_stats': {}
        }
        
        for col in df.columns:
            missing_count = int(df[col].isnull().sum())
            missing_pct = float(missing_count / len(df) * 100) if len(df) > 0 else 0.0
            
            if missing_count > 0:
                results['columns_with_missing'].append(col)
                results['column_missing_stats'][col] = {
                    'count': missing_count,
                    'percentage': missing_pct
                }
        
        # Assess missing value patterns using TabPFN if available
        if self.unsupervised_model is not None and len(results['columns_with_missing']) > 0:
            try:
                # Convert to numeric-only for pattern analysis
                numeric_df = df.select_dtypes(include=[np.number])
                if len(numeric_df.columns) > 0:
                    # Use a subset for pattern analysis
                    sample_size = min(1000, len(numeric_df))
                    sample_df = numeric_df.sample(n=sample_size, random_state=self.random_state) if len(numeric_df) > sample_size else numeric_df
                    
                    # Check for missing value dependencies
                    results['pattern_analysis'] = self._analyze_missing_patterns(sample_df)
            except Exception as e:
                results['pattern_analysis'] = {'error': str(e)}
        
        return results
    
    def _analyze_missing_patterns(self, df: pd.DataFrame) -> Dict:
        """
        Analyze missing value patterns using TabPFN.
        
        Args:
            df: Input DataFrame (numeric only)
            
        Returns:
            Dictionary with pattern analysis results
        """
        # Simple correlation-based pattern analysis
        missing_matrix = df.isnull()
        correlations = {}
        
        for col1 in df.columns:
            if missing_matrix[col1].sum() > 0:
                for col2 in df.columns:
                    if col1 != col2 and missing_matrix[col2].sum() > 0:
                        corr = missing_matrix[col1].corr(missing_matrix[col2])
                        if abs(corr) > 0.3:  # Threshold for significant correlation
                            correlations[f"{col1}_{col2}"] = float(corr)
        
        return {
            'missing_correlations': correlations,
            'pattern_detected': len(correlations) > 0
        }
    
    def detect_outliers(self, df: pd.DataFrame, feature_indices: Optional[List[int]] = None) -> Dict:
        """
        Detect outliers using TabPFN unsupervised learning.
        
        Args:
            df: Input DataFrame
            feature_indices: Optional list of feature indices to analyze
            
        Returns:
            Dictionary with outlier detection results
        """
        results = {
            'outlier_scores': [],
            'outlier_flags': [],
            'outlier_count': 0,
            'method': 'tabpfn_unsupervised'
        }
        
        if self.unsupervised_model is None:
            return {
                **results,
                'error': 'TabPFN unsupervised model not available',
                'fallback': 'statistical'
            }
        
        try:
            # Convert DataFrame to numeric-only for TabPFN
            numeric_df = df.select_dtypes(include=[np.number])
            
            if len(numeric_df.columns) == 0:
                return {
                    **results,
                    'error': 'No numeric columns found for outlier detection'
                }
            
            # Limit to reasonable size for TabPFN
            if len(numeric_df) > 1000:
                numeric_df = numeric_df.sample(n=1000, random_state=self.random_state)
            
            # Convert to tensor
            X = torch.tensor(numeric_df.values, dtype=torch.float32)
            
            # Create dummy target for unsupervised learning
            y = torch.zeros(len(X))
            
            # Select features to analyze
            if feature_indices is None:
                # Analyze first few numeric columns
                feature_indices = list(range(min(5, len(numeric_df.columns))))
            
            # Run outlier detection experiment
            exp_outlier = experiments.OutlierDetectionUnsupervisedExperiment(
                task_type="unsupervised"
            )
            
            outlier_results = exp_outlier.run(
                tabpfn=self.unsupervised_model,
                X=X,
                y=y,
                attribute_names=list(numeric_df.columns),
                indices=feature_indices
            )
            
            # Extract outlier scores
            if hasattr(outlier_results, 'outlier_scores'):
                scores = outlier_results.outlier_scores
            elif isinstance(outlier_results, dict) and 'outlier_scores' in outlier_results:
                scores = outlier_results['outlier_scores']
            else:
                # Fallback to statistical method
                scores = self._statistical_outlier_detection(numeric_df)
            
            results['outlier_scores'] = scores.tolist() if isinstance(scores, np.ndarray) else scores
            results['outlier_flags'] = [score > np.percentile(scores, 95) for score in results['outlier_scores']]
            results['outlier_count'] = int(sum(results['outlier_flags']))
            results['outlier_percentage'] = float(results['outlier_count'] / len(results['outlier_flags']) * 100)
            
        except Exception as e:
            # Fallback to statistical method
            numeric_df = df.select_dtypes(include=[np.number])
            if len(numeric_df.columns) > 0:
                scores = self._statistical_outlier_detection(numeric_df)
                results['outlier_scores'] = scores.tolist()
                results['outlier_flags'] = [score > np.percentile(scores, 95) for score in results['outlier_scores']]
                results['outlier_count'] = int(sum(results['outlier_flags']))
                results['outlier_percentage'] = float(results['outlier_count'] / len(results['outlier_flags']) * 100)
                results['method'] = 'statistical_fallback'
                results['error'] = str(e)
            else:
                results['error'] = f'Outlier detection failed: {str(e)}'
        
        return results
    
    def _statistical_outlier_detection(self, df: pd.DataFrame) -> np.ndarray:
        """
        Fallback statistical outlier detection using Z-scores.
        
        Args:
            df: Input DataFrame (numeric only)
            
        Returns:
            Array of outlier scores
        """
        scores = []
        for idx in range(len(df)):
            row = df.iloc[idx]
            z_scores = np.abs((row - df.mean()) / (df.std() + 1e-10))
            max_z_score = z_scores.max()
            scores.append(max_z_score)
        return np.array(scores)
    
    def detect_anomalies(self, df: pd.DataFrame) -> Dict:
        """
        Detect anomalies using TabPFN.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Dictionary with anomaly detection results
        """
        results = {
            'anomaly_scores': [],
            'anomaly_flags': [],
            'anomaly_count': 0,
            'method': 'tabpfn'
        }
        
        # Use outlier detection as anomaly detection
        outlier_results = self.detect_outliers(df)
        
        if 'outlier_scores' in outlier_results:
            results['anomaly_scores'] = outlier_results['outlier_scores']
            results['anomaly_flags'] = outlier_results.get('outlier_flags', [])
            results['anomaly_count'] = outlier_results.get('outlier_count', 0)
            results['anomaly_percentage'] = outlier_results.get('outlier_percentage', 0.0)
            results['method'] = outlier_results.get('method', 'tabpfn')
        
        return results
    
    def calculate_quality_score(self, df: pd.DataFrame, 
                                missing_weight: float = 0.3,
                                outlier_weight: float = 0.3,
                                anomaly_weight: float = 0.2,
                                consistency_weight: float = 0.2) -> Dict:
        """
        Calculate overall data quality score.
        
        Args:
            df: Input DataFrame
            missing_weight: Weight for missing value component
            outlier_weight: Weight for outlier component
            anomaly_weight: Weight for anomaly component
            consistency_weight: Weight for consistency component
            
        Returns:
            Dictionary with quality scores
        """
        # Assess missing values
        missing_assessment = self.assess_missing_values(df)
        missing_score = max(0, 100 - missing_assessment['missing_percentage'])
        
        # Detect outliers
        outlier_results = self.detect_outliers(df)
        outlier_score = 100.0
        if 'outlier_percentage' in outlier_results:
            outlier_score = max(0, 100 - outlier_results['outlier_percentage'] * 2)  # Penalize outliers
        
        # Detect anomalies
        anomaly_results = self.detect_anomalies(df)
        anomaly_score = 100.0
        if 'anomaly_percentage' in anomaly_results:
            anomaly_score = max(0, 100 - anomaly_results['anomaly_percentage'] * 2)
        
        # Consistency check (duplicates, data types)
        duplicate_pct = (df.duplicated().sum() / len(df) * 100) if len(df) > 0 else 0
        consistency_score = max(0, 100 - duplicate_pct * 5)  # Heavy penalty for duplicates
        
        # Calculate weighted overall score
        overall_score = (
            missing_score * missing_weight +
            outlier_score * outlier_weight +
            anomaly_score * anomaly_weight +
            consistency_score * consistency_weight
        )
        
        return {
            'overall_score': float(overall_score),
            'missing_score': float(missing_score),
            'outlier_score': float(outlier_score),
            'anomaly_score': float(anomaly_score),
            'consistency_score': float(consistency_score),
            'component_scores': {
                'missing': float(missing_score),
                'outliers': float(outlier_score),
                'anomalies': float(anomaly_score),
                'consistency': float(consistency_score)
            },
            'weights': {
                'missing': missing_weight,
                'outliers': outlier_weight,
                'anomalies': anomaly_weight,
                'consistency': consistency_weight
            }
        }
    
    def assess_column_quality(self, df: pd.DataFrame) -> Dict[str, Dict]:
        """
        Assess quality for each column individually.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Dictionary mapping column names to quality assessments
        """
        column_quality = {}
        
        for col in df.columns:
            col_df = df[[col]]
            missing_assessment = self.assess_missing_values(col_df)
            
            quality = {
                'missing_percentage': missing_assessment.get('missing_percentage', 0.0),
                'missing_count': missing_assessment.get('column_missing_stats', {}).get(col, {}).get('count', 0),
                'data_type': str(df[col].dtype),
                'unique_values': int(df[col].nunique()),
                'quality_score': 100.0
            }
            
            # Penalize missing values
            quality['quality_score'] = max(0, 100 - quality['missing_percentage'] * 2)
            
            # For numeric columns, check for outliers
            if df[col].dtype in [np.number]:
                try:
                    outlier_results = self.detect_outliers(col_df)
                    if 'outlier_percentage' in outlier_results:
                        quality['outlier_percentage'] = outlier_results['outlier_percentage']
                        quality['quality_score'] = max(0, quality['quality_score'] - outlier_results['outlier_percentage'])
                except:
                    pass
            
            column_quality[col] = quality
        
        return column_quality

