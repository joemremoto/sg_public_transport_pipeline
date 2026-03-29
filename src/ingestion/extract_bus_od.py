"""
Bus Origin-Destination (OD) Data Extraction Script

PURPOSE:
    This script fetches monthly bus journey data from the LTA DataMall API.
    Unlike bus stops (dimension data), this is FACT data - it shows actual
    passenger journeys between bus stops.
    
    Each record shows:
    - Origin bus stop code (where journey started)
    - Destination bus stop code (where journey ended)
    - Time period (e.g., 6-7 AM, weekday vs weekend)
    - Number of trips (how many people made this journey)

WHY THIS MATTERS:
    This is the core transactional data for our analytics. We'll use it to:
    - Understand travel patterns (where people go, when they travel)
    - Identify busiest routes
    - Optimize bus schedules
    - Visualize passenger flows

IMPORTANT CONSTRAINTS:
    - Only last 3 months of data available
    - Data published monthly (around the 10th of following month)
    - Download links expire after 5 minutes
    - Files are large (10-50 MB compressed, 100-500 MB uncompressed)

USAGE:
    Run with year and month parameters:
    
    uv run python src/ingestion/extract_bus_od.py --year 2026 --month 1
    
    Or run without parameters to use current month minus 1:
    
    uv run python src/ingestion/extract_bus_od.py

OUTPUT:
    Creates: data/raw/bus/bus_od_YYYYMM.csv
    Example: data/raw/bus/bus_od_202601.csv (January 2026 data)
"""

# ============================================================================
# IMPORTS
# ============================================================================

import json
import logging
import zipfile
import io
import argparse
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta
import pandas as pd

# Import our custom modules
from src.config.settings import Config
from src.ingestion.lta_client import LTAClient


# ============================================================================
# LOGGING SETUP
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_default_year_month() -> tuple[int, int]:
    """
    Get default year and month (previous month from today).
    
    WHY PREVIOUS MONTH:
    LTA publishes data with a delay. Current month data isn't available yet.
    We default to previous month as it's most likely to be available.
    
    Returns:
        Tuple of (year, month)
        Example: If today is March 25, 2026 -> returns (2026, 2)
    """
    # Get current date
    today = datetime.now()
    
    # Subtract one month
    # timedelta doesn't support months directly, so we go back ~30 days
    # then extract the year/month from that date
    previous_month = today.replace(day=1) - timedelta(days=1)
    
    return previous_month.year, previous_month.month


def validate_year_month(year: int, month: int) -> None:
    """
    Validate that year and month are reasonable values.
    
    VALIDATION CHECKS:
    1. Month must be 1-12
    2. Date must not be in the future
    3. Date should be within last ~3 months (LTA constraint)
    
    Parameters:
        year: Year (e.g., 2026)
        month: Month (1-12)
    
    Raises:
        ValueError: If validation fails
    """
    # Check month range
    if not 1 <= month <= 12:
        raise ValueError(f"Month must be 1-12, got: {month}")
    
    # Check if date is in the future
    requested_date = datetime(year, month, 1)
    if requested_date > datetime.now():
        raise ValueError(
            f"Cannot request future data. Requested: {year}-{month:02d}, "
            f"Current: {datetime.now().strftime('%Y-%m')}"
        )
    
    # Warn if data might be too old (LTA only keeps 3 months)
    three_months_ago = datetime.now() - timedelta(days=90)
    if requested_date < three_months_ago:
        logger.warning(
            f"Requesting data from {year}-{month:02d}, which is more than "
            f"3 months old. LTA may not have this data available."
        )


def download_and_extract_od_data(
    year: int,
    month: int,
    output_dir: Path
) -> Path:
    """
    Download bus OD data for a specific month and extract the CSV.
    
    WORKFLOW:
    1. Call LTA API to get download link
    2. API returns a ZIP file (binary data)
    3. Extract CSV from ZIP (in memory)
    4. Parse CSV with pandas
    5. Save as CSV to disk
    
    Parameters:
        year: Year (e.g., 2026)
        month: Month (1-12)
        output_dir: Directory to save the CSV file
    
    Returns:
        Path to the saved CSV file
    
    Raises:
        Exception: If download or extraction fails
    """
    
    logger.info(f"Fetching bus OD data for {year}-{month:02d}...")
    
    try:
        # STEP 1: Download ZIP from API
        logger.info("Step 1: Requesting data from LTA API...")
        
        with LTAClient() as client:
            # This returns the ZIP file content as bytes
            zip_content = client.get_bus_od_data(year=year, month=month)
        
        logger.info(f"Downloaded ZIP file ({len(zip_content) / 1024:.2f} KB)")
        
        # STEP 2: Extract CSV from ZIP
        logger.info("Step 2: Extracting CSV from ZIP...")
        
        # Wrap bytes in BytesIO to create file-like object
        zip_buffer = io.BytesIO(zip_content)
        
        with zipfile.ZipFile(zip_buffer, 'r') as zip_ref:
            # List files in ZIP
            file_list = zip_ref.namelist()
            logger.info(f"Files in ZIP: {file_list}")
            
            # Find CSV file (should be only one)
            csv_files = [f for f in file_list if f.lower().endswith('.csv')]
            
            if not csv_files:
                raise FileNotFoundError(
                    f"No CSV file found in ZIP. Files: {file_list}"
                )
            
            csv_filename = csv_files[0]
            logger.info(f"Extracting: {csv_filename}")
            
            # Read CSV content
            with zip_ref.open(csv_filename) as csv_file:
                csv_content = csv_file.read()
        
        logger.info(f"Extracted CSV ({len(csv_content) / 1024 / 1024:.2f} MB)")
        
        # STEP 3: Parse CSV with pandas (for validation and preview)
        logger.info("Step 3: Parsing CSV data...")
        
        csv_buffer = io.BytesIO(csv_content)
        df = pd.read_csv(csv_buffer)
        
        logger.info(f"CSV has {len(df)} rows and {len(df.columns)} columns")
        logger.info(f"Columns: {df.columns.tolist()}")
        
        # STEP 4: Save to disk
        logger.info("Step 4: Saving to disk...")
        
        # Create filename with year and month
        output_filename = f"bus_od_{year}{month:02d}.csv"
        output_path = output_dir / output_filename
        
        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save CSV
        # We already have it as bytes, so just write directly
        with output_path.open('wb') as f:
            f.write(csv_content)
        
        file_size_mb = output_path.stat().st_size / 1024 / 1024
        logger.info(f"Saved to {output_path} ({file_size_mb:.2f} MB)")
        
        return output_path
        
    except Exception as e:
        logger.error(f"Error downloading/extracting OD data: {e}")
        raise


def print_summary(csv_path: Path) -> None:
    """
    Print summary statistics of the extracted OD data.
    
    Parameters:
        csv_path: Path to the CSV file
    """
    
    logger.info("Generating summary...")
    
    try:
        # Read CSV with pandas for analysis
        # We only read first 100k rows for quick preview (full file might be huge)
        df = pd.read_csv(csv_path, nrows=100000)
        
        print("\n" + "="*70)
        print("BUS ORIGIN-DESTINATION DATA SUMMARY")
        print("="*70)
        
        print(f"\nFile: {csv_path.name}")
        print(f"File size: {csv_path.stat().st_size / 1024 / 1024:.2f} MB")
        
        # Read full file to get exact row count
        # We need to count all rows, not just the preview
        total_rows = sum(1 for _ in open(csv_path)) - 1  # -1 for header
        print(f"Total rows: {total_rows:,}")
        
        print(f"\nColumns ({len(df.columns)}):")
        for col in df.columns:
            print(f"  - {col}")
        
        print("\nSample records (first 3):")
        print(df.head(3).to_string(index=False))
        
        # Basic statistics
        print("\nData Statistics (from first 100k rows):")
        
        if 'TOTAL_TRIPS' in df.columns or 'TOTAL_TAP_IN_VOLUME' in df.columns:
            trip_col = 'TOTAL_TRIPS' if 'TOTAL_TRIPS' in df.columns else 'TOTAL_TAP_IN_VOLUME'
            print(f"  Total trips (sample): {df[trip_col].sum():,}")
            print(f"  Average trips per OD pair: {df[trip_col].mean():.2f}")
            print(f"  Max trips for single OD pair: {df[trip_col].max():,}")
        
        if 'ORIGIN_PT_CODE' in df.columns and 'DESTINATION_PT_CODE' in df.columns:
            unique_origins = df['ORIGIN_PT_CODE'].nunique()
            unique_destinations = df['DESTINATION_PT_CODE'].nunique()
            print(f"  Unique origin stops: {unique_origins:,}")
            print(f"  Unique destination stops: {unique_destinations:,}")
        
        print("\n" + "="*70 + "\n")
        
    except Exception as e:
        logger.warning(f"Could not generate full summary: {e}")
        print(f"\nFile saved successfully: {csv_path}")


# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

def parse_arguments():
    """
    Parse command line arguments.
    
    ARGPARSE EXPLAINED:
    This allows users to run the script with options like:
      python script.py --year 2026 --month 1
    
    If no arguments provided, we use default (previous month).
    
    Returns:
        Namespace with parsed arguments (year, month)
    """
    parser = argparse.ArgumentParser(
        description='Extract bus origin-destination data from LTA DataMall',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract data for January 2026
  python src/ingestion/extract_bus_od.py --year 2026 --month 1
  
  # Extract data for previous month (default)
  python src/ingestion/extract_bus_od.py
        """
    )
    
    parser.add_argument(
        '--year',
        type=int,
        help='Year (e.g., 2026). Default: previous month'
    )
    
    parser.add_argument(
        '--month',
        type=int,
        help='Month (1-12). Default: previous month'
    )
    
    return parser.parse_args()


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """
    Main function - orchestrates the bus OD data extraction.
    """
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Determine year and month
    if args.year and args.month:
        year, month = args.year, args.month
        logger.info(f"Using provided date: {year}-{month:02d}")
    else:
        year, month = get_default_year_month()
        logger.info(f"Using default date (previous month): {year}-{month:02d}")
    
    logger.info("="*70)
    logger.info(f"BUS OD DATA EXTRACTION STARTING - {year}-{month:02d}")
    logger.info("="*70)
    
    try:
        # STEP 1: Validate inputs
        logger.info("Step 1: Validating inputs...")
        validate_year_month(year, month)
        Config.validate()  # Validate API key is set
        logger.info("  Validation passed")
        
        # STEP 2: Download and extract
        logger.info("Step 2: Downloading and extracting data...")
        # Save to mode-specific subdirectory (data/raw/bus/)
        output_dir = Config.RAW_DATA_DIR / 'bus'
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = download_and_extract_od_data(
            year=year,
            month=month,
            output_dir=output_dir
        )
        
        # STEP 3: Print summary
        logger.info("Step 3: Generating summary...")
        print_summary(output_path)
        
        # Success!
        logger.info("="*70)
        logger.info("BUS OD DATA EXTRACTION COMPLETED SUCCESSFULLY")
        logger.info("="*70)
        logger.info(f"Output file: {output_path}")
        
    except Exception as e:
        logger.error("="*70)
        logger.error("BUS OD DATA EXTRACTION FAILED")
        logger.error("="*70)
        logger.error(f"Error: {e}")
        
        import traceback
        traceback.print_exc()
        
        exit(1)


# ============================================================================
# SCRIPT ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()
