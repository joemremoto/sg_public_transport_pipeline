"""
Train Stations Data Extraction Script

PURPOSE:
    This script downloads train station information from LTA DataMall's website.
    Unlike bus stops (which use the API), train station data is provided as a
    downloadable ZIP file containing a CSV.
    
    Train stations are DIMENSION data that describe WHERE train journeys happen.
    Each station has:
    - Station code (e.g., "NS1" for North South Line station 1)
    - Station name in English
    - Station name in Chinese
    
WHY THIS MATTERS:
    When analyzing train journey data (Origin-Destination), we need station names
    and codes to understand the routes people take. This is foundational reference data.

TECHNICAL NOTE:
    This script demonstrates a different data extraction pattern:
    1. HTTP download of binary file (ZIP)
    2. In-memory extraction (no temp files)
    3. CSV parsing
    4. JSON conversion for consistency with other dimension data

USAGE:
    Run this script from the project root:
    
    uv run python src/ingestion/extract_train_stations.py
    
OUTPUT:
    Creates: data/raw/train_stations.json
    Contains: Array of all train stations with their codes and names
"""

# ============================================================================
# IMPORTS - Libraries and modules we need
# ============================================================================

import json                           # For saving data in JSON format
import logging                        # For progress tracking
import zipfile                        # For extracting ZIP files
import io                            # For in-memory file operations
from pathlib import Path             # For working with file paths
from typing import List, Dict, Any   # For type hints
import requests                      # For HTTP downloads
import pandas as pd                  # For reading Excel files

# Import our custom modules
from src.config.settings import Config  # Configuration manager


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
# CONFIGURATION - Train station data URL
# ============================================================================

# Direct download link from LTA DataMall
# This ZIP contains an Excel file (.xls) with station codes and Chinese names
TRAIN_STATIONS_URL = (
    "https://datamall.lta.gov.sg/content/dam/datamall/datasets/"
    "Geospatial/Train%20Station%20Codes%20and%20Chinese%20Names.zip"
)

# The file inside is Excel format (.xls), not CSV
EXPECTED_FILE_EXTENSIONS = [".xls", ".xlsx"]  # Excel formats


# ============================================================================
# MAIN EXTRACTION FUNCTIONS
# ============================================================================

def download_zip_file(url: str, timeout: int = 30) -> bytes:
    """
    Download ZIP file from URL and return binary content.
    
    HTTP DOWNLOAD EXPLAINED:
    When you download a file, your computer makes an HTTP GET request to a URL.
    The server responds with the file content as binary data (bytes).
    
    Parameters:
        url: Web address of the ZIP file
        timeout: How long to wait before giving up (seconds)
    
    Returns:
        bytes: Raw binary content of the ZIP file
    
    Raises:
        requests.RequestException: If download fails
        requests.Timeout: If download takes too long
    """
    
    logger.info(f"Downloading ZIP file from LTA DataMall...")
    logger.info(f"URL: {url}")
    
    try:
        # Make HTTP GET request
        # stream=False means download entire file at once (it's small ~50KB)
        response = requests.get(url, timeout=timeout)
        
        # Check if download was successful
        # HTTP 200 = OK, anything else is an error
        response.raise_for_status()
        
        # Get file size for logging
        file_size_kb = len(response.content) / 1024
        logger.info(f"Successfully downloaded ZIP file ({file_size_kb:.2f} KB)")
        
        # Return the raw binary content
        return response.content
        
    except requests.Timeout:
        logger.error(f"Download timed out after {timeout} seconds")
        raise
        
    except requests.RequestException as e:
        logger.error(f"Download failed: {e}")
        raise


def extract_excel_from_zip(zip_content: bytes) -> bytes:
    """
    Extract Excel file from ZIP archive.
    
    IN-MEMORY EXTRACTION:
    We don't save the ZIP to disk. Instead, we:
    1. Wrap the bytes in an io.BytesIO object (acts like a file in memory)
    2. Pass it to zipfile.ZipFile
    3. Extract and return the Excel file content as bytes
    4. Discard the ZIP (no cleanup needed!)
    
    Parameters:
        zip_content: Binary content of the ZIP file
    
    Returns:
        bytes: Binary content of the Excel file
    
    Raises:
        zipfile.BadZipFile: If ZIP is corrupted
        FileNotFoundError: If no Excel file found in ZIP
    """
    
    logger.info("Extracting Excel file from ZIP archive...")
    
    try:
        # Create a file-like object in memory from the bytes
        zip_buffer = io.BytesIO(zip_content)
        
        # Open the ZIP file from memory
        with zipfile.ZipFile(zip_buffer, 'r') as zip_ref:
            
            # List all files in the ZIP
            file_list = zip_ref.namelist()
            logger.info(f"Files in ZIP: {file_list}")
            
            # Find the Excel file
            # Look for .xls or .xlsx files
            excel_files = [
                f for f in file_list 
                if any(f.lower().endswith(ext) for ext in EXPECTED_FILE_EXTENSIONS)
            ]
            
            if not excel_files:
                raise FileNotFoundError(
                    f"No Excel file found in ZIP. Files present: {file_list}"
                )
            
            # Use the first Excel file found
            excel_filename = excel_files[0]
            logger.info(f"Extracting: {excel_filename}")
            
            # Read the Excel file content as binary
            with zip_ref.open(excel_filename) as excel_file:
                excel_content = excel_file.read()
            
            logger.info(f"Successfully extracted Excel file ({len(excel_content)} bytes)")
            return excel_content
            
    except zipfile.BadZipFile:
        logger.error("Downloaded file is not a valid ZIP archive")
        raise
        
    except Exception as e:
        logger.error(f"Error extracting Excel file: {e}")
        raise


def parse_train_stations_excel(excel_content: bytes) -> List[Dict[str, Any]]:
    """
    Parse Excel content and convert to list of dictionaries.
    
    EXCEL PARSING WITH PANDAS:
    Pandas can read Excel files directly from bytes in memory.
    It's much easier than manually parsing Excel formats!
    
    EXPECTED FORMAT:
    Column headers: stn_code, mrt_station_english, mrt_station_chinese
    Example rows:
    NS1  | Jurong East     | 裕廊东
    NS2  | Bukit Batok     | 武吉巴督
    
    We convert each row to a dictionary:
    {
        "station_code": "NS1",
        "station_name": "Jurong East",
        "station_name_chinese": "裕廊东"
    }
    
    Parameters:
        excel_content: Binary content of Excel file
    
    Returns:
        List of dictionaries, each representing one train station
    
    Raises:
        Exception: If Excel cannot be parsed or has unexpected format
    """
    
    logger.info("Parsing Excel data...")
    
    try:
        # Wrap bytes in BytesIO to make it file-like
        excel_buffer = io.BytesIO(excel_content)
        
        # Read Excel file with pandas
        # pandas automatically handles .xls and .xlsx formats
        # engine='xlrd' is needed for old .xls format
        df = pd.read_excel(excel_buffer, engine='xlrd')
        
        logger.info(f"Excel columns found: {df.columns.tolist()}")
        logger.info(f"Excel has {len(df)} rows")
        
        # Convert DataFrame to list of dictionaries
        stations = []
        
        for _, row in df.iterrows():
            # Keep original field names to match BigQuery schema
            station = {
                "stn_code": str(row.get('stn_code', '')).strip(),
                "mrt_station_english": str(row.get('mrt_station_english', '')).strip(),
                "mrt_station_chinese": str(row.get('mrt_station_chinese', '')).strip(),
                "mrt_line_english": str(row.get('mrt_line_english', '')).strip()
            }
            
            # Only add if station code exists and is not NaN
            if station['stn_code'] and station['stn_code'] != 'nan':
                stations.append(station)
        
        logger.info(f"Parsed {len(stations)} train stations")
        
        return stations
        
    except Exception as e:
        logger.error(f"Error parsing Excel file: {e}")
        logger.error(
            "Hint: Make sure 'xlrd' is installed for .xls files. "
            "Run: uv add xlrd"
        )
        raise


def save_train_stations(stations: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save train stations data to JSON file.
    
    Parameters:
        stations: List of station dictionaries
        output_path: Where to save the file
    
    Raises:
        IOError: If file cannot be written
    """
    
    logger.info(f"Saving to {output_path}...")
    
    try:
        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write JSON file
        with output_path.open('w', encoding='utf-8') as f:
            json.dump(
                stations,
                f,
                indent=2,
                ensure_ascii=False  # Keep Chinese characters readable
            )
        
        # Log success with file size
        file_size_kb = output_path.stat().st_size / 1024
        logger.info(
            f"Successfully saved {len(stations)} train stations "
            f"({file_size_kb:.2f} KB)"
        )
        
    except Exception as e:
        logger.error(f"Error saving file: {e}")
        raise


def print_summary(stations: List[Dict[str, Any]]) -> None:
    """
    Print summary of extracted train stations.
    
    Parameters:
        stations: List of station dictionaries
    """
    
    print("\n" + "="*70)
    print("TRAIN STATIONS EXTRACTION SUMMARY")
    print("="*70)
    
    print(f"\nTotal train stations extracted: {len(stations)}")
    
    if stations:
        print("\nSample train stations (first 5):\n")
        
        # Show first 5 stations
        for i, station in enumerate(stations[:5], start=1):
            print(f"  {i}. Code: {station.get('stn_code')}")
            print(f"     Name (EN): {station.get('mrt_station_english')}")
            print(f"     Line: {station.get('mrt_line_english')}")
            print()
        
        # Count by line (NS, EW, CC, etc.)
        print("Stations by MRT line:")
        line_counts = {}
        for station in stations:
            # Extract line code (e.g., "NS" from "NS1")
            code = station.get('stn_code', '')
            if code:
                # Line code is the letters at the start
                line = ''.join(c for c in code if c.isalpha())
                line_counts[line] = line_counts.get(line, 0) + 1
        
        for line, count in sorted(line_counts.items()):
            print(f"  {line}: {count} stations")
        
        # Show complete structure of first station (without Chinese to avoid encoding issues)
        print("\nComplete structure of first station:")
        first = stations[0].copy()
        # Keep only ASCII-safe fields for display
        safe_station = {
            "stn_code": first.get("stn_code"),
            "mrt_station_english": first.get("mrt_station_english"),
            "mrt_line_english": first.get("mrt_line_english")
        }
        print(json.dumps(safe_station, indent=2))
    
    
    else:
        print("\nWARNING: No stations retrieved!")
    
    print("\n" + "="*70 + "\n")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """
    Main function - orchestrates the train stations extraction process.
    
    WORKFLOW:
    1. Download ZIP file from LTA website
    2. Extract CSV from ZIP (in memory)
    3. Parse CSV into structured data
    4. Save as JSON
    5. Print summary
    """
    
    logger.info("="*70)
    logger.info("TRAIN STATIONS EXTRACTION STARTING")
    logger.info("="*70)
    
    try:
        # STEP 1: Download ZIP file
        logger.info("Step 1: Downloading ZIP file...")
        zip_content = download_zip_file(TRAIN_STATIONS_URL)
        
        # STEP 2: Extract Excel from ZIP
        logger.info("Step 2: Extracting Excel from ZIP...")
        excel_content = extract_excel_from_zip(zip_content)
        
        # STEP 3: Parse Excel data
        logger.info("Step 3: Parsing Excel data...")
        stations = parse_train_stations_excel(excel_content)
        
        # STEP 4: Save to file
        logger.info("Step 4: Saving to file...")
        output_path = Config.RAW_DATA_DIR / 'train_stations.json'
        save_train_stations(stations, output_path)
        
        # STEP 5: Print summary
        logger.info("Step 5: Generating summary...")
        print_summary(stations)
        
        # Success!
        logger.info("="*70)
        logger.info("TRAIN STATIONS EXTRACTION COMPLETED SUCCESSFULLY")
        logger.info("="*70)
        logger.info(f"Output file: {output_path}")
        
    except Exception as e:
        # If anything goes wrong, log it and exit with error code
        logger.error("="*70)
        logger.error("TRAIN STATIONS EXTRACTION FAILED")
        logger.error("="*70)
        logger.error(f"Error: {e}")
        
        # Print full error trace for debugging
        import traceback
        traceback.print_exc()
        
        # Exit with error code
        exit(1)


# ============================================================================
# SCRIPT ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    """
    This block runs only when script is executed directly.
    """
    main()
