"""
Script: load_to_bq.py
Purpose: Command-line interface for loading data from GCS to BigQuery.
         Provides a user-friendly way to load reference data and OD data.

Why this exists:
- Makes it easy to load data manually when needed
- Supports loading specific tables or all data at once
- Useful for backfilling historical data or recovering from failures
- Provides clear feedback on what's being loaded

This is part of Phase 4: BigQuery Schema & Load
In Phase 6, Airflow will automate these loads on a schedule.

Usage Examples:
    # Load all reference data (bus stops, train stations)
    python scripts/load_to_bq.py --reference
    
    # Load all OD data currently in GCS
    python scripts/load_to_bq.py --od
    
    # Load everything (reference + OD data)
    python scripts/load_to_bq.py --all
    
    # Load specific mode and period
    python scripts/load_to_bq.py --mode bus --period 202601
    
    # Load range of periods for a mode
    python scripts/load_to_bq.py --mode train --start 202512 --end 202602

Author: Data Engineering Team
Date: 2026-03-30
"""

# Import statements
import argparse  # For parsing command-line arguments
import logging  # For logging progress
import sys  # For system exit codes

# Our custom modules
from src.config.settings import Config  # Configuration
from src.load.bq_loader import BigQueryLoader  # BigQuery loader


# Set up logging
# This shows progress in real-time as data is loaded
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_reference_data(loader: BigQueryLoader) -> None:
    """
    Load all reference/dimension data into BigQuery.
    
    Reference data includes:
    - bus_stops: All bus stop locations and details
    - train_stations: All MRT/LRT station details
    
    This data is relatively small and doesn't change often,
    so we load it completely each time (WRITE_TRUNCATE mode).
    
    Parameters:
        loader (BigQueryLoader): Initialized BigQuery loader instance
        
    Example:
        loader = BigQueryLoader()
        load_reference_data(loader)
    """
    logger.info("=" * 80)
    logger.info("LOADING REFERENCE DATA")
    logger.info("=" * 80)
    
    # List of reference tables to load
    reference_tables = ['bus_stops', 'train_stations']
    
    for table_name in reference_tables:
        try:
            logger.info(f"\n📍 Loading {table_name}...")
            loader.load_reference_data(table_name)
            logger.info(f"✓ Successfully loaded {table_name}\n")
            
        except Exception as e:
            logger.error(f"❌ Failed to load {table_name}: {e}")
            # Continue with next table instead of failing completely
            continue
    
    logger.info("=" * 80)
    logger.info("✓ Reference data loading completed")
    logger.info("=" * 80)


def load_od_data_for_mode(loader: BigQueryLoader, mode: str, periods: list[str]) -> None:
    """
    Load OD data for a specific transport mode and list of periods.
    
    Parameters:
        loader (BigQueryLoader): Initialized BigQuery loader instance
        mode (str): Transport mode ('bus' or 'train')
        periods (list[str]): List of year-month strings (YYYYMM format)
        
    Example:
        loader = BigQueryLoader()
        load_od_data_for_mode(loader, 'bus', ['202512', '202601', '202602'])
    """
    logger.info(f"\n📊 Loading {mode.upper()} OD data for {len(periods)} period(s)...")
    
    for period in periods:
        try:
            logger.info(f"  Loading {mode} data for {period}...")
            loader.load_od_data(mode, period)
            
        except Exception as e:
            logger.error(f"  ❌ Failed to load {mode} data for {period}: {e}")
            # Continue with next period
            continue
    
    logger.info(f"✓ Completed loading {mode.upper()} OD data\n")


def detect_available_periods() -> dict[str, list[str]]:
    """
    Detect what OD data is available in GCS by listing bucket contents.
    
    This scans the GCS bucket to find what year-month folders exist,
    so we know what data is available to load.
    
    Returns:
        dict: Dictionary mapping mode ('bus', 'train') to list of available periods
        
    Example return:
        {
            'bus': ['202512', '202601', '202602'],
            'train': ['202512', '202601', '202602']
        }
        
    Note: This requires read access to the GCS bucket.
    """
    from google.cloud import storage
    
    logger.info("🔍 Scanning GCS bucket for available data...")
    
    # Initialize GCS client
    gcs_client = storage.Client(project=Config.GCP_PROJECT_ID)
    bucket = gcs_client.bucket(Config.GCS_BUCKET_RAW)
    
    # Dictionary to store results
    available_data = {
        'bus': [],
        'train': []
    }
    
    # Scan for each mode
    for mode in ['bus', 'train']:
        # List all files under journeys/{mode}/
        # This matches the upload structure: journeys/bus/2026/01/bus_od_202601.csv
        prefix = f'journeys/{mode}/'
        blobs = bucket.list_blobs(prefix=prefix)
        
        # Extract unique year-month values from paths
        # Paths look like: journeys/bus/2026/01/bus_od_202601.csv
        periods = set()
        for blob in blobs:
            # blob.name is the full path
            # Split by / and look for YYYYMM pattern in path
            parts = blob.name.split('/')
            # journeys/bus/2026/01/bus_od_202601.csv
            # parts = ['journeys', 'bus', '2026', '01', 'bus_od_202601.csv']
            if len(parts) >= 5 and parts[-1].endswith('.csv'):
                # Reconstruct YYYYMM from year and month folders
                year = parts[2]
                month = parts[3]
                if year.isdigit() and month.isdigit():
                    period = f"{year}{month}"
                    periods.add(period)
        
        available_data[mode] = sorted(list(periods))
    
    # Log what we found
    for mode, periods in available_data.items():
        if periods:
            logger.info(f"  ✓ Found {mode} data for: {', '.join(periods)}")
        else:
            logger.info(f"  ⚠ No {mode} data found in GCS")
    
    return available_data


def main():
    """
    Main function - handles command-line arguments and executes loads.
    
    This function:
    1. Parses command-line arguments
    2. Validates configuration
    3. Initializes BigQuery loader
    4. Executes requested load operations
    5. Reports results
    """
    # =========================================================================
    # Set up argument parser
    # =========================================================================
    # ArgumentParser = library for handling command-line arguments
    # It automatically generates help text and validates inputs
    
    parser = argparse.ArgumentParser(
        description='Load data from GCS into BigQuery tables',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Load all reference data
  python scripts/load_to_bq.py --reference
  
  # Load all OD data
  python scripts/load_to_bq.py --od
  
  # Load everything
  python scripts/load_to_bq.py --all
  
  # Load specific mode and period
  python scripts/load_to_bq.py --mode bus --period 202601
  
  # Load range of periods
  python scripts/load_to_bq.py --mode train --start 202512 --end 202602
        """
    )
    
    # Define command-line arguments
    # Each argument has: name, help text, and optional default value
    
    # Option 1: Load all data
    parser.add_argument(
        '--all',
        action='store_true',  # This is a flag (no value needed)
        help='Load all reference data and all OD data found in GCS'
    )
    
    # Option 2: Load only reference data
    parser.add_argument(
        '--reference',
        action='store_true',
        help='Load only reference data (bus_stops, train_stations)'
    )
    
    # Option 3: Load only OD data
    parser.add_argument(
        '--od',
        action='store_true',
        help='Load all OD data (bus and train) found in GCS'
    )
    
    # Option 4: Load specific mode
    parser.add_argument(
        '--mode',
        type=str,
        choices=['bus', 'train'],
        help='Load OD data for specific mode (bus or train)'
    )
    
    # Option 5: Load specific period
    parser.add_argument(
        '--period',
        type=str,
        help='Load OD data for specific period (YYYYMM format, e.g., 202601)'
    )
    
    # Option 6: Load range of periods
    parser.add_argument(
        '--start',
        type=str,
        help='Start period for range load (YYYYMM format, requires --end)'
    )
    
    parser.add_argument(
        '--end',
        type=str,
        help='End period for range load (YYYYMM format, requires --start)'
    )
    
    # Parse the arguments
    args = parser.parse_args()
    
    # =========================================================================
    # Validate arguments
    # =========================================================================
    
    # Check that user provided at least one option
    if not any([args.all, args.reference, args.od, args.mode]):
        parser.error("Must specify at least one option: --all, --reference, --od, or --mode")
    
    # Check that period-related arguments are used correctly
    if args.period and (args.start or args.end):
        parser.error("Cannot use --period with --start/--end. Choose one approach.")
    
    if args.start and not args.end:
        parser.error("--start requires --end")
    
    if args.end and not args.start:
        parser.error("--end requires --start")
    
    if (args.start or args.end) and not args.mode:
        parser.error("--start/--end requires --mode")
    
    # =========================================================================
    # Validate configuration
    # =========================================================================
    
    logger.info("🔧 Validating configuration...")
    try:
        Config.validate()
        logger.info("✓ Configuration validated")
    except ValueError as e:
        logger.error(f"❌ Configuration error: {e}")
        sys.exit(1)
    
    # =========================================================================
    # Initialize BigQuery loader
    # =========================================================================
    
    logger.info("🚀 Initializing BigQuery loader...")
    try:
        loader = BigQueryLoader()
        logger.info("✓ BigQuery loader initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize loader: {e}")
        sys.exit(1)
    
    # =========================================================================
    # Execute load operations based on arguments
    # =========================================================================
    
    try:
        # Handle --all flag: load everything
        if args.all:
            logger.info("\n📦 Loading ALL data (reference + OD)...\n")
            
            # Load reference data
            load_reference_data(loader)
            
            # Detect and load all OD data
            available_data = detect_available_periods()
            
            for mode in ['bus', 'train']:
                if available_data[mode]:
                    load_od_data_for_mode(loader, mode, available_data[mode])
                else:
                    logger.warning(f"⚠ No {mode} OD data found in GCS")
        
        # Handle --reference flag: load only reference data
        elif args.reference:
            load_reference_data(loader)
        
        # Handle --od flag: load all OD data
        elif args.od:
            logger.info("\n📊 Loading all OD data...\n")
            available_data = detect_available_periods()
            
            for mode in ['bus', 'train']:
                if available_data[mode]:
                    load_od_data_for_mode(loader, mode, available_data[mode])
        
        # Handle --mode flag: load specific mode
        elif args.mode:
            # Determine which periods to load
            if args.period:
                # Load single period
                periods = [args.period]
            elif args.start and args.end:
                # Load range of periods
                from src.load.bq_loader import generate_year_month_range
                periods = generate_year_month_range(args.start, args.end)
            else:
                # Load all available periods for this mode
                available_data = detect_available_periods()
                periods = available_data[args.mode]
            
            if periods:
                load_od_data_for_mode(loader, args.mode, periods)
            else:
                logger.warning(f"⚠ No data found for {args.mode}")
        
        # =====================================================================
        # Success!
        # =====================================================================
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ DATA LOAD COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)
        logger.info(f"\nData is now available in BigQuery:")
        logger.info(f"  Project: {Config.GCP_PROJECT_ID}")
        logger.info(f"  Dataset: {Config.BQ_DATASET}")
        logger.info(f"  Location: {Config.BQ_LOCATION}")
        logger.info(f"\nView data in BigQuery Console:")
        logger.info(f"  https://console.cloud.google.com/bigquery?project={Config.GCP_PROJECT_ID}")
        logger.info("=" * 80 + "\n")
        
    except Exception as e:
        logger.error(f"\n❌ Load failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


# Entry point
# This block runs when the script is executed directly (not imported)
if __name__ == '__main__':
    main()
