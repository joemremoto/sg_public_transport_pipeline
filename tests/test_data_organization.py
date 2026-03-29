"""
Test: Validate Data File Organization

PURPOSE:
    This test verifies that all extracted data files are organized correctly
    in their respective subdirectories.
    
    Expected structure:
    data/
    └── raw/
        ├── bus_stops.json          # Reference data (root level)
        ├── train_stations.json     # Reference data (root level)
        ├── bus/                    # Bus OD data subdirectory
        │   ├── bus_od_202512.csv
        │   ├── bus_od_202601.csv
        │   └── bus_od_202602.csv
        └── train/                  # Train OD data subdirectory
            ├── train_od_202512.csv
            ├── train_od_202601.csv
            └── train_od_202602.csv

WHY THIS MATTERS:
    - Keeps data organized by transport mode
    - Matches the GCS bucket structure (journeys/bus/, journeys/train/)
    - Makes scripts predictable and maintainable
    - Prevents confusion between bus and train data

USAGE:
    Run this test to check if files are in the right places:
    
    python tests/test_data_organization.py
    
    Or with pytest:
    
    pytest tests/test_data_organization.py -v

WHAT IT CHECKS:
    ✓ Reference data files exist in data/raw/
    ✓ OD data files exist in data/raw/bus/ or data/raw/train/
    ✓ No OD files are in the wrong directories
    ✓ All found files match expected naming conventions

Author: Joseph Emmanuel Remoto
Date: 2026-03-29
"""

import sys
from pathlib import Path
from typing import List, Dict, Tuple

# Add project root to path so we can import our modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config.settings import Config


# ANSI color codes for terminal output
class Colors:
    """Terminal color codes for pretty output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(text: str) -> None:
    """Print a formatted header."""
    print("\n" + "="*70)
    print(f"{Colors.BOLD}{text}{Colors.END}")
    print("="*70 + "\n")


def print_success(text: str) -> None:
    """Print success message in green."""
    print(f"{Colors.GREEN}✓{Colors.END} {text}")


def print_error(text: str) -> None:
    """Print error message in red."""
    print(f"{Colors.RED}✗{Colors.END} {text}")


def print_warning(text: str) -> None:
    """Print warning message in yellow."""
    print(f"{Colors.YELLOW}⚠{Colors.END} {text}")


def print_info(text: str) -> None:
    """Print info message in blue."""
    print(f"{Colors.BLUE}ℹ{Colors.END} {text}")


def check_reference_data() -> Tuple[bool, List[str]]:
    """
    Check that reference data files exist in data/raw/.
    
    Reference data should be at root level:
    - data/raw/bus_stops.json
    - data/raw/train_stations.json
    
    Returns:
        Tuple of (all_found: bool, errors: List[str])
    """
    print_header("1. CHECKING REFERENCE DATA FILES")
    
    errors = []
    expected_files = [
        'bus_stops.json',
        'train_stations.json'
    ]
    
    for filename in expected_files:
        file_path = Config.RAW_DATA_DIR / filename
        
        if file_path.exists():
            # Check file size
            size_mb = file_path.stat().st_size / (1024 * 1024)
            print_success(f"Found {filename} ({size_mb:.2f} MB)")
        else:
            print_error(f"Missing {filename}")
            errors.append(f"Reference file not found: {filename}")
    
    return len(errors) == 0, errors


def check_od_data_organization() -> Tuple[bool, List[str], Dict[str, List[str]]]:
    """
    Check that OD data files are organized in mode-specific subdirectories.
    
    Expected:
    - Bus OD files in data/raw/bus/
    - Train OD files in data/raw/train/
    - NO OD files in data/raw/ (root level)
    
    Returns:
        Tuple of (is_valid: bool, errors: List[str], found_files: Dict)
    """
    print_header("2. CHECKING OD DATA ORGANIZATION")
    
    errors = []
    found_files = {'bus': [], 'train': []}
    
    # Check each transport mode
    for mode in Config.TRANSPORT_MODES:  # ['bus', 'train']
        mode_dir = Config.RAW_DATA_DIR / mode
        
        print(f"\n{Colors.BOLD}Checking {mode.upper()} directory:{Colors.END}")
        print(f"  Path: {mode_dir}")
        
        if not mode_dir.exists():
            print_error(f"  Directory does not exist")
            errors.append(f"Missing directory: {mode_dir}")
            continue
        
        if not mode_dir.is_dir():
            print_error(f"  Path exists but is not a directory")
            errors.append(f"Not a directory: {mode_dir}")
            continue
        
        # Find OD files in this directory
        od_files = list(mode_dir.glob(f'{mode}_od_*.csv'))
        
        if not od_files:
            print_warning(f"  No {mode} OD files found (this is OK if not yet extracted)")
        else:
            print_success(f"  Found {len(od_files)} {mode} OD files")
            
            # List each file with details
            for file_path in sorted(od_files):
                size_mb = file_path.stat().st_size / (1024 * 1024)
                print(f"    • {file_path.name} ({size_mb:.2f} MB)")
                found_files[mode].append(file_path.name)
    
    return len(errors) == 0, errors, found_files


def check_misplaced_files() -> Tuple[bool, List[str]]:
    """
    Check for OD files in the wrong location (data/raw/ root).
    
    OD files should NOT be in data/raw/ directly - they should be in
    mode-specific subdirectories (data/raw/bus/ or data/raw/train/).
    
    Returns:
        Tuple of (no_misplaced: bool, errors: List[str])
    """
    print_header("3. CHECKING FOR MISPLACED FILES")
    
    errors = []
    
    # Look for OD CSV files in root data/raw/ directory
    misplaced_files = list(Config.RAW_DATA_DIR.glob('*_od_*.csv'))
    
    if misplaced_files:
        print_error(f"Found {len(misplaced_files)} OD files in wrong location!")
        print(f"\n  {Colors.RED}These files should be moved to their mode-specific subdirectories:{Colors.END}\n")
        
        for file_path in sorted(misplaced_files):
            # Determine correct location based on filename
            if file_path.name.startswith('bus_'):
                correct_location = Config.RAW_DATA_DIR / 'bus' / file_path.name
                print(f"    {Colors.RED}✗{Colors.END} {file_path.name}")
                print(f"      {Colors.YELLOW}→{Colors.END} Should be: {correct_location}")
            elif file_path.name.startswith('train_'):
                correct_location = Config.RAW_DATA_DIR / 'train' / file_path.name
                print(f"    {Colors.RED}✗{Colors.END} {file_path.name}")
                print(f"      {Colors.YELLOW}→{Colors.END} Should be: {correct_location}")
            
            errors.append(f"Misplaced file: {file_path.name} (should be in {file_path.stem.split('_')[0]}/ subdirectory)")
        
        print(f"\n  {Colors.YELLOW}ACTION REQUIRED:{Colors.END}")
        print(f"    Move these files to their correct subdirectories:")
        print(f"    • Bus files → data/raw/bus/")
        print(f"    • Train files → data/raw/train/")
    else:
        print_success("No misplaced OD files found - all files are organized correctly!")
    
    return len(errors) == 0, errors


def validate_file_naming() -> Tuple[bool, List[str]]:
    """
    Validate that all OD files follow the correct naming convention.
    
    Expected format: {mode}_od_{YYYYMM}.csv
    Examples: bus_od_202601.csv, train_od_202512.csv
    
    Returns:
        Tuple of (all_valid: bool, errors: List[str])
    """
    print_header("4. VALIDATING FILE NAMING CONVENTIONS")
    
    errors = []
    all_valid = True
    
    for mode in Config.TRANSPORT_MODES:
        mode_dir = Config.RAW_DATA_DIR / mode
        
        if not mode_dir.exists():
            continue
        
        # Find all CSV files in mode directory
        all_csvs = list(mode_dir.glob('*.csv'))
        
        for file_path in all_csvs:
            filename = file_path.name
            
            # Check naming convention: {mode}_od_{YYYYMM}.csv
            parts = filename.replace('.csv', '').split('_')
            
            if len(parts) != 3:
                print_error(f"Invalid filename format: {filename}")
                print(f"         Expected: {mode}_od_YYYYMM.csv")
                errors.append(f"Invalid filename: {filename}")
                all_valid = False
                continue
            
            file_mode, od_marker, yyyymm = parts
            
            # Validate each part
            if file_mode != mode:
                print_error(f"Mode mismatch: {filename} is in {mode}/ directory but starts with '{file_mode}_'")
                errors.append(f"Mode mismatch: {filename}")
                all_valid = False
            
            if od_marker != 'od':
                print_error(f"Missing 'od' marker: {filename}")
                errors.append(f"Invalid format: {filename}")
                all_valid = False
            
            if len(yyyymm) != 6 or not yyyymm.isdigit():
                print_error(f"Invalid date format: {filename} (expected YYYYMM)")
                errors.append(f"Invalid date format: {filename}")
                all_valid = False
            else:
                # Validate date components
                year = int(yyyymm[:4])
                month = int(yyyymm[4:6])
                
                if not (2020 <= year <= 2030):
                    print_warning(f"Unusual year: {filename} (year={year})")
                
                if not (1 <= month <= 12):
                    print_error(f"Invalid month: {filename} (month={month})")
                    errors.append(f"Invalid month in filename: {filename}")
                    all_valid = False
    
    if all_valid:
        print_success("All file names follow the correct convention")
    
    return all_valid, errors


def print_summary(
    ref_ok: bool,
    org_ok: bool,
    no_misplaced: bool,
    naming_ok: bool,
    found_files: Dict[str, List[str]]
) -> bool:
    """
    Print final summary and overall pass/fail status.
    
    Returns:
        bool: True if all checks passed, False otherwise
    """
    print_header("VALIDATION SUMMARY")
    
    # Calculate statistics
    total_bus_files = len(found_files['bus'])
    total_train_files = len(found_files['train'])
    total_od_files = total_bus_files + total_train_files
    
    print(f"📊 {Colors.BOLD}Statistics:{Colors.END}")
    print(f"   • Reference files: 2 expected")
    print(f"   • Bus OD files: {total_bus_files}")
    print(f"   • Train OD files: {total_train_files}")
    print(f"   • Total OD files: {total_od_files}")
    
    print(f"\n🔍 {Colors.BOLD}Check Results:{Colors.END}")
    
    checks = [
        ("Reference data files", ref_ok),
        ("OD data organization", org_ok),
        ("No misplaced files", no_misplaced),
        ("File naming conventions", naming_ok)
    ]
    
    all_passed = True
    for check_name, passed in checks:
        if passed:
            print_success(f"{check_name}")
        else:
            print_error(f"{check_name}")
            all_passed = False
    
    print("\n" + "="*70)
    
    if all_passed:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ ALL VALIDATION CHECKS PASSED!{Colors.END}")
        print(f"\n{Colors.GREEN}Your data files are organized correctly.{Colors.END}")
        print(f"{Colors.GREEN}Scripts can now reliably find and process your data.{Colors.END}\n")
        return True
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}✗ VALIDATION FAILED{Colors.END}")
        print(f"\n{Colors.RED}Please fix the issues listed above before proceeding.{Colors.END}")
        print(f"{Colors.YELLOW}Run this test again after making corrections.{Colors.END}\n")
        return False


def main():
    """
    Main function - runs all validation checks.
    """
    print_header("DATA ORGANIZATION VALIDATION TEST")
    print(f"Checking data directory: {Config.RAW_DATA_DIR}\n")
    
    # Run all checks
    ref_ok, ref_errors = check_reference_data()
    org_ok, org_errors, found_files = check_od_data_organization()
    no_misplaced, misplaced_errors = check_misplaced_files()
    naming_ok, naming_errors = validate_file_naming()
    
    # Print summary
    all_passed = print_summary(ref_ok, org_ok, no_misplaced, naming_ok, found_files)
    
    # Collect all errors
    all_errors = ref_errors + org_errors + misplaced_errors + naming_errors
    
    if all_errors:
        print(f"\n{Colors.RED}{Colors.BOLD}Errors found ({len(all_errors)}):{Colors.END}")
        for i, error in enumerate(all_errors, 1):
            print(f"  {i}. {error}")
    
    # Exit with appropriate code
    # 0 = success, 1 = failure
    # This is important for CI/CD pipelines and automation
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
