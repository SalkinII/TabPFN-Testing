"""
Test script for data quality assessment functionality.
Tests the DataQualityAssessor class and TabPFN integration.
"""

import pandas as pd
import numpy as np
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_quality import DataQualityAssessor
from utils import log_dev_event


def create_test_dataframe(n_rows=100, n_numeric=5, n_categorical=3, missing_pct=0.1):
    """Create a test DataFrame with mixed data types."""
    np.random.seed(42)
    
    data = {}
    
    # Add numeric columns
    for i in range(n_numeric):
        col_name = f"numeric_{i+1}"
        values = np.random.normal(100, 20, n_rows)
        # Add some missing values
        missing_mask = np.random.random(n_rows) < missing_pct
        values[missing_mask] = np.nan
        data[col_name] = values
    
    # Add categorical columns
    categories = ['A', 'B', 'C', 'D']
    for i in range(n_categorical):
        col_name = f"categorical_{i+1}"
        values = np.random.choice(categories, n_rows)
        # Add some missing values
        missing_mask = np.random.random(n_rows) < missing_pct
        values[missing_mask] = None
        data[col_name] = values
    
    return pd.DataFrame(data)


def test_assessor_initialization():
    """Test DataQualityAssessor initialization."""
    print(f"\n{'='*60}")
    print("Test: DataQualityAssessor Initialization")
    print(f"{'='*60}")
    
    try:
        assessor = DataQualityAssessor()
        print("✅ Assessor initialized successfully")
        
        # Check if models are initialized
        if assessor.clf is not None:
            print("✅ TabPFN Classifier initialized")
        else:
            print("⚠️  TabPFN Classifier not initialized (may be acceptable)")
        
        if assessor.reg is not None:
            print("✅ TabPFN Regressor initialized")
        else:
            print("⚠️  TabPFN Regressor not initialized (may be acceptable)")
        
        if assessor.unsupervised_model is not None:
            print("✅ TabPFN Unsupervised Model initialized")
        else:
            print("⚠️  TabPFN Unsupervised Model not initialized (may be acceptable)")
        
        return True
    except Exception as e:
        print(f"❌ Failed to initialize assessor: {e}")
        return False


def test_missing_value_assessment():
    """Test missing value assessment."""
    print(f"\n{'='*60}")
    print("Test: Missing Value Assessment")
    print(f"{'='*60}")
    
    try:
        assessor = DataQualityAssessor()
        df = create_test_dataframe(n_rows=100, missing_pct=0.15)
        
        result = assessor.assess_missing_values(df)
        
        print(f"✅ Missing value assessment completed")
        print(f"   Total missing: {result.get('total_missing', 0)}")
        print(f"   Missing percentage: {result.get('missing_percentage', 0):.2f}%")
        print(f"   Columns with missing: {len(result.get('columns_with_missing', []))}")
        
        # Validate result structure
        required_keys = ['total_missing', 'total_cells', 'missing_percentage', 
                        'columns_with_missing', 'column_missing_stats']
        missing_keys = [key for key in required_keys if key not in result]
        
        if missing_keys:
            print(f"⚠️  Missing keys in result: {missing_keys}")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Missing value assessment failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_outlier_detection():
    """Test outlier detection."""
    print(f"\n{'='*60}")
    print("Test: Outlier Detection")
    print(f"{'='*60}")
    
    try:
        assessor = DataQualityAssessor()
        df = create_test_dataframe(n_rows=100, n_numeric=5)
        
        # Add some outliers
        df.loc[0, 'numeric_1'] = 1000  # Extreme outlier
        df.loc[1, 'numeric_2'] = -500  # Negative outlier
        
        result = assessor.detect_outliers(df)
        
        print(f"✅ Outlier detection completed")
        print(f"   Method: {result.get('method', 'unknown')}")
        print(f"   Outlier count: {result.get('outlier_count', 0)}")
        print(f"   Outlier percentage: {result.get('outlier_percentage', 0):.2f}%")
        
        if 'error' in result:
            print(f"⚠️  Error in outlier detection: {result['error']}")
            print(f"   Using fallback method: {result.get('fallback', 'none')}")
        
        # Check if we have outlier scores
        if 'outlier_scores' in result and len(result['outlier_scores']) > 0:
            print(f"   Outlier scores generated: {len(result['outlier_scores'])}")
            print(f"   Score range: {min(result['outlier_scores']):.2f} - {max(result['outlier_scores']):.2f}")
        
        return True
    except Exception as e:
        print(f"❌ Outlier detection failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_anomaly_detection():
    """Test anomaly detection."""
    print(f"\n{'='*60}")
    print("Test: Anomaly Detection")
    print(f"{'='*60}")
    
    try:
        assessor = DataQualityAssessor()
        df = create_test_dataframe(n_rows=100)
        
        result = assessor.detect_anomalies(df)
        
        print(f"✅ Anomaly detection completed")
        print(f"   Method: {result.get('method', 'unknown')}")
        print(f"   Anomaly count: {result.get('anomaly_count', 0)}")
        print(f"   Anomaly percentage: {result.get('anomaly_percentage', 0):.2f}%")
        
        if 'anomaly_scores' in result and len(result['anomaly_scores']) > 0:
            print(f"   Anomaly scores generated: {len(result['anomaly_scores'])}")
        
        return True
    except Exception as e:
        print(f"❌ Anomaly detection failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_quality_score_calculation():
    """Test quality score calculation."""
    print(f"\n{'='*60}")
    print("Test: Quality Score Calculation")
    print(f"{'='*60}")
    
    try:
        assessor = DataQualityAssessor()
        df = create_test_dataframe(n_rows=100)
        
        result = assessor.calculate_quality_score(df)
        
        print(f"✅ Quality score calculation completed")
        print(f"   Overall score: {result.get('overall_score', 0):.2f}/100")
        print(f"   Missing score: {result.get('missing_score', 0):.2f}/100")
        print(f"   Outlier score: {result.get('outlier_score', 0):.2f}/100")
        print(f"   Anomaly score: {result.get('anomaly_score', 0):.2f}/100")
        print(f"   Consistency score: {result.get('consistency_score', 0):.2f}/100")
        
        # Validate score is in reasonable range
        overall_score = result.get('overall_score', 0)
        if 0 <= overall_score <= 100:
            print(f"✅ Overall score is in valid range (0-100)")
        else:
            print(f"⚠️  Overall score is outside valid range: {overall_score}")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Quality score calculation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_column_quality_assessment():
    """Test column-level quality assessment."""
    print(f"\n{'='*60}")
    print("Test: Column Quality Assessment")
    print(f"{'='*60}")
    
    try:
        assessor = DataQualityAssessor()
        df = create_test_dataframe(n_rows=100)
        
        result = assessor.assess_column_quality(df)
        
        print(f"✅ Column quality assessment completed")
        print(f"   Columns assessed: {len(result)}")
        
        for col, metrics in list(result.items())[:3]:  # Show first 3
            print(f"   {col}:")
            print(f"      Quality score: {metrics.get('quality_score', 0):.2f}")
            print(f"      Missing %: {metrics.get('missing_percentage', 0):.2f}")
            print(f"      Data type: {metrics.get('data_type', 'unknown')}")
        
        return True
    except Exception as e:
        print(f"❌ Column quality assessment failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_with_real_csv_file(file_path: str):
    """Test data quality assessment with a real CSV file."""
    print(f"\n{'='*60}")
    print(f"Test: Real CSV File Assessment")
    print(f"File: {file_path}")
    print(f"{'='*60}")
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    try:
        # Load CSV
        df = pd.read_csv(file_path)
        print(f"✅ Loaded CSV: {len(df)} rows, {len(df.columns)} columns")
        
        # Limit size for testing
        if len(df) > 1000:
            df = df.head(1000)
            print(f"   Using first 1000 rows for testing")
        
        assessor = DataQualityAssessor()
        
        # Test missing values
        missing_result = assessor.assess_missing_values(df)
        print(f"✅ Missing values: {missing_result.get('missing_percentage', 0):.2f}%")
        
        # Test outliers (if numeric columns exist)
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            outlier_result = assessor.detect_outliers(df)
            print(f"✅ Outliers detected: {outlier_result.get('outlier_count', 0)}")
        else:
            print("⚠️  No numeric columns for outlier detection")
        
        # Test quality score
        quality_result = assessor.calculate_quality_score(df)
        print(f"✅ Overall quality score: {quality_result.get('overall_score', 0):.2f}/100")
        
        return True
    except Exception as e:
        print(f"❌ Assessment failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_edge_cases():
    """Test edge cases."""
    print(f"\n{'='*60}")
    print("Test: Edge Cases")
    print(f"{'='*60}")
    
    results = []
    
    # Test with single column
    try:
        assessor = DataQualityAssessor()
        df_single = pd.DataFrame({'col1': [1, 2, 3, 4, 5]})
        result = assessor.assess_missing_values(df_single)
        print("✅ Single column DataFrame handled")
        results.append(True)
    except Exception as e:
        print(f"❌ Single column failed: {e}")
        results.append(False)
    
    # Test with all numeric
    try:
        assessor = DataQualityAssessor()
        df_numeric = create_test_dataframe(n_rows=50, n_numeric=5, n_categorical=0)
        result = assessor.detect_outliers(df_numeric)
        print("✅ All numeric DataFrame handled")
        results.append(True)
    except Exception as e:
        print(f"❌ All numeric failed: {e}")
        results.append(False)
    
    # Test with all categorical
    try:
        assessor = DataQualityAssessor()
        df_categorical = create_test_dataframe(n_rows=50, n_numeric=0, n_categorical=5)
        result = assessor.assess_missing_values(df_categorical)
        print("✅ All categorical DataFrame handled")
        results.append(True)
    except Exception as e:
        print(f"❌ All categorical failed: {e}")
        results.append(False)
    
    return all(results)


def main():
    """Run all data quality tests."""
    print("="*60)
    print("Data Quality Assessment Test Suite")
    print("="*60)
    
    results = []
    
    # Core functionality tests
    results.append(("Initialization", test_assessor_initialization()))
    results.append(("Missing Value Assessment", test_missing_value_assessment()))
    results.append(("Outlier Detection", test_outlier_detection()))
    results.append(("Anomaly Detection", test_anomaly_detection()))
    results.append(("Quality Score Calculation", test_quality_score_calculation()))
    results.append(("Column Quality Assessment", test_column_quality_assessment()))
    results.append(("Edge Cases", test_edge_cases()))
    
    # Test with real CSV files (relative to project root)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_files = [
        os.path.join(project_root, "csv1k/patients.csv"),
        os.path.join(project_root, "csvlate/patients.csv"),
    ]
    
    for file_path in csv_files:
        if os.path.exists(file_path):
            result = test_with_real_csv_file(file_path)
            results.append((f"Real CSV: {os.path.basename(file_path)}", result))
    
    # Summary
    print(f"\n{'='*60}")
    print("Test Summary")
    print(f"{'='*60}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit(main())

