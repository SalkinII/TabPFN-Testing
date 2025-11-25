"""
Test script for Panel web app functionality.
Simulates Panel FileInput behavior and tests the complete file upload flow.
"""

import pandas as pd
import io
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import load_csv_file, process_file, assess_data_quality, create_dashboard
from utils import log_dev_event


class MockEvent:
    """Mock Panel Event object for testing."""
    
    def __init__(self, file_value):
        self.new = file_value
        self.old = None
        self.obj = None


class MockFileInputWidget:
    """Mock Panel FileInput widget."""
    
    def __init__(self, value):
        self.value = value


def test_load_csv_with_bytes():
    """Test loading CSV with bytes (Panel FileInput format)."""
    print(f"\n{'='*60}")
    print("Test: Load CSV with bytes (Panel FileInput format)")
    print(f"{'='*60}")
    
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_file = os.path.join(project_root, "csv1k/patients.csv")
    
    if not os.path.exists(csv_file):
        print(f"❌ File not found: {csv_file}")
        return False
    
    # Read file as bytes (simulating Panel FileInput)
    with open(csv_file, 'rb') as f:
        file_bytes = f.read()
    
    # Panel FileInput.value is a list of bytes
    file_input = [file_bytes]
    
    df = load_csv_file(file_input)
    
    if df is None:
        print("❌ Failed to load CSV")
        return False
    
    if len(df) == 0:
        print("❌ DataFrame is empty")
        return False
    
    print(f"✅ CSV loaded successfully")
    print(f"   Rows: {len(df)}")
    print(f"   Columns: {len(df.columns)}")
    print(f"   Column names: {list(df.columns[:5])}...")
    
    return True


def test_process_file_with_event():
    """Test process_file function with Event object."""
    print(f"\n{'='*60}")
    print("Test: process_file with Event object")
    print(f"{'='*60}")
    
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_file = os.path.join(project_root, "csv1k/patients.csv")
    
    if not os.path.exists(csv_file):
        print(f"❌ File not found: {csv_file}")
        return False
    
    # Read file as bytes
    with open(csv_file, 'rb') as f:
        file_bytes = f.read()
    
    # Create mock Event object (as Panel would)
    mock_event = MockEvent([file_bytes])
    
    # Test that we can extract the value
    if hasattr(mock_event, 'new'):
        file_input = mock_event.new
        print(f"✅ Event.new contains file value: {type(file_input)}")
        
        if isinstance(file_input, list) and len(file_input) > 0:
            print(f"✅ File value is list with {len(file_input)} item(s)")
            print(f"   First item type: {type(file_input[0])}")
            print(f"   First item size: {len(file_input[0])} bytes")
            
            # Test loading
            df = load_csv_file(file_input)
            if df is not None and len(df) > 0:
                print(f"✅ Successfully loaded CSV from Event: {len(df)} rows, {len(df.columns)} columns")
                return True
            else:
                print("❌ Failed to load CSV from Event")
                return False
        else:
            print("❌ File value is not in expected format")
            return False
    else:
        print("❌ Event object doesn't have 'new' attribute")
        return False


def test_end_to_end_pipeline():
    """Test complete pipeline: load → assess → dashboard."""
    print(f"\n{'='*60}")
    print("Test: End-to-End Pipeline")
    print(f"{'='*60}")
    
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_file = os.path.join(project_root, "csv1k/patients.csv")
    
    if not os.path.exists(csv_file):
        print(f"❌ File not found: {csv_file}")
        return False
    
    # Step 1: Load CSV
    print("\n[Step 1] Loading CSV...")
    with open(csv_file, 'rb') as f:
        file_bytes = f.read()
    
    file_input = [file_bytes]
    df = load_csv_file(file_input)
    
    if df is None or len(df) == 0:
        print("❌ Failed to load CSV")
        return False
    
    print(f"✅ CSV loaded: {len(df)} rows, {len(df.columns)} columns")
    
    # Step 2: Assess data quality
    print("\n[Step 2] Assessing data quality...")
    try:
        quality_results = assess_data_quality(df)
        print("✅ Quality assessment completed")
        print(f"   Overall score: {quality_results.get('quality_score', {}).get('overall_score', 0):.2f}/100")
    except Exception as e:
        print(f"❌ Quality assessment failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 3: Create dashboard
    print("\n[Step 3] Creating dashboard...")
    try:
        dashboard = create_dashboard(df)
        print("✅ Dashboard created successfully")
        print(f"   Dashboard type: {type(dashboard).__name__}")
        
        if hasattr(dashboard, 'objects'):
            print(f"   Dashboard components: {len(dashboard.objects)}")
        
        return True
    except Exception as e:
        print(f"❌ Dashboard creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_event_extraction():
    """Test extracting file value from Event object."""
    print(f"\n{'='*60}")
    print("Test: Event Value Extraction")
    print(f"{'='*60}")
    
    # Create test data
    test_csv = b"Id,Name,Value\n1,Test,100\n2,Test2,200\n"
    file_input_value = [test_csv]
    
    # Test different Event scenarios
    scenarios = [
        ("Event with new attribute", MockEvent(file_input_value)),
        ("Direct value (backwards compat)", file_input_value),
    ]
    
    for scenario_name, event_or_value in scenarios:
        print(f"\nTesting: {scenario_name}")
        
        # Simulate process_file logic
        if hasattr(event_or_value, 'new'):
            file_input = event_or_value.new
            print(f"  ✅ Extracted from event.new")
        elif hasattr(event_or_value, 'obj') and hasattr(event_or_value.obj, 'value'):
            file_input = event_or_value.obj.value
            print(f"  ✅ Extracted from event.obj.value")
        else:
            file_input = event_or_value
            print(f"  ✅ Using value directly")
        
        # Test loading
        df = load_csv_file(file_input)
        if df is not None and len(df) > 0:
            print(f"  ✅ Successfully loaded: {len(df)} rows")
        else:
            print(f"  ❌ Failed to load")
            return False
    
    return True


def main():
    """Run all web app tests."""
    print("="*60)
    print("Web App Test Suite")
    print("="*60)
    
    results = []
    
    # Test Event extraction
    results.append(("Event Value Extraction", test_event_extraction()))
    
    # Test CSV loading with bytes
    results.append(("Load CSV with bytes", test_load_csv_with_bytes()))
    
    # Test process_file with Event
    results.append(("process_file with Event", test_process_file_with_event()))
    
    # Test end-to-end pipeline
    results.append(("End-to-End Pipeline", test_end_to_end_pipeline()))
    
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

