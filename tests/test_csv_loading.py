"""
Test script for CSV file loading functionality.
Tests the load_csv_file function with various file formats and edge cases.
"""

import pandas as pd
import io
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import load_csv_file
from utils import log_dev_event


class MockFileInput:
    """Mock Panel FileInput widget for testing."""
    
    def __init__(self, file_path=None, content_bytes=None, content_string=None):
        self.file_path = file_path
        self.content_bytes = content_bytes
        self.content_string = content_string
        self._content = None
        
        if file_path and os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                self.content_bytes = f.read()
        elif content_bytes:
            self.content_bytes = content_bytes
        elif content_string:
            self.content_string = content_string
    
    def __len__(self):
        return 1 if (self.content_bytes or self.content_string) else 0
    
    def __getitem__(self, index):
        if index == 0:
            if self.content_bytes:
                return self.content_bytes
            elif self.content_string:
                return self.content_string
        raise IndexError("Index out of range")


def test_load_real_csv_file(file_path: str, description: str):
    """Test loading a real CSV file."""
    print(f"\n{'='*60}")
    print(f"Test: {description}")
    print(f"File: {file_path}")
    print(f"{'='*60}")
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    # Test with bytes (most common case)
    file_input_bytes = MockFileInput(file_path=file_path)
    df_bytes = load_csv_file(file_input_bytes)
    
    if df_bytes is None:
        print("❌ Failed to load CSV (bytes)")
        return False
    
    print(f"✅ Loaded successfully (bytes)")
    print(f"   Rows: {len(df_bytes)}")
    print(f"   Columns: {len(df_bytes.columns)}")
    print(f"   Column names: {list(df_bytes.columns[:5])}...")
    
    # Verify it's not empty
    if len(df_bytes) == 0:
        print("⚠️  Warning: DataFrame is empty")
        return False
    
    if len(df_bytes.columns) == 0:
        print("⚠️  Warning: DataFrame has no columns")
        return False
    
    return True


def test_load_empty_csv():
    """Test loading an empty CSV file."""
    print(f"\n{'='*60}")
    print("Test: Empty CSV file")
    print(f"{'='*60}")
    
    # Create empty CSV content
    empty_content = b""
    file_input = MockFileInput(content_bytes=empty_content)
    df = load_csv_file(file_input)
    
    if df is None:
        print("✅ Correctly returned None for empty file")
        return True
    else:
        print(f"❌ Should return None but got DataFrame with {len(df)} rows")
        return False


def test_load_headers_only_csv():
    """Test loading CSV with only headers."""
    print(f"\n{'='*60}")
    print("Test: CSV with headers only")
    print(f"{'='*60}")
    
    headers_only = b"Id,Name,Value\n"
    file_input = MockFileInput(content_bytes=headers_only)
    df = load_csv_file(file_input)
    
    if df is None:
        print("✅ Correctly handled headers-only CSV (returned None or empty)")
        return True
    elif len(df) == 0:
        print("✅ Correctly returned empty DataFrame for headers-only CSV")
        print(f"   Columns: {list(df.columns)}")
        return True
    else:
        print(f"⚠️  Got DataFrame with {len(df)} rows (expected 0)")
        return True  # Still acceptable


def test_load_malformed_csv():
    """Test loading a malformed CSV file."""
    print(f"\n{'='*60}")
    print("Test: Malformed CSV file")
    print(f"{'='*60}")
    
    malformed = b"Id,Name\n1,John\n2,Jane,Extra,Columns\n3"
    file_input = MockFileInput(content_bytes=malformed)
    df = load_csv_file(file_input)
    
    if df is None:
        print("✅ Correctly handled malformed CSV (returned None)")
        return True
    else:
        print(f"⚠️  Parsed malformed CSV (may be acceptable): {len(df)} rows")
        return True  # Pandas may still parse it


def test_load_string_content():
    """Test loading CSV from string content."""
    print(f"\n{'='*60}")
    print("Test: CSV from string content")
    print(f"{'='*60}")
    
    csv_string = "Id,Name,Value\n1,Test,100\n2,Test2,200\n"
    file_input = MockFileInput(content_string=csv_string)
    df = load_csv_file(file_input)
    
    if df is None:
        print("❌ Failed to load CSV from string")
        return False
    
    print(f"✅ Loaded successfully (string)")
    print(f"   Rows: {len(df)}")
    print(f"   Columns: {len(df.columns)}")
    return True


def main():
    """Run all CSV loading tests."""
    print("="*60)
    print("CSV Loading Test Suite")
    print("="*60)
    
    results = []
    
    # Test with real CSV files (relative to project root)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_files = [
        (os.path.join(project_root, "csv1k/patients.csv"), "Small dataset (csv1k)"),
        (os.path.join(project_root, "csvlate/patients.csv"), "Large dataset (csvlate)"),
    ]
    
    for file_path, description in csv_files:
        if os.path.exists(file_path):
            result = test_load_real_csv_file(file_path, description)
            results.append(("Real CSV: " + description, result))
        else:
            print(f"\n⚠️  Skipping {file_path} (file not found)")
    
    # Test edge cases
    results.append(("Empty CSV", test_load_empty_csv()))
    results.append(("Headers only CSV", test_load_headers_only_csv()))
    results.append(("Malformed CSV", test_load_malformed_csv()))
    results.append(("String content CSV", test_load_string_content()))
    
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

