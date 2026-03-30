"""
Module: gcs_uploader.py
Purpose: Upload local data files to Google Cloud Storage (GCS).
         This script handles the transfer of extracted LTA data from local storage
         to GCS buckets for cloud-based processing and analysis.

Why this exists:
- Moves data from local development environment to cloud storage
- Organizes data in GCS with proper directory structure (year/month partitioning)
- Handles both reference data (bus stops, train stations) and fact data (OD journeys)
- Provides progress tracking and error handling for uploads

Author: Joseph Emmanuel Remoto
Date: 2026-03-29

This is part of the Singapore Public Transport Analytics Pipeline.
Dependencies: google-cloud-storage, pathlib
"""

# Import statements - Libraries we need for GCS operations
import logging  # logging = record what the program does (better than print for production)
from pathlib import Path  # Path = modern way to work with file paths
from typing import Optional  # Optional = type hint meaning "can be None"
from datetime import datetime  # datetime = work with dates and times

from google.cloud import storage  # Google's official library for working with GCS
from google.cloud.exceptions import GoogleCloudError  # Exception types for GCS errors

from src.config.settings import Config  # Our configuration class

# Set up logging
# This creates a "logger" object that records messages with timestamps
# INFO level = log informational messages (not just errors)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GCSUploader:
    """
    Upload local data files to Google Cloud Storage buckets.
    
    This class handles:
    1. Connecting to GCS using service account credentials
    2. Creating bucket paths with proper structure (year/month partitioning)
    3. Uploading files with progress tracking
    4. Handling errors gracefully
    
    The class organizes data in GCS like this:
    
    bucket/
    ├── reference/
    │   ├── bus_stops.json          # Static reference data
    │   └── train_stations.json
    └── journeys/
        ├── bus/
        │   └── 2026/
        │       └── 01/
        │           └── bus_od_202601.csv
        └── train/
            └── 2026/
                └── 01/
                    └── train_od_202601.csv
    
    Usage:
        uploader = GCSUploader()
        
        # Upload a single file
        uploader.upload_file(
            local_path='data/raw/bus_stops.json',
            gcs_path='reference/bus_stops.json'
        )
        
        # Upload all extracted data for a month
        uploader.upload_monthly_data(year=2026, month=1)
    """
    
    def __init__(self):
        """
        Initialize the GCS uploader.
        
        This constructor:
        1. Validates that GCP configuration is set
        2. Creates a storage client (connection to GCS)
        3. Gets references to the buckets we'll upload to
        
        The storage client authenticates using the service account
        credentials specified in GOOGLE_APPLICATION_CREDENTIALS.
        
        Raises:
            ValueError: If required configuration is missing
            GoogleCloudError: If unable to connect to GCS
        """
        # Validate configuration before proceeding
        # This ensures we have all required settings (project ID, credentials, bucket names)
        Config.validate()
        
        logger.info("Initializing GCS uploader...")
        
        try:
            # Create a storage client
            # This is the main object we use to interact with GCS
            # It automatically uses credentials from GOOGLE_APPLICATION_CREDENTIALS env var
            self.client = storage.Client(project=Config.GCP_PROJECT_ID)
            
            # Get reference to the raw data bucket
            # bucket() doesn't check if bucket exists - just creates a reference
            # We'll verify existence on first upload
            self.raw_bucket = self.client.bucket(Config.GCS_BUCKET_RAW)
            
            logger.info(f"✅ Connected to GCS project: {Config.GCP_PROJECT_ID}")
            logger.info(f"✅ Target bucket: {Config.GCS_BUCKET_RAW}")
            
        except GoogleCloudError as e:
            # This catches errors from Google Cloud (auth failures, permission issues, etc.)
            logger.error(f"Failed to connect to GCS: {e}")
            raise
        except Exception as e:
            # Catch-all for other errors
            logger.error(f"Unexpected error initializing GCS uploader: {e}")
            raise
    
    def upload_file(
        self,
        local_path: str | Path,
        gcs_path: str,
        bucket_name: Optional[str] = None,
        max_retries: int = 3
    ) -> bool:
        """
        Upload a single file to Google Cloud Storage with retry logic.
        
        This method:
        1. Checks that the local file exists
        2. Creates a blob (GCS object) at the specified path
        3. Uploads the file content with appropriate timeout
        4. Retries on failure (up to max_retries times)
        5. Verifies the upload succeeded
        
        Parameters:
            local_path (str | Path): Path to local file to upload
                Example: 'data/raw/bus_stops.json'
            
            gcs_path (str): Destination path in GCS bucket (without gs:// prefix)
                Example: 'reference/bus_stops.json'
                This becomes: gs://bucket-name/reference/bus_stops.json
            
            bucket_name (str, optional): Bucket to upload to. 
                If None, uses Config.GCS_BUCKET_RAW
            
            max_retries (int): Maximum number of retry attempts for failed uploads
                Default: 3
        
        Returns:
            bool: True if upload successful, False otherwise
            
        Example:
            # Upload bus stops reference data
            success = uploader.upload_file(
                local_path='data/raw/bus_stops.json',
                gcs_path='reference/bus_stops.json'
            )
            
            if success:
                print("File uploaded successfully!")
        
        Technical Notes:
            - Files are uploaded with default storage class (STANDARD)
            - Overwrites existing files at same path (no versioning)
            - Uses resumable uploads for reliability
            - Timeout scales with file size (120s per 100MB)
            - Automatically retries on timeout/network errors
        """
        # Convert to Path object if string was provided
        # Path objects are more robust for file operations
        local_path = Path(local_path)
        
        # Check if file exists locally
        if not local_path.exists():
            logger.error(f"❌ Local file not found: {local_path}")
            return False
        
        # Check if it's actually a file (not a directory)
        if not local_path.is_file():
            logger.error(f"❌ Path is not a file: {local_path}")
            return False
        
        # Get file size for logging and timeout calculation
        # stat() returns file metadata, st_size is size in bytes
        file_size = local_path.stat().st_size
        # Convert bytes to MB for human-readable output
        file_size_mb = file_size / (1024 * 1024)
        
        # Calculate appropriate timeout based on file size
        # Base timeout: 120 seconds per 100MB, minimum 120 seconds
        # For 232MB file: 120 * (232/100) = 278 seconds
        timeout_seconds = max(120, int(120 * (file_size_mb / 100)))
        
        logger.info(f"📤 Uploading {local_path.name} ({file_size_mb:.2f} MB)...")
        logger.info(f"   From: {local_path}")
        logger.info(f"   To:   gs://{self.raw_bucket.name}/{gcs_path}")
        logger.info(f"   Timeout: {timeout_seconds}s (with {max_retries} retries)")
        
        # Retry loop
        for attempt in range(1, max_retries + 1):
            try:
                if attempt > 1:
                    logger.info(f"   Retry attempt {attempt}/{max_retries}...")
                
                # Create a blob (GCS object) at the destination path
                # blob = like a file in GCS (but called "blob" because it can be any data)
                blob = self.raw_bucket.blob(gcs_path)
                
                # Configure timeout for the upload
                # This is important for large files that take time to upload
                blob.chunk_size = 5 * 1024 * 1024  # 5MB chunks for better reliability
                
                # Upload the file with timeout
                # upload_from_filename() reads the local file and uploads its content
                # This is a blocking call - waits until upload completes
                blob.upload_from_filename(str(local_path), timeout=timeout_seconds)
                
                # Verify upload succeeded by checking if blob exists in GCS
                if blob.exists():
                    logger.info(f"✅ Successfully uploaded: {gcs_path}")
                    return True
                else:
                    logger.error(f"❌ Upload verification failed: {gcs_path}")
                    if attempt < max_retries:
                        logger.info(f"   Will retry...")
                        continue
                    return False
                    
            except GoogleCloudError as e:
                # GCS-specific errors (permission denied, bucket not found, etc.)
                logger.error(f"❌ GCS error uploading {local_path.name} (attempt {attempt}/{max_retries}): {e}")
                if attempt < max_retries:
                    logger.info(f"   Retrying in 5 seconds...")
                    import time
                    time.sleep(5)
                    continue
                return False
            except Exception as e:
                # Catch-all for unexpected errors (timeouts, SSL errors, etc.)
                error_msg = str(e)
                # Shorten long error messages
                if len(error_msg) > 200:
                    error_msg = error_msg[:200] + "..."
                logger.error(f"❌ Error uploading {local_path.name} (attempt {attempt}/{max_retries}): {error_msg}")
                if attempt < max_retries:
                    logger.info(f"   Retrying in 5 seconds...")
                    import time
                    time.sleep(5)
                    continue
                return False
        
        # If we get here, all retries failed
        return False
    
    def upload_reference_data(self) -> dict[str, bool]:
        """
        Upload reference data files (bus stops and train stations) to GCS.
        
        Reference data = static/slowly-changing data used for lookups
        These files contain dimension information (locations, names, codes)
        
        This method:
        1. Reads JSON array files from local storage
        2. Converts to NDJSON (newline-delimited JSON) format for BigQuery
        3. Uploads to GCS
        
        Why NDJSON?
        - BigQuery loads NDJSON much faster than JSON arrays
        - Standard format for BigQuery data imports
        - Each line is a complete JSON object (easier to process)
        
        Conversion example:
        JSON array:        NDJSON:
        [                  {"code": "01012", "name": "Stop A"}
          {...},           {"code": "01013", "name": "Stop B"}
          {...}
        ]
        
        This method looks for:
        - data/raw/bus_stops.json
        - data/raw/train_stations.json
        
        And uploads them as NDJSON to:
        - gs://bucket/reference/bus_stops.ndjson
        - gs://bucket/reference/train_stations.ndjson
        
        Returns:
            dict[str, bool]: Upload status for each file
                Example: {'bus_stops': True, 'train_stations': True}
        
        Example:
            uploader = GCSUploader()
            results = uploader.upload_reference_data()
            
            if all(results.values()):
                print("All reference data uploaded successfully!")
            else:
                print(f"Some uploads failed: {results}")
        """
        import json
        import tempfile
        
        logger.info("\n" + "="*70)
        logger.info("📚 UPLOADING REFERENCE DATA")
        logger.info("="*70)
        
        results = {}  # Dictionary to store upload results
        
        # Define reference files to upload
        # Format: (local filename, table name, GCS destination path)
        reference_files = [
            ('bus_stops.json', 'bus_stops', 'reference/bus_stops.ndjson'),
            ('train_stations.json', 'train_stations', 'reference/train_stations.ndjson')
        ]
        
        # Upload each reference file
        for local_filename, key, gcs_path in reference_files:
            local_path = Config.RAW_DATA_DIR / local_filename
            
            # Check if file exists
            if not local_path.exists():
                logger.error(f"❌ Local file not found: {local_path}")
                results[key] = False
                continue
            
            try:
                # Step 1: Read JSON array from local file
                logger.info(f"\n📄 Processing {local_filename}...")
                with open(local_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if not isinstance(data, list):
                    logger.error(f"❌ Expected JSON array, got {type(data)}")
                    results[key] = False
                    continue
                
                logger.info(f"   Loaded {len(data):,} records")
                
                # Step 2: Convert to NDJSON (newline-delimited JSON)
                # Each line is a separate JSON object
                logger.info(f"   Converting to NDJSON format...")
                
                # Create a temporary file for NDJSON
                with tempfile.NamedTemporaryFile(
                    mode='w',
                    encoding='utf-8',
                    suffix='.ndjson',
                    delete=False
                ) as tmp_file:
                    temp_path = tmp_file.name
                    
                    # Write each record as a separate line
                    for record in data:
                        # json.dumps converts dict to JSON string
                        # ensure_ascii=False keeps special characters (Chinese, etc.)
                        json_line = json.dumps(record, ensure_ascii=False)
                        tmp_file.write(json_line + '\n')
                
                logger.info(f"   Created NDJSON file: {len(data):,} lines")
                
                # Step 3: Upload NDJSON file to GCS
                success = self.upload_file(temp_path, gcs_path)
                results[key] = success
                
                # Step 4: Clean up temporary file
                import os
                os.unlink(temp_path)
                
            except json.JSONDecodeError as e:
                logger.error(f"❌ Invalid JSON in {local_filename}: {e}")
                results[key] = False
            except Exception as e:
                logger.error(f"❌ Error processing {local_filename}: {e}")
                results[key] = False
        
        logger.info("="*70 + "\n")
        return results
    
    def upload_od_data(self, year: int, month: int, mode: str) -> bool:
        """
        Upload origin-destination (OD) journey data for a specific month and mode.
        
        OD data = fact data containing aggregated trip counts between locations
        This is the core analytical data for our pipeline
        
        Parameters:
            year (int): Year of the data (e.g., 2026)
            month (int): Month number (1-12)
            mode (str): Transport mode - either 'bus' or 'train'
        
        Returns:
            bool: True if upload successful, False otherwise
            
        Example:
            # Upload January 2026 bus data
            success = uploader.upload_od_data(year=2026, month=1, mode='bus')
            
            # This uploads:
            # From: data/raw/bus_od_202601.csv
            # To:   gs://bucket/journeys/bus/2026/01/bus_od_202601.csv
        
        Technical Notes:
            - Data is partitioned by year/month for efficient querying
            - File naming convention: {mode}_od_{YYYYMM}.csv
            - Partitioned structure enables BigQuery external tables later
        """
        # Validate mode parameter
        if mode not in ['bus', 'train']:
            logger.error(f"❌ Invalid mode: {mode}. Must be 'bus' or 'train'")
            return False
        
        # Format month with leading zero (1 → 01, 12 → 12)
        # zfill(2) = "zero fill to width 2" → pads with zeros on left
        month_str = str(month).zfill(2)
        
        # Construct local file path in mode-specific subdirectory
        # Example: data/raw/bus/bus_od_202601.csv
        filename = f"{mode}_od_{year}{month_str}.csv"
        local_path = Config.RAW_DATA_DIR / mode / filename
        
        # Construct GCS path with partitioning
        # Example: journeys/bus/2026/01/bus_od_202601.csv
        # This structure enables partition pruning in BigQuery
        gcs_path = f"journeys/{mode}/{year}/{month_str}/{filename}"
        
        # Upload the file
        return self.upload_file(local_path, gcs_path)
    
    def upload_monthly_data(self, year: int, month: int) -> dict[str, bool]:
        """
        Upload all data for a specific month (both bus and train).
        
        This is a convenience method that uploads:
        1. Bus OD data for the month
        2. Train OD data for the month
        
        This method does NOT upload reference data (use upload_reference_data() for that)
        because reference data is uploaded once and rarely changes.
        
        Parameters:
            year (int): Year of the data (e.g., 2026)
            month (int): Month number (1-12, where 1=January)
        
        Returns:
            dict[str, bool]: Upload status for each transport mode
                Example: {'bus': True, 'train': True}
        
        Example:
            uploader = GCSUploader()
            
            # Upload all January 2026 data
            results = uploader.upload_monthly_data(year=2026, month=1)
            
            if all(results.values()):
                print("All data for the month uploaded successfully!")
            else:
                failed = [mode for mode, success in results.items() if not success]
                print(f"Failed uploads: {failed}")
        """
        logger.info("\n" + "="*70)
        logger.info(f"📅 UPLOADING DATA FOR {year}-{str(month).zfill(2)}")
        logger.info("="*70)
        
        results = {}
        
        # Upload data for each transport mode
        for mode in Config.TRANSPORT_MODES:  # ['bus', 'train']
            logger.info(f"\n🚌 Uploading {mode.upper()} data...")
            results[mode] = self.upload_od_data(year, month, mode)
        
        logger.info("="*70 + "\n")
        return results
    
    def upload_all_local_data(self) -> dict:
        """
        Upload all data files found in the local raw data directory.
        
        This method:
        1. Scans the local data/raw/ directory for all data files
        2. Uploads reference data (bus stops, train stations)
        3. Detects and uploads all monthly OD data files
        
        This is useful for initial setup when you have multiple months
        of historical data already extracted locally.
        
        Returns:
            dict: Comprehensive results showing what was uploaded
                {
                    'reference': {'bus_stops': True, 'train_stations': True},
                    'monthly': {
                        '2026-01': {'bus': True, 'train': True},
                        '2026-02': {'bus': True, 'train': True}
                    }
                }
        
        Example:
            uploader = GCSUploader()
            results = uploader.upload_all_local_data()
            
            # Check reference data uploads
            if all(results['reference'].values()):
                print("Reference data uploaded successfully!")
            
            # Check monthly data uploads
            for month_key, month_results in results['monthly'].items():
                if all(month_results.values()):
                    print(f"✅ {month_key} uploaded successfully")
                else:
                    print(f"❌ {month_key} had failures")
        """
        logger.info("\n" + "="*70)
        logger.info("🚀 UPLOADING ALL LOCAL DATA TO GCS")
        logger.info("="*70)
        
        results = {
            'reference': {},
            'monthly': {}
        }
        
        # Step 1: Upload reference data
        results['reference'] = self.upload_reference_data()
        
        # Step 2: Find and upload all monthly OD data
        # Scan for CSV files matching pattern: {mode}_od_{YYYYMM}.csv
        logger.info("\n🔍 Scanning for monthly OD data files...")
        
        raw_data_dir = Config.RAW_DATA_DIR
        
        # Scan in mode-specific subdirectories
        od_files = []
        for mode in Config.TRANSPORT_MODES:  # ['bus', 'train']
            mode_dir = raw_data_dir / mode
            if mode_dir.exists():
                # Find all OD CSV files in this mode directory
                mode_files = list(mode_dir.glob('*_od_*.csv'))
                od_files.extend(mode_files)
                logger.info(f"   Found {len(mode_files)} {mode} OD files")
        
        if not od_files:
            logger.warning("⚠️  No OD data files found in local directories")
        else:
            logger.info(f"   Total: {len(od_files)} OD data files")
            
            # Extract unique year-month combinations from filenames
            # We'll process by month to keep logs organized
            months_found = set()
            
            for file_path in od_files:
                # Parse filename: bus_od_202601.csv → year=2026, month=01
                # filename.stem removes the .csv extension
                parts = file_path.stem.split('_')  # ['bus', 'od', '202601']
                if len(parts) == 3:
                    yyyymm = parts[2]  # '202601'
                    if len(yyyymm) == 6:
                        year = int(yyyymm[:4])  # 2026
                        month = int(yyyymm[4:6])  # 1
                        months_found.add((year, month))
            
            # Upload data for each month found
            for year, month in sorted(months_found):
                month_key = f"{year}-{str(month).zfill(2)}"
                results['monthly'][month_key] = self.upload_monthly_data(year, month)
        
        # Print summary
        logger.info("\n" + "="*70)
        logger.info("📊 UPLOAD SUMMARY")
        logger.info("="*70)
        
        # Reference data summary
        ref_success = sum(results['reference'].values())
        ref_total = len(results['reference'])
        logger.info(f"Reference Data: {ref_success}/{ref_total} files uploaded")
        
        # Monthly data summary
        if results['monthly']:
            for month_key, month_results in results['monthly'].items():
                mode_success = sum(month_results.values())
                mode_total = len(month_results)
                status = "✅" if mode_success == mode_total else "❌"
                logger.info(f"{status} {month_key}: {mode_success}/{mode_total} modes uploaded")
        else:
            logger.info("Monthly Data: None found")
        
        logger.info("="*70 + "\n")
        
        return results


# Convenience function for quick uploads
def upload_data(year: int, month: int, include_reference: bool = False) -> bool:
    """
    Quick utility function to upload data for a specific month.
    
    This is a shortcut for common upload operations without needing
    to instantiate the GCSUploader class directly.
    
    Parameters:
        year (int): Year of the data
        month (int): Month number (1-12)
        include_reference (bool): Whether to also upload reference data
            Default False (reference data rarely changes)
    
    Returns:
        bool: True if all uploads successful, False if any failed
    
    Example:
        # Upload January 2026 data
        success = upload_data(year=2026, month=1)
        
        # Upload February 2026 data including reference files
        success = upload_data(year=2026, month=2, include_reference=True)
    """
    uploader = GCSUploader()
    
    results = {}
    
    # Upload reference data if requested
    if include_reference:
        results.update(uploader.upload_reference_data())
    
    # Upload monthly data
    monthly_results = uploader.upload_monthly_data(year, month)
    results.update(monthly_results)
    
    # Return True only if all uploads succeeded
    return all(results.values())


# Script entry point
if __name__ == "__main__":
    """
    This block runs when you execute: python src/upload/gcs_uploader.py
    Useful for testing uploads or running ad-hoc upload operations.
    """
    print("\n" + "="*70)
    print("🚀 GCS UPLOADER - STANDALONE EXECUTION")
    print("="*70 + "\n")
    
    try:
        # Create uploader instance
        uploader = GCSUploader()
        
        # Upload all local data
        # This is a full upload - use for initial setup or re-uploading everything
        results = uploader.upload_all_local_data()
        
        # Check if everything succeeded
        all_reference_success = all(results['reference'].values())
        all_monthly_success = all(
            all(month_results.values()) 
            for month_results in results['monthly'].values()
        ) if results['monthly'] else True
        
        if all_reference_success and all_monthly_success:
            print("\n✅ All uploads completed successfully!")
            exit(0)
        else:
            print("\n⚠️  Some uploads failed. Check logs above for details.")
            exit(1)
            
    except Exception as e:
        print(f"\n❌ Upload failed with error: {e}")
        logger.exception("Full error details:")
        exit(1)
