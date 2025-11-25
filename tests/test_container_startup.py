"""
Test script to verify the app initializes correctly in Docker container.
Checks for common startup errors and verifies components are ready.

This test should be run inside the Docker container where all dependencies
are installed. To run this test:

    Using dev.ps1 script (recommended):
        .\dev.ps1 test

    Using Docker directly:
        docker exec tabpfn-data-quality-dev python tests/test_container_startup.py

    Using docker-compose:
        docker-compose -f docker-compose.dev.yml exec tabpfn-dev python tests/test_container_startup.py

All dependencies (panel, pandas, numpy, tabpfn, etc.) are installed in the
container, so no local installation is required.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Detect if running in Docker container
def is_docker_environment():
    """Check if running in Docker container."""
    # Check for /app directory (container working directory)
    if os.path.exists('/app'):
        return True
    # Check for container environment variable
    if os.environ.get('ENV') == 'development':
        return True
    # Check if we're in a container by looking for .dockerenv
    if os.path.exists('/.dockerenv'):
        return True
    return False


def test_imports():
    """Test that all required modules can be imported."""
    print(f"\n{'='*60}")
    print("Test: Module Imports")
    print(f"{'='*60}")
    
    try:
        import panel as pn
        print("✅ Panel imported")
    except ImportError as e:
        print(f"❌ Failed to import Panel: {e}")
        return False
    
    try:
        import pandas as pd
        print("✅ Pandas imported")
    except ImportError as e:
        print(f"❌ Failed to import Pandas: {e}")
        return False
    
    try:
        import numpy as np
        print("✅ NumPy imported")
    except ImportError as e:
        print(f"❌ Failed to import NumPy: {e}")
        return False
    
    try:
        from tabpfn import TabPFNClassifier, TabPFNRegressor
        print("✅ TabPFN imported")
    except ImportError as e:
        print(f"⚠️  Failed to import TabPFN: {e} (may use fallback)")
    
    try:
        from data_quality import DataQualityAssessor
        print("✅ DataQualityAssessor imported")
    except ImportError as e:
        print(f"❌ Failed to import DataQualityAssessor: {e}")
        return False
    
    try:
        from clinical_quality import ClinicalQualityChecker
        print("✅ ClinicalQualityChecker imported")
    except ImportError as e:
        print(f"❌ Failed to import ClinicalQualityChecker: {e}")
        return False
    
    try:
        from visualizations import create_quality_score_card
        print("✅ Visualization functions imported")
    except ImportError as e:
        print(f"❌ Failed to import visualization functions: {e}")
        return False
    
    try:
        from utils import log_dev_event, log_error
        print("✅ Utility functions imported")
    except ImportError as e:
        print(f"❌ Failed to import utility functions: {e}")
        return False
    
    return True


def test_app_initialization():
    """Test that the app can be initialized."""
    print(f"\n{'='*60}")
    print("Test: App Initialization")
    print(f"{'='*60}")
    
    try:
        # Import app module (this will execute initialization code)
        import app
        
        print("✅ App module imported successfully")
        
        # Check that key components exist
        if hasattr(app, 'assessor'):
            print("✅ DataQualityAssessor initialized")
        else:
            print("❌ DataQualityAssessor not initialized")
            return False
        
        if hasattr(app, 'clinical_checker'):
            print("✅ ClinicalQualityChecker initialized")
        else:
            print("❌ ClinicalQualityChecker not initialized")
            return False
        
        if hasattr(app, 'file_input'):
            print("✅ FileInput widget created")
        else:
            print("❌ FileInput widget not created")
            return False
        
        if hasattr(app, 'app'):
            print("✅ Panel app created")
        else:
            print("❌ Panel app not created")
            return False
        
        return True
    except Exception as e:
        print(f"❌ App initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_file_paths():
    """Test that required directories and files exist."""
    print(f"\n{'='*60}")
    print("Test: File Paths")
    print(f"{'='*60}")
    
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Check logs directory
    logs_dir = os.path.join(project_root, "logs")
    if os.path.exists(logs_dir):
        print(f"✅ Logs directory exists: {logs_dir}")
    else:
        print(f"⚠️  Logs directory doesn't exist: {logs_dir}")
    
    # Check CSV directories
    csv_dirs = ["csv1k", "csvlate"]
    for csv_dir in csv_dirs:
        csv_path = os.path.join(project_root, csv_dir)
        if os.path.exists(csv_path):
            csv_files = [f for f in os.listdir(csv_path) if f.endswith('.csv')]
            print(f"✅ {csv_dir} directory exists with {len(csv_files)} CSV files")
        else:
            print(f"⚠️  {csv_dir} directory doesn't exist: {csv_path}")
    
    return True


def test_environment_variables():
    """Test environment variables."""
    print(f"\n{'='*60}")
    print("Test: Environment Variables")
    print(f"{'='*60}")
    
    hf_token = os.environ.get('HF_TOKEN')
    if hf_token:
        print(f"✅ HF_TOKEN is set (length: {len(hf_token)})")
    else:
        print("⚠️  HF_TOKEN not set (TabPFN will use statistical fallback)")
    
    python_unbuffered = os.environ.get('PYTHONUNBUFFERED')
    if python_unbuffered:
        print(f"✅ PYTHONUNBUFFERED is set: {python_unbuffered}")
    else:
        print("⚠️  PYTHONUNBUFFERED not set")
    
    return True


def test_panel_extension():
    """Test that Panel extensions are available."""
    print(f"\n{'='*60}")
    print("Test: Panel Extensions")
    print(f"{'='*60}")
    
    try:
        import panel as pn
        
        # Check if extensions are available
        extensions = ['plotly', 'tabulator']
        for ext in extensions:
            try:
                pn.extension(ext)
                print(f"✅ Panel extension '{ext}' is available")
            except Exception as e:
                print(f"⚠️  Panel extension '{ext}' may not be available: {e}")
        
        return True
    except Exception as e:
        print(f"❌ Panel extension test failed: {e}")
        return False


def main():
    """Run all container startup tests."""
    print("="*60)
    print("Container Startup Test Suite")
    print("="*60)
    
    # Check environment
    if not is_docker_environment():
        print("\n⚠️  Warning: Not running in Docker container environment.")
        print("   This test is designed to run inside the Docker container.")
        print("   Run with: .\dev.ps1 test")
        print("   Or: docker exec tabpfn-data-quality-dev python tests/test_container_startup.py")
        print("   Continuing anyway...\n")
    else:
        print("✅ Running in Docker container environment\n")
    
    results = []
    
    # Run tests
    results.append(("Module Imports", test_imports()))
    results.append(("App Initialization", test_app_initialization()))
    results.append(("File Paths", test_file_paths()))
    results.append(("Environment Variables", test_environment_variables()))
    results.append(("Panel Extensions", test_panel_extension()))
    
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
        print("\n🎉 All startup tests passed!")
        print("The app should start successfully in the container.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed or had warnings")
        print("Check the errors above before starting the container.")
        return 1


if __name__ == "__main__":
    exit(main())

