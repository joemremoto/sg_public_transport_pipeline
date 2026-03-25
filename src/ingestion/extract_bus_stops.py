"""
Bus Stops Data Extraction Script

PURPOSE:
    This script fetches all bus stop information from the LTA DataMall API
    and saves it as a JSON file in our local data/raw/ folder.
    
    Bus stops are DIMENSION data (descriptive/reference data) that we'll use
    to understand WHERE bus journeys happen. Each stop has:
    - Bus stop code (unique identifier like "01012")
    - Description/name (e.g., "Hotel Grand Pacific")
    - Road name (e.g., "Victoria St")
    - Latitude/Longitude (exact location on map)

WHY THIS MATTERS:
    Later, when we analyze journey data (Origin-Destination), we'll need to
    know the names and locations of bus stops. This is foundational data.

USAGE:
    Run this script from the project root:
    
    uv run python src/ingestion/extract_bus_stops.py
    
OUTPUT:
    Creates: data/raw/bus_stops.json
    Contains: Array of all bus stops with their details
"""

# ============================================================================
# IMPORTS - Libraries and modules we need
# ============================================================================

import json                          # For saving data in JSON format
import logging                       # For printing progress messages
from pathlib import Path            # For working with file paths (modern way)
from typing import List, Dict, Any  # For type hints (documentation)
from datetime import datetime       # For timestamps in messages

# Import our custom modules
from src.config.settings import Config      # Configuration manager
from src.ingestion.lta_client import LTAClient  # API client


# ============================================================================
# LOGGING SETUP - So we can see what's happening
# ============================================================================

# Configure logging to show INFO level messages with timestamps
# Format: "2026-03-21 14:30:45 - INFO - Fetching bus stops..."
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Create a logger for this specific module
logger = logging.getLogger(__name__)


# ============================================================================
# MAIN EXTRACTION FUNCTION
# ============================================================================

def fetch_all_bus_stops() -> List[Dict[str, Any]]:
    """
    Fetch all bus stops from LTA API using pagination.
    
    PAGINATION EXPLAINED:
    The LTA API doesn't return all bus stops at once. It returns them in
    "pages" of 500 stops each. We need to:
    1. Fetch page 1 (stops 0-499)
    2. Fetch page 2 (stops 500-999)
    3. Continue until we get fewer than 500 stops (last page)
    
    This is like reading a book one chapter at a time instead of all at once.
    
    Returns:
        List of dictionaries, each containing one bus stop's information
        Example: [
            {
                "BusStopCode": "01012",
                "RoadName": "Victoria St",
                "Description": "Hotel Grand Pacific",
                "Latitude": 1.29684825487647,
                "Longitude": 103.85253591654006
            },
            ... (more stops)
        ]
    
    Raises:
        Exception: If API request fails or returns unexpected data
    """
    
    logger.info("Starting bus stops extraction...")
    
    # This list will accumulate ALL bus stops across all pages
    all_bus_stops = []
    
    # Pagination parameters
    skip = 0              # How many records to skip (starts at 0)
    page_size = 500       # LTA returns max 500 per request
    page_number = 1       # Just for logging/tracking which page we're on
    
    # Use context manager to ensure HTTP session is properly closed
    # The "with" statement automatically calls __enter__ and __exit__
    with LTAClient() as client:
        
        # Keep fetching until we get a page with fewer than 500 stops
        # This means we've reached the last page
        while True:
            logger.info(f"Fetching page {page_number} (skip={skip})...")
            
            try:
                # Make API request for this page
                # skip=0 gets stops 0-499
                # skip=500 gets stops 500-999
                # skip=1000 gets stops 1000-1499, etc.
                response = client.get_bus_stops(skip=skip)
                
                # Extract the actual bus stops from the response
                # API returns: {"odata.metadata": "...", "value": [stops]}
                # We only want the "value" array
                bus_stops = response.get('value', [])
                
                # How many stops did we get in this page?
                num_stops = len(bus_stops)
                logger.info(f"  Retrieved {num_stops} bus stops")
                
                # Add this page's stops to our complete list
                all_bus_stops.extend(bus_stops)
                
                # STOPPING CONDITION:
                # If we got fewer than 500 stops, this is the last page
                if num_stops < page_size:
                    logger.info(f"  Last page reached (only {num_stops} stops)")
                    break  # Exit the while loop
                
                # Prepare for next iteration
                skip += page_size    # Move to next page (skip next 500)
                page_number += 1     # Increment page counter for logging
                
            except Exception as e:
                # If something goes wrong, log the error and re-raise it
                logger.error(f"Error fetching page {page_number}: {e}")
                raise  # Re-raise the exception to stop execution
    
    # Log final count
    logger.info(f"Successfully fetched {len(all_bus_stops)} bus stops total")
    
    return all_bus_stops


def save_bus_stops(bus_stops: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save bus stops data to a JSON file.
    
    JSON FORMAT:
    JSON (JavaScript Object Notation) is a text format for storing structured data.
    It's human-readable and widely used for data exchange.
    
    Parameters:
        bus_stops: List of bus stop dictionaries to save
        output_path: Where to save the file (Path object)
    
    Raises:
        IOError: If file cannot be written
    """
    
    logger.info(f"Saving to {output_path}...")
    
    try:
        # Ensure the parent directory exists
        # For "data/raw/bus_stops.json", this creates "data/raw/" if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write the data to file
        # 'w' = write mode (overwrites if file exists)
        # encoding='utf-8' = support international characters
        with output_path.open('w', encoding='utf-8') as f:
            json.dump(
                bus_stops,          # Data to save
                f,                  # File handle
                indent=2,           # Pretty-print with 2-space indentation
                ensure_ascii=False  # Keep Chinese characters as-is (not \uXXXX)
            )
        
        # Log success with file size
        file_size_kb = output_path.stat().st_size / 1024  # Convert bytes to KB
        logger.info(f"Successfully saved {len(bus_stops)} bus stops ({file_size_kb:.2f} KB)")
        
    except Exception as e:
        logger.error(f"Error saving file: {e}")
        raise


def print_summary(bus_stops: List[Dict[str, Any]]) -> None:
    """
    Print a summary of the extracted data for verification.
    
    This helps us quickly check:
    - Did we get data?
    - What does a sample record look like?
    - Are there any obvious issues?
    
    Parameters:
        bus_stops: List of bus stop dictionaries
    """
    
    print("\n" + "="*70)
    print("BUS STOPS EXTRACTION SUMMARY")
    print("="*70)
    
    print(f"\nTotal bus stops extracted: {len(bus_stops)}")
    
    if bus_stops:
        print("\nSample bus stops (first 3):\n")
        
        # Show first 3 stops as examples
        for i, stop in enumerate(bus_stops[:3], start=1):
            print(f"  {i}. Code: {stop.get('BusStopCode')}")
            print(f"     Name: {stop.get('Description')}")
            print(f"     Road: {stop.get('RoadName')}")
            print(f"     Location: ({stop.get('Latitude')}, {stop.get('Longitude')})")
            print()
        
        # Show data structure of one stop
        print("Complete structure of first stop:")
        print(json.dumps(bus_stops[0], indent=2, ensure_ascii=False))
    
    else:
        print("\nWARNING: No bus stops retrieved!")
    
    print("\n" + "="*70 + "\n")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """
    Main function - coordinates the entire extraction process.
    
    WORKFLOW:
    1. Validate configuration (check API key is set)
    2. Fetch all bus stops from API
    3. Save to JSON file
    4. Print summary
    """
    
    logger.info("="*70)
    logger.info("BUS STOPS EXTRACTION STARTING")
    logger.info("="*70)
    
    try:
        # STEP 1: Validate configuration
        logger.info("Step 1: Validating configuration...")
        Config.validate()  # Will raise error if LTA_ACCOUNT_KEY not set
        logger.info("  Configuration valid")
        
        # STEP 2: Fetch data from API
        logger.info("Step 2: Fetching bus stops from LTA API...")
        bus_stops = fetch_all_bus_stops()
        
        # STEP 3: Save to file
        logger.info("Step 3: Saving to file...")
        output_path = Config.RAW_DATA_DIR / 'bus_stops.json'
        save_bus_stops(bus_stops, output_path)
        
        # STEP 4: Print summary
        logger.info("Step 4: Generating summary...")
        print_summary(bus_stops)
        
        # Success!
        logger.info("="*70)
        logger.info("BUS STOPS EXTRACTION COMPLETED SUCCESSFULLY")
        logger.info("="*70)
        logger.info(f"Output file: {output_path}")
        
    except Exception as e:
        # If anything goes wrong, log it and exit with error code
        logger.error("="*70)
        logger.error("BUS STOPS EXTRACTION FAILED")
        logger.error("="*70)
        logger.error(f"Error: {e}")
        
        # Print full error trace for debugging
        import traceback
        traceback.print_exc()
        
        # Exit with error code (non-zero = failure)
        exit(1)


# ============================================================================
# SCRIPT ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    """
    This block runs only when the script is executed directly.
    
    If you import this module elsewhere, this block won't run.
    Example:
        python src/ingestion/extract_bus_stops.py  <- Runs main()
        from src.ingestion import extract_bus_stops <- Doesn't run main()
    """
    main()
