"""
Standalone script to corrupt CSV files for testing TabPFN detection capabilities.
Can be run in Docker container or locally.
"""

import argparse
import os
import sys
import pandas as pd
from pathlib import Path
from typing import List, Optional
from corruption_framework import DataCorruptor
from utils import log_operation, ensure_logs_directory


def find_csv_files(source_path: str) -> List[str]:
    """
    Find all CSV files in the source path.
    
    Args:
        source_path: Path to file or directory
        
    Returns:
        List of CSV file paths
    """
    path = Path(source_path)
    
    if path.is_file():
        if path.suffix.lower() == '.csv':
            return [str(path)]
        else:
            print(f"Error: {source_path} is not a CSV file")
            return []
    
    if path.is_dir():
        csv_files = list(path.glob('*.csv'))
        if not csv_files:
            print(f"Warning: No CSV files found in {source_path}")
        return [str(f) for f in csv_files]
    
    print(f"Error: {source_path} does not exist")
    return []


def get_output_path(source_file: str, output_base: str, source_folder: str) -> str:
    """
    Determine output path for corrupted file, preserving folder structure.
    
    Args:
        source_file: Path to source CSV file
        output_base: Base output directory (corrupt/)
        source_folder: Original source folder name (csv1k, csvlate, etc.)
        
    Returns:
        Output file path
    """
    source_path = Path(source_file)
    
    # If source_file is inside a folder like csv1k/patients.csv
    # Create corrupt/csv1k/patients.csv
    if source_folder in str(source_path):
        # Extract relative path from source_folder
        relative_path = source_path.relative_to(source_folder)
        output_dir = Path(output_base) / source_folder
    else:
        # Just use filename
        output_dir = Path(output_base)
        relative_path = source_path.name
    
    output_dir.mkdir(parents=True, exist_ok=True)
    return str(output_dir / relative_path)


def corrupt_file(input_file: str, output_file: str, corruption_type: str, 
                 level: Optional[float] = None, random_seed: int = 42) -> dict:
    """
    Corrupt a single CSV file.
    
    Args:
        input_file: Path to input CSV file
        output_file: Path to output corrupted CSV file
        corruption_type: Type of corruption ('missing', 'outliers', 'duplicates', 
                         'inconsistencies', 'maximum')
        level: Corruption level (percentage, 0-100)
        random_seed: Random seed for reproducibility
        
    Returns:
        Dictionary with corruption details
    """
    print(f"Processing: {input_file}")
    
    try:
        # Load CSV
        df = pd.read_csv(input_file)
        print(f"  Loaded {len(df)} rows, {len(df.columns)} columns")
        
        # Initialize corruptor
        corruptor = DataCorruptor(random_seed=random_seed)
        
        # Apply corruption
        if corruption_type == 'missing':
            level = level or 10.0
            corrupted_df, details = corruptor.introduce_missing_values(
                df, missing_percentage=level, pattern='random'
            )
        elif corruption_type == 'outliers':
            level = level or 5.0
            corrupted_df, details = corruptor.introduce_outliers(
                df, outlier_percentage=level, outlier_type='statistical'
            )
        elif corruption_type == 'duplicates':
            level = level or 5.0
            corrupted_df, details = corruptor.introduce_duplicates(
                df, duplicate_percentage=level
            )
        elif corruption_type == 'inconsistencies':
            level = level or 5.0
            corrupted_df, details = corruptor.introduce_inconsistencies(
                df, inconsistency_percentage=level
            )
        elif corruption_type == 'maximum':
            corrupted_df, details = corruptor.apply_maximum_corruption(df)
        else:
            raise ValueError(f"Unknown corruption type: {corruption_type}")
        
        # Save corrupted CSV
        corrupted_df.to_csv(output_file, index=False)
        print(f"  Saved corrupted file: {output_file}")
        
        # Add file info to details
        details['input_file'] = input_file
        details['output_file'] = output_file
        details['original_rows'] = len(df)
        details['corrupted_rows'] = len(corrupted_df)
        
        return details
        
    except Exception as e:
        error_msg = f"Error processing {input_file}: {str(e)}"
        print(f"  ERROR: {error_msg}")
        return {
            'input_file': input_file,
            'error': str(e),
            'success': False
        }


def main():
    """Main entry point for the corruption script."""
    parser = argparse.ArgumentParser(
        description='Corrupt CSV files for testing TabPFN detection capabilities',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Corrupt all files in csvlate/ with 10% missing values
  python corrupt_data.py --source csvlate --corruption missing --level 10

  # Corrupt single file with maximum corruption
  python corrupt_data.py --source csvlate/patients.csv --corruption maximum

  # Corrupt with outliers at 5%
  python corrupt_data.py --source csv1k --corruption outliers --level 5

  # Use custom random seed
  python corrupt_data.py --source csvlate --corruption missing --level 10 --seed 123
        """
    )
    
    parser.add_argument(
        '--source', '-s',
        required=True,
        help='Source CSV file or directory containing CSV files (e.g., csvlate/ or csvlate/patients.csv)'
    )
    
    parser.add_argument(
        '--corruption', '-c',
        required=True,
        choices=['missing', 'outliers', 'duplicates', 'inconsistencies', 'maximum'],
        help='Type of corruption to apply'
    )
    
    parser.add_argument(
        '--level', '-l',
        type=float,
        default=None,
        help='Corruption level (percentage, 0-100). Not used for "maximum" corruption.'
    )
    
    parser.add_argument(
        '--output', '-o',
        default='corrupt',
        help='Output directory for corrupted files (default: corrupt/)'
    )
    
    parser.add_argument(
        '--seed', '-r',
        type=int,
        default=42,
        help='Random seed for reproducibility (default: 42)'
    )
    
    args = parser.parse_args()
    
    # Find CSV files
    csv_files = find_csv_files(args.source)
    if not csv_files:
        print("No CSV files found. Exiting.")
        sys.exit(1)
    
    print(f"\nFound {len(csv_files)} CSV file(s) to process")
    print(f"Corruption type: {args.corruption}")
    if args.level is not None:
        print(f"Corruption level: {args.level}%")
    print(f"Random seed: {args.seed}")
    print(f"Output directory: {args.output}/")
    print("-" * 60)
    
    # Determine source folder name for preserving structure
    source_path = Path(args.source)
    if source_path.is_file():
        source_folder = source_path.parent.name
    else:
        source_folder = source_path.name
    
    # Process each file
    results = []
    for csv_file in csv_files:
        output_file = get_output_path(csv_file, args.output, source_folder)
        result = corrupt_file(
            csv_file, 
            output_file, 
            args.corruption, 
            args.level, 
            args.seed
        )
        results.append(result)
    
    # Log summary
    successful = [r for r in results if r.get('success', True) and 'error' not in r]
    failed = [r for r in results if 'error' in r or not r.get('success', True)]
    
    summary = {
        'total_files': len(csv_files),
        'successful': len(successful),
        'failed': len(failed),
        'corruption_type': args.corruption,
        'corruption_level': args.level,
        'random_seed': args.seed,
        'output_directory': args.output,
        'results': results
    }
    
    log_file = log_operation('corruption_batch', summary)
    
    print("-" * 60)
    print(f"\nSummary:")
    print(f"  Total files processed: {len(csv_files)}")
    print(f"  Successful: {len(successful)}")
    print(f"  Failed: {len(failed)}")
    print(f"  Log file: {log_file}")
    
    if failed:
        print(f"\nFailed files:")
        for result in failed:
            print(f"  - {result.get('input_file', 'unknown')}: {result.get('error', 'unknown error')}")
    
    print(f"\nCorrupted files saved to: {args.output}/")
    print("You can now upload these files to the dashboard to test TabPFN detection capabilities.")


if __name__ == '__main__':
    main()

