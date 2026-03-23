"""
Module: lta_client.py
Purpose: Client for interacting with Singapore's LTA DataMall API.
         Handles authentication, error handling, and data retrieval.

What this module does:
- Provides a clean interface to call LTA DataMall API endpoints
- Automatically adds authentication headers to requests
- Handles common errors (timeouts, rate limits, invalid responses)
- Returns data in easy-to-use format (Python dictionaries)

This is part of the Singapore Public Transport Analytics Pipeline.
API Reference: LTA_DataMall_API_User_Guide.pdf
API Portal: https://datamall.lta.gov.sg
"""

# Import statements - Libraries we need
import time  # time = for adding delays between retries
import logging  # logging = record what the program does (better than print)
from typing import Dict, List, Optional, Any  # Type hints for better code documentation
from datetime import datetime  # datetime = work with dates and times

import requests  # requests = library for making HTTP API calls
from requests.exceptions import (  # Import specific error types
    RequestException,  # Base error for all requests issues
    Timeout,  # Error when request takes too long
    HTTPError,  # Error when server returns error status (404, 500, etc.)
    ConnectionError  # Error when can't connect to server
)

# Import our configuration
from src.config.settings import Config


# Set up logging for this module
# Logger = object that records messages about what's happening
logger = logging.getLogger(__name__)  # __name__ = "src.ingestion.lta_client"


class LTAClient:
    """
    Client for interacting with LTA DataMall API.
    
    This class handles all communication with Singapore's LTA DataMall API.
    It automatically adds authentication, handles errors, and provides
    clean methods to fetch different types of transport data.
    
    Usage:
        from src.ingestion.lta_client import LTAClient
        
        # Create client instance
        client = LTAClient()
        
        # Fetch bus stops
        bus_stops = client.get_bus_stops()
        
        # Fetch bus OD data for March 2024
        bus_od_data = client.get_bus_od_data(year=2024, month=3)
    
    Attributes:
        base_url (str): The base URL for LTA API endpoints
        api_key (str): Your LTA AccountKey for authentication
        timeout (int): How long to wait for API response (seconds)
        session (requests.Session): Persistent HTTP session for efficiency
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: Optional[int] = None
    ):
        """
        Initialize the LTA API client.
        
        This sets up the client with API credentials and configuration.
        By default, it loads values from Config, but you can override them.
        
        Parameters:
            api_key (str, optional): LTA AccountKey. Defaults to Config value.
            base_url (str, optional): API base URL. Defaults to Config value.
            timeout (int, optional): Request timeout in seconds. Defaults to 30.
            
        Raises:
            ValueError: If api_key is not provided and not in Config
            
        Example:
            # Use default config
            client = LTAClient()
            
            # Or override with custom values
            client = LTAClient(api_key="custom_key", timeout=60)
        """
        # Load API credentials from Config or use provided values
        # "or" operator = use first value if it exists, otherwise use second
        self.api_key = api_key or Config.LTA_ACCOUNT_KEY
        self.base_url = base_url or Config.LTA_BASE_URL
        self.timeout = timeout or Config.LTA_API_TIMEOUT
        
        # Validate that we have an API key
        # Without this, we can't authenticate to the API
        if not self.api_key:
            raise ValueError(
                "LTA API key is required. "
                "Set LTA_ACCOUNT_KEY in your .env file or pass api_key parameter."
            )
        
        # Create a requests Session
        # Session = reuses HTTP connections (faster than creating new connection each time)
        # Like keeping a phone line open instead of hanging up and redialing
        self.session = requests.Session()
        
        # Set default headers for ALL requests through this session
        # Headers = metadata sent with HTTP requests
        self.session.headers.update({
            'AccountKey': self.api_key,  # Authentication - proves who we are
            'accept': 'application/json'  # We want responses in JSON format
        })
        
        # Log that client was initialized successfully
        logger.info(
            f"LTA Client initialized with base_url: {self.base_url}, "
            f"timeout: {self.timeout}s"
        )
    
    def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        max_retries: int = 3,
        retry_delay: int = 2
    ) -> Dict[str, Any]:
        """
        Make an HTTP GET request to LTA API with retry logic.
        
        This is a private method (starts with _) used internally by other methods.
        It handles the actual HTTP request and manages retries if something fails.
        
        Parameters:
            endpoint (str): API endpoint path (e.g., "/BusStops")
            params (dict, optional): Query parameters to send with request
            max_retries (int): How many times to retry if request fails
            retry_delay (int): Seconds to wait between retries
            
        Returns:
            dict: Parsed JSON response from API
            
        Raises:
            RequestException: If request fails after all retries
            ValueError: If response is not valid JSON
            
        Example:
            # This is called internally by public methods
            response = self._make_request("/BusStops", params={"$skip": 0})
        """
        # Construct full URL by combining base URL and endpoint
        # Example: "http://datamall2.../ltaodataservice" + "/BusStops"
        url = f"{self.base_url}{endpoint}"
        
        # Log what we're about to do (helpful for debugging)
        logger.info(f"Making request to: {url} with params: {params}")
        
        # Try the request multiple times (retry loop)
        for attempt in range(1, max_retries + 1):
            try:
                # Make the actual HTTP GET request
                # session.get() = send GET request using our configured session
                # timeout = how long to wait before giving up
                response = self.session.get(
                    url,
                    params=params,  # Query parameters (added to URL)
                    timeout=self.timeout
                )
                
                # Check if request was successful (status code 200-299)
                # raise_for_status() = raises HTTPError if status is 4xx or 5xx
                response.raise_for_status()
                
                # Parse JSON response into Python dictionary
                # response.json() = converts JSON text to dict
                data = response.json()
                
                # Log success
                logger.info(f"Request successful on attempt {attempt}")
                
                # Return the data
                return data
                
            except Timeout:
                # Request took too long (exceeded timeout)
                logger.warning(
                    f"Request timeout on attempt {attempt}/{max_retries} "
                    f"for {url}"
                )
                
                # If we've used all retries, give up
                if attempt == max_retries:
                    logger.error(f"Max retries reached for {url}")
                    raise  # Re-raise the exception to caller
                
                # Wait before trying again
                # Exponential backoff = wait longer each time (2s, 4s, 8s...)
                wait_time = retry_delay * attempt
                logger.info(f"Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
                
            except HTTPError as e:
                # Server returned an error status code
                status_code = e.response.status_code
                logger.error(
                    f"HTTP error {status_code} on attempt {attempt}/{max_retries} "
                    f"for {url}: {e}"
                )
                
                # Some errors shouldn't be retried
                if status_code in [400, 401, 403, 404]:
                    # 400 = Bad request (our fault, retrying won't help)
                    # 401 = Unauthorized (bad API key, retrying won't help)
                    # 403 = Forbidden (no permission, retrying won't help)
                    # 404 = Not found (endpoint doesn't exist, retrying won't help)
                    logger.error(f"Non-retryable error {status_code}, giving up")
                    raise
                
                # For other errors (500, 502, 503), retry
                if attempt == max_retries:
                    logger.error(f"Max retries reached for {url}")
                    raise
                
                wait_time = retry_delay * attempt
                logger.info(f"Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
                
            except ConnectionError as e:
                # Couldn't connect to server (network issue, server down, etc.)
                logger.error(
                    f"Connection error on attempt {attempt}/{max_retries} "
                    f"for {url}: {e}"
                )
                
                if attempt == max_retries:
                    logger.error(f"Max retries reached for {url}")
                    raise
                
                wait_time = retry_delay * attempt
                logger.info(f"Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
                
            except RequestException as e:
                # Catch-all for any other request errors
                logger.error(
                    f"Request error on attempt {attempt}/{max_retries} "
                    f"for {url}: {e}"
                )
                
                if attempt == max_retries:
                    logger.error(f"Max retries reached for {url}")
                    raise
                
                wait_time = retry_delay * attempt
                logger.info(f"Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
    
    def get_bus_stops(self, skip: int = 0) -> Dict[str, Any]:
        """
        Fetch bus stop data from LTA API.
        
        This retrieves information about all bus stops in Singapore including
        location (latitude/longitude), road name, and description.
        
        Note: LTA API returns data in pages of 500 records. Use 'skip' parameter
        to get subsequent pages.
        
        Parameters:
            skip (int): Number of records to skip (for pagination).
                       Default 0 (first page).
                       Use 500 for page 2, 1000 for page 3, etc.
        
        Returns:
            dict: API response containing bus stop data
                  Format: {
                      "odata.metadata": "...",
                      "value": [
                          {
                              "BusStopCode": "83139",
                              "RoadName": "Upp Changi Rd East",
                              "Description": "Opp Tropicana Condo",
                              "Latitude": 1.3521,
                              "Longitude": 103.9615
                          },
                          ...
                      ]
                  }
        
        Example:
            client = LTAClient()
            
            # Get first 500 bus stops
            page1 = client.get_bus_stops(skip=0)
            
            # Get next 500 bus stops
            page2 = client.get_bus_stops(skip=500)
            
            # Access the actual data
            bus_stops = page1['value']
            for stop in bus_stops:
                print(f"{stop['BusStopCode']}: {stop['Description']}")
        """
        logger.info(f"Fetching bus stops with skip={skip}")
        
        # Make request to BusStops endpoint
        # $skip is an OData query parameter (standard for APIs)
        return self._make_request(
            endpoint="/BusStops",
            params={"$skip": skip}
        )
    
    def get_bus_od_data(self, year: int, month: int) -> bytes:
        """
        Download bus origin-destination data for a specific month.
        
        This fetches the monthly OD (Origin-Destination) data showing how many
        trips occurred between each pair of bus stops, broken down by hour and day type.
        
        IMPORTANT: 
        - The API returns a link to a ZIP file that expires after 5 minutes!
        - Only last 3 months of data are available (historical access limited)
        - Data is published monthly (usually by the 10th of the following month)
        
        This method downloads the ZIP file immediately and returns the binary content.
        
        Parameters:
            year (int): Year (e.g., 2026)
            month (int): Month number (1-12, where 1=January)
            
        Returns:
            bytes: Binary content of the ZIP file containing CSV data
                   You'll need to extract this with zipfile module
        
        Raises:
            ValueError: If month is not 1-12 or data not available for that date
            RequestException: If download fails
            
        Example:
            client = LTAClient()
            
            # Download January 2026 bus OD data
            zip_content = client.get_bus_od_data(year=2026, month=1)
            
            # Save to file
            with open('bus_od_202601.zip', 'wb') as f:
                f.write(zip_content)
            
            # Or extract directly in memory
            import zipfile
            import io
            zip_file = zipfile.ZipFile(io.BytesIO(zip_content))
            # Now you can extract files from zip_file
        """
        # Validate month parameter
        if not 1 <= month <= 12:
            raise ValueError(f"Month must be 1-12, got: {month}")
        
        # Format date as YYYYMM (e.g., 202403 for March 2024)
        # {:02d} = format as 2 digits with leading zero (3 becomes 03)
        date_param = f"{year}{month:02d}"
        
        logger.info(f"Fetching bus OD data for {date_param}")
        
        # Step 1: Get the download link from API
        # The API first returns JSON with a link to the actual ZIP file
        response = self._make_request(
            endpoint="/PV/ODBus",
            params={"Date": date_param}
        )
        
        # Extract the download link from response
        # Response format: {"value": [{"Link": "https://..."}]}
        if not response.get('value') or len(response['value']) == 0:
            raise ValueError(f"No data available for {date_param}")
        
        download_link = response['value'][0].get('Link')
        
        if not download_link:
            raise ValueError(f"No download link in response for {date_param}")
        
        logger.info(f"Got download link: {download_link}")
        logger.warning("Download link expires in 5 minutes! Downloading immediately...")
        
        # Step 2: Download the ZIP file from the link
        # This is a different URL (not the API), so we make a direct request
        try:
            download_response = self.session.get(
                download_link,
                timeout=300  # 5 minutes timeout for large files
            )
            download_response.raise_for_status()
            
            logger.info(f"Successfully downloaded {len(download_response.content)} bytes")
            
            # Return the raw binary content of the ZIP file
            return download_response.content
            
        except RequestException as e:
            logger.error(f"Failed to download ZIP file: {e}")
            raise
    
    def get_train_od_data(self, year: int, month: int) -> bytes:
        """
        Download train origin-destination data for a specific month.
        
        This fetches the monthly OD data showing how many trips occurred between
        each pair of train stations, broken down by hour and day type.
        
        Works exactly like get_bus_od_data() but for train/MRT data.
        
        IMPORTANT:
        - Only last 3 months of data are available (historical access limited)
        - Data is published monthly (usually by the 10th of the following month)
        - Download links expire after 5 minutes
        
        Parameters:
            year (int): Year (e.g., 2026)
            month (int): Month number (1-12)
            
        Returns:
            bytes: Binary content of the ZIP file containing CSV data
        
        Raises:
            ValueError: If month is not 1-12 or data not available for that date
            RequestException: If download fails
            
        Example:
            client = LTAClient()
            
            # Download January 2026 train OD data
            zip_content = client.get_train_od_data(year=2026, month=1)
            
            # Save to file
            with open('train_od_202601.zip', 'wb') as f:
                f.write(zip_content)
        """
        # Validate month
        if not 1 <= month <= 12:
            raise ValueError(f"Month must be 1-12, got: {month}")
        
        # Format date as YYYYMM
        date_param = f"{year}{month:02d}"
        
        logger.info(f"Fetching train OD data for {date_param}")
        
        # Get download link
        response = self._make_request(
            endpoint="/PV/ODTrain",
            params={"Date": date_param}
        )
        
        # Extract link
        if not response.get('value') or len(response['value']) == 0:
            raise ValueError(f"No data available for {date_param}")
        
        download_link = response['value'][0].get('Link')
        
        if not download_link:
            raise ValueError(f"No download link in response for {date_param}")
        
        logger.info(f"Got download link: {download_link}")
        logger.warning("Download link expires in 5 minutes! Downloading immediately...")
        
        # Download ZIP file
        try:
            download_response = self.session.get(
                download_link,
                timeout=300  # 5 minutes for large files
            )
            download_response.raise_for_status()
            
            logger.info(f"Successfully downloaded {len(download_response.content)} bytes")
            
            return download_response.content
            
        except RequestException as e:
            logger.error(f"Failed to download ZIP file: {e}")
            raise
    
    def close(self):
        """
        Close the HTTP session.
        
        This releases any resources held by the session (HTTP connections).
        Call this when you're done using the client.
        
        Good practice: Use client in a context manager (with statement)
        to ensure it's always closed properly.
        
        Example:
            # Manual close
            client = LTAClient()
            try:
                data = client.get_bus_stops()
            finally:
                client.close()
            
            # Better: Use context manager (we'll implement this next)
            with LTAClient() as client:
                data = client.get_bus_stops()
            # Automatically closed when exiting 'with' block
        """
        if self.session:
            self.session.close()
            logger.info("LTA Client session closed")
    
    def __enter__(self):
        """
        Enable use as context manager (with statement).
        
        This is called when entering a 'with' block.
        
        Example:
            with LTAClient() as client:
                data = client.get_bus_stops()
        """
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Enable use as context manager (with statement).
        
        This is called when exiting a 'with' block.
        Automatically closes the session.
        
        Parameters are exception info if an error occurred in the with block.
        """
        self.close()
        # Return False to propagate any exceptions
        return False


# Module-level convenience function
def create_client() -> LTAClient:
    """
    Create and return a new LTA API client.
    
    This is a convenience function that creates a client with default config.
    
    Returns:
        LTAClient: Configured API client ready to use
        
    Example:
        from src.ingestion.lta_client import create_client
        
        client = create_client()
        bus_stops = client.get_bus_stops()
    """
    return LTAClient()


# If this file is run directly (not imported), test the client
if __name__ == "__main__":
    # This block only runs if you execute: python src/ingestion/lta_client.py
    # Useful for testing
    
    # Set up logging to see what's happening
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("Testing LTA API Client...\n")
    
    try:
        # Create client
        print("1. Creating LTA client...")
        with LTAClient() as client:
            
            # Test 1: Fetch bus stops (now works with HTTPS!)
            print("\n2. Fetching first 5 bus stops...")
            bus_stops_response = client.get_bus_stops(skip=0)
            bus_stops = bus_stops_response.get('value', [])[:5]
            
            print(f"   Found {len(bus_stops)} bus stops (showing first 5):")
            for stop in bus_stops:
                print(f"   - {stop['BusStopCode']}: {stop['Description']}")
            
            print("\n3. LTA API Client is working!")
            print("\n   Note: For detailed endpoint testing, run:")
            print("   uv run python tests/test_api_connection.py")
            
    except ValueError as e:
        print(f"\nConfiguration error: {e}")
        print("   Make sure LTA_ACCOUNT_KEY is set in your .env file")
        
    except Exception as e:
        print(f"\nError testing client: {e}")
        import traceback
        traceback.print_exc()
