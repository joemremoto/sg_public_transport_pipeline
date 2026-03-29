"""
Script: upload_to_gcs.py
Purpose: Standalone script to upload extracted LTA data to Google Cloud Storage.
         
This script provides a simple command-line interface for uploading data.
It can be run manually or called by orchestration tools (Airflow).

Usage:
    # Upload all local data (reference + all monthly data found)
    python scripts/upload_to_gcs.py --all
    
    # Upload specific month
    python scripts/upload_to_gcs.py --year 2026 --month 1
    
    # Upload specific month with reference data
    python scripts/upload_to_gcs.py --year 2026 --month 1 --include-reference
    
    # Upload only reference data
    python scripts/upload_to_gcs.py --reference-only

Author: Joseph Emmanuel Remoto
Date: 2026-03-28
"""

import argparse  # argparse = library for parsing command-line arguments
import sys  # sys = system-specific functions (like exit codes)
from pathlib import Path

# Add project root to Python path so we can import our modules
# This allows the script to run from anywhere
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.upload.gcs_uploader import GCSUploader
from src.config.settings import Config


def main():
    """
    Main entry point for the upload script.
    
    This function:
    1. Parses command-line arguments
    2. Validates configuration
    3. Creates uploader instance
    4. Executes the requested upload operation
    5. Returns appropriate exit code (0=success, 1=failure)
    """
    # Set up argument parser
    # ArgumentParser creates a nice command-line interface with --help support
    parser = argparse.ArgumentParser(
        description='Upload LTA data to Google Cloud Storage',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Upload all local data
  python scripts/upload_to_gcs.py --all
  
  # Upload January 2026 data
  python scripts/upload_to_gcs.py --year 2026 --month 1
  
  # Upload with reference data
  python scripts/upload_to_gcs.py --year 2026 --month 1 --include-reference
        """
    )
    
    # Define command-line arguments
    # Each add_argument() defines an option you can pass to the script
    
    parser.add_argument(
        '--all',
        action='store_true',  # This makes it a flag (no value needed)
        help='Upload all data found in local raw directory'
    )
    
    parser.add_argument(
        '--reference-only',
        action='store_true',
        help='Upload only reference data (bus stops, train stations)'
    )
    
    parser.add_argument(
        '--year',
        type=int,  # Converts input to integer
        help='Year of data to upload (e.g., 2026)'
    )
    
    parser.add_argument(
        '--month',
        type=int,
        help='Month of data to upload (1-12)'
    )
    
    parser.add_argument(
        '--include-reference',
        action='store_true',
        help='Also upload reference data (use with --year and --month)'
    )
    
    parser.add_argument(
        '--mode',
        type=str,
        choices=['bus', 'train'],
        help='Upload only specific transport mode (use with --year and --month)'
    )
    
    # Parse arguments from command line
    # args is an object with attributes matching the argument names
    # Example: if user runs --year 2026, then args.year = 2026
    args = parser.parse_args()
    
    # Validate argument combinations
    if not any([args.all, args.reference_only, (args.year and args.month)]):
        parser.error(
            "Must specify one of: --all, --reference-only, or --year/--month"
        )
    
    if (args.year and not args.month) or (args.month and not args.year):
        parser.error("Both --year and --month must be specified together")
    
    if args.month and not (1 <= args.month <= 12):
        parser.error("Month must be between 1 and 12")
    
    # Print configuration summary
    print("\n" + "="*70)
    print("📤 GCS UPLOAD SCRIPT")
    print("="*70)
    print(f"Target Bucket: {Config.GCS_BUCKET_RAW}")
    print(f"GCP Project: {Config.GCP_PROJECT_ID}")
    print(f"GCP Region: {Config.GCP_REGION}")
    print("="*70 + "\n")
    
    try:
        # Create uploader instance
        # This validates configuration and connects to GCS
        uploader = GCSUploader()
        
        # Execute the requested operation based on arguments
        
        if args.all:
            # Upload everything found locally
            print("📦 Uploading all local data...\n")
            results = uploader.upload_all_local_data()
            
            # Check results
            all_success = (
                all(results['reference'].values()) and
                all(
                    all(month_results.values())
                    for month_results in results['monthly'].values()
                ) if results['monthly'] else True
            )
            
            if all_success:
                print("\n✅ All uploads completed successfully!")
                return 0
            else:
                print("\n⚠️  Some uploads failed. Check logs above.")
                return 1
        
        elif args.reference_only:
            # Upload only reference data
            print("📚 Uploading reference data...\n")
            results = uploader.upload_reference_data()
            
            if all(results.values()):
                print("\n✅ Reference data uploaded successfully!")
                return 0
            else:
                print("\n⚠️  Some reference uploads failed. Check logs above.")
                return 1
        
        else:
            # Upload specific month
            results = {}
            
            # Upload reference data if requested
            if args.include_reference:
                print("📚 Uploading reference data...\n")
                ref_results = uploader.upload_reference_data()
                results.update(ref_results)
            
            # Upload monthly data
            if args.mode:
                # Upload specific mode only
                print(f"📅 Uploading {args.mode.upper()} data for {args.year}-{str(args.month).zfill(2)}...\n")
                success = uploader.upload_od_data(args.year, args.month, args.mode)
                results[args.mode] = success
            else:
                # Upload all modes
                print(f"📅 Uploading data for {args.year}-{str(args.month).zfill(2)}...\n")
                monthly_results = uploader.upload_monthly_data(args.year, args.month)
                results.update(monthly_results)
            
            # Check results
            if all(results.values()):
                print("\n✅ Upload completed successfully!")
                return 0
            else:
                print("\n⚠️  Some uploads failed. Check logs above.")
                return 1
    
    except Exception as e:
        print(f"\n❌ Upload failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    # Run main function and exit with its return code
    # Exit code 0 = success, non-zero = failure
    # This is important for automation (Airflow checks exit codes)
    exit_code = main()
    sys.exit(exit_code)
