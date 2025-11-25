"""
Integration test script for the complete CSV processing pipeline.
Tests the end-to-end flow from file upload to dashboard creation.
"""

import pandas as pd
import numpy as np
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import load_csv_file, assess_data_quality, create_dashboard
from tests.test_csv_loading import MockFileInput


def test_end_to_end_pipeline(file_path: str, description: str):
    """Test the complete pipeline from CSV loading to dashboard creation."""
    print(f"\n{'='*60}")
    print(f"Integration Test: {description}")
    print(f"File: {file_path}")
    print(f"{'='*60}")
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    try:
        # Step 1: Load CSV
        print("\n[Step 1] Loading CSV file...")
        file_input = MockFileInput(file_path=file_path)
        df = load_csv_file(file_input)
        
        if df is None:
            print("❌ Failed to load CSV")
            return False
        
        if len(df) == 0:
            print("❌ DataFrame is empty")
            return False
        
        print(f"✅ CSV loaded: {len(df)} rows, {len(df.columns)} columns")
        
        # Step 2: Assess data quality
        print("\n[Step 2] Assessing data quality...")
        quality_results = assess_data_quality(df)
        
        if not quality_results:
            print("❌ Quality assessment returned empty results")
            return False
        
        print("✅ Quality assessment completed")
        print(f"   Overall score: {quality_results.get('quality_score', {}).get('overall_score', 0):.2f}/100")
        print(f"   Missing %: {quality_results.get('missing_assessment', {}).get('missing_percentage', 0):.2f}%")
        print(f"   Outliers: {quality_results.get('outlier_results', {}).get('outlier_count', 0)}")
        
        # Step 3: Create dashboard
        print("\n[Step 3] Creating dashboard...")
        dashboard = create_dashboard(df)
        
        if dashboard is None:
            print("❌ Dashboard creation returned None")
            return False
        
        print("✅ Dashboard created successfully")
        print(f"   Dashboard type: {type(dashboard).__name__}")
        
        # Verify dashboard has content
        if hasattr(dashboard, 'objects') and len(dashboard.objects) > 0:
            print(f"   Dashboard components: {len(dashboard.objects)}")
        else:
            print("⚠️  Dashboard appears to be empty")
        
        print("\n✅ End-to-end pipeline test PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Pipeline test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_error_handling_empty_file():
    """Test error handling for empty CSV file."""
    print(f"\n{'='*60}")
    print("Integration Test: Empty File Error Handling")
    print(f"{'='*60}")
    
    try:
        empty_content = b""
        file_input = MockFileInput(content_bytes=empty_content)
        df = load_csv_file(file_input)
        
        if df is None:
            print("✅ Empty file correctly handled (returned None)")
            return True
        
        # If it returns a DataFrame, it should be empty
        if len(df) == 0:
            print("✅ Empty file correctly handled (empty DataFrame)")
            # Should fail when trying to assess
            try:
                assess_data_quality(df)
                print("❌ Should have raised error for empty DataFrame")
                return False
            except ValueError:
                print("✅ Correctly raised error when assessing empty DataFrame")
                return True
        
        return False
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False


def test_error_handling_headers_only():
    """Test error handling for headers-only CSV."""
    print(f"\n{'='*60}")
    print("Integration Test: Headers-Only CSV Error Handling")
    print(f"{'='*60}")
    
    try:
        headers_only = b"Id,Name,Value\n"
        file_input = MockFileInput(content_bytes=headers_only)
        df = load_csv_file(file_input)
        
        if df is None:
            print("✅ Headers-only file correctly handled (returned None)")
            return True
        
        if len(df) == 0:
            print("✅ Headers-only file correctly handled (empty DataFrame)")
            # Should fail when trying to assess
            try:
                assess_data_quality(df)
                print("❌ Should have raised error for empty DataFrame")
                return False
            except ValueError:
                print("✅ Correctly raised error when assessing empty DataFrame")
                return True
        
        return False
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False


def test_error_handling_malformed_csv():
    """Test error handling for malformed CSV."""
    print(f"\n{'='*60}")
    print("Integration Test: Malformed CSV Error Handling")
    print(f"{'='*60}")
    
    try:
        malformed = b"Id,Name\n1,John\n2,Jane,Extra,Columns\n3"
        file_input = MockFileInput(content_bytes=malformed)
        df = load_csv_file(file_input)
        
        if df is None:
            print("✅ Malformed CSV correctly handled (returned None)")
            return True
        
        # If pandas can parse it, try to process it
        if len(df) > 0:
            print(f"⚠️  Pandas parsed malformed CSV ({len(df)} rows)")
            try:
                quality_results = assess_data_quality(df)
                print("✅ Successfully processed parsed malformed CSV")
                return True
            except Exception as e:
                print(f"⚠️  Failed to process parsed CSV: {e}")
                return False
        
        return False
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False


def test_performance_large_file():
    """Test performance with a larger file."""
    print(f"\n{'='*60}")
    print("Integration Test: Large File Performance")
    print(f"{'='*60}")
    
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_file = os.path.join(project_root, "csvlate/patients.csv")
    if not os.path.exists(csv_file):
        print(f"⚠️  Skipping: {csv_file} not found")
        return True  # Not a failure, just skip
    
    try:
        import time
        
        start_time = time.time()
        
        file_input = MockFileInput(file_path=csv_file)
        df = load_csv_file(file_input)
        
        load_time = time.time() - start_time
        print(f"✅ CSV loaded in {load_time:.2f} seconds")
        
        if df is None or len(df) == 0:
            print("❌ Failed to load large file")
            return False
        
        # Limit size for performance testing
        if len(df) > 500:
            df = df.head(500)
            print(f"   Using first 500 rows for performance test")
        
        start_time = time.time()
        quality_results = assess_data_quality(df)
        assess_time = time.time() - start_time
        print(f"✅ Quality assessment completed in {assess_time:.2f} seconds")
        
        start_time = time.time()
        dashboard = create_dashboard(df)
        dashboard_time = time.time() - start_time
        print(f"✅ Dashboard created in {dashboard_time:.2f} seconds")
        
        total_time = load_time + assess_time + dashboard_time
        print(f"\n✅ Total processing time: {total_time:.2f} seconds")
        
        return True
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all integration tests."""
    print("="*60)
    print("Integration Test Suite")
    print("="*60)
    
    results = []
    
    # Test with real CSV files (relative to project root)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_files = [
        (os.path.join(project_root, "csvlate/patients.csv"), "Small dataset (csvlate)"),
        (os.path.join(project_root, "csv1k/patients.csv"), "Large dataset (csv1k)"),
    ]
    
    for file_path, description in csv_files:
        if os.path.exists(file_path):
            result = test_end_to_end_pipeline(file_path, description)
            results.append((f"End-to-end: {description}", result))
        else:
            print(f"\n⚠️  Skipping {file_path} (file not found)")
    
    # Test error handling
    results.append(("Error handling: Empty file", test_error_handling_empty_file()))
    results.append(("Error handling: Headers only", test_error_handling_headers_only()))
    results.append(("Error handling: Malformed CSV", test_error_handling_malformed_csv()))
    results.append(("Performance: Large file", test_performance_large_file()))
    
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
        print("\n🎉 All integration tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit(main())

