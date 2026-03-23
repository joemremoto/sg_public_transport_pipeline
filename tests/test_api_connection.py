"""
Module: test_api_connection.py
Purpose: Test individual LTA API endpoints to diagnose connection issues.

This test file helps us:
1. Verify API key authentication works
2. Test each endpoint individually
3. Diagnose 404 errors and find correct endpoint URLs
4. See detailed response information for debugging

Run this with: uv run python tests/test_api_connection.py
"""

# Import statements
import os
import sys
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key from environment
API_KEY = os.getenv('LTA_ACCOUNT_KEY')

# API base URL
BASE_URL = 'https://datamall2.mytransport.sg/ltaodataservice'

# Test configuration
# Use recent dates - LTA only provides up to 3 months of historical data
# Current date: March 2026, so we can try January or February 2026
TEST_YEAR = 2026
TEST_MONTH = 1  # January 2026 (should be available)


def print_section(title):
    """Print a section header for readability."""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def test_api_key():
    """
    Test 1: Verify API key is configured.
    
    This checks if the API key exists in the environment.
    If this fails, nothing else will work.
    """
    print_section("TEST 1: API Key Configuration")
    
    if not API_KEY:
        print("[FAIL] LTA_ACCOUNT_KEY not found in environment")
        print("       Check your .env file")
        return False
    
    print(f"[PASS] API Key found: {API_KEY[:4]}...{API_KEY[-4:]}")
    print(f"       Length: {len(API_KEY)} characters")
    return True


def test_endpoint(name, endpoint, params=None):
    """
    Test a specific API endpoint.
    
    This function:
    1. Makes request to the endpoint
    2. Shows the full URL being called
    3. Shows response status code
    4. Shows response headers
    5. Shows first 500 characters of response
    
    Parameters:
        name (str): Friendly name for the test
        endpoint (str): API endpoint path (e.g., "/BusStops")
        params (dict, optional): Query parameters
        
    Returns:
        bool: True if successful (status 200), False otherwise
    """
    print(f"\n--- Testing: {name} ---")
    
    # Build full URL
    url = f"{BASE_URL}{endpoint}"
    
    # Prepare headers with API key
    headers = {
        'AccountKey': API_KEY,
        'accept': 'application/json'
    }
    
    print(f"URL: {url}")
    if params:
        print(f"Params: {params}")
    print(f"Headers: AccountKey={API_KEY[:4]}...{API_KEY[-4:]}")
    
    try:
        # Make the request
        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=30
        )
        
        # Show status code
        print(f"\nStatus Code: {response.status_code}")
        
        # Show response headers (useful for debugging)
        print("\nResponse Headers:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")
        
        # Show response body preview
        print(f"\nResponse Body Preview (first 500 chars):")
        response_text = response.text[:500]
        print(response_text)
        if len(response.text) > 500:
            print("... (truncated)")
        
        # Check if successful
        if response.status_code == 200:
            print(f"\n[PASS] {name} - Success!")
            return True
        elif response.status_code == 401:
            print(f"\n[FAIL] {name} - Authentication failed (401)")
            print("       This means API key is invalid or expired")
            return False
        elif response.status_code == 404:
            print(f"\n[FAIL] {name} - Not found (404)")
            print("       This means the endpoint doesn't exist")
            print("       The endpoint URL might have changed")
            return False
        else:
            print(f"\n[FAIL] {name} - Unexpected status: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"\n[FAIL] {name} - Request timed out")
        print("       The API is not responding")
        return False
        
    except requests.exceptions.ConnectionError as e:
        print(f"\n[FAIL] {name} - Connection error")
        print(f"       {e}")
        print("       Check internet connection")
        return False
        
    except Exception as e:
        print(f"\n[FAIL] {name} - Unexpected error")
        print(f"       {e}")
        return False


def main():
    """
    Run all API tests in sequence.
    
    This will test:
    1. API key configuration
    2. Bus stops endpoint
    3. Bus services endpoint (simpler endpoint to test auth)
    4. Bus OD data endpoint
    5. Train OD data endpoint
    """
    print("\n" + "="*70)
    print("  LTA DataMall API Connection Tests")
    print("="*70)
    print(f"\nBase URL: {BASE_URL}")
    print(f"Test Date: {TEST_YEAR}-{TEST_MONTH:02d}")
    
    results = []
    
    # Test 1: API Key
    if not test_api_key():
        print("\n" + "="*70)
        print("  CRITICAL: API Key not configured. Fix this first!")
        print("="*70)
        return
    
    print_section("TEST 2: Individual Endpoint Tests")
    
    # Test 2: Bus Stops (reference data)
    results.append(test_endpoint(
        name="Bus Stops",
        endpoint="/BusStops",
        params={"$skip": 0}
    ))
    
    # Test 3: Bus Services (simpler endpoint)
    results.append(test_endpoint(
        name="Bus Services",
        endpoint="/BusServices"
    ))
    
    # Test 4: Bus Routes (another reference endpoint)
    results.append(test_endpoint(
        name="Bus Routes",
        endpoint="/BusRoutes"
    ))
    
    # Test 5: Bus OD Data (monthly data)
    results.append(test_endpoint(
        name="Bus Origin-Destination Data",
        endpoint="/PV/ODBus",
        params={"Date": f"{TEST_YEAR}{TEST_MONTH:02d}"}
    ))
    
    # Test 6: Train OD Data (monthly data)
    results.append(test_endpoint(
        name="Train Origin-Destination Data",
        endpoint="/PV/ODTrain",
        params={"Date": f"{TEST_YEAR}{TEST_MONTH:02d}"}
    ))
    
    # Summary
    print_section("TEST SUMMARY")
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nTests Passed: {passed}/{total}")
    
    if passed == 0:
        print("\nDIAGNOSIS:")
        print("  - All tests failed")
        print("  - If all showed 401: API key is invalid")
        print("  - If all showed 404: API endpoints have changed")
        print("  - Check response bodies above for error messages")
    elif passed < total:
        print("\nDIAGNOSIS:")
        print("  - Some tests passed, some failed")
        print("  - API key works (authentication is OK)")
        print("  - Failed endpoints may have moved or been deprecated")
        print("  - Check LTA DataMall documentation for current endpoints")
    else:
        print("\nDIAGNOSIS:")
        print("  - All tests passed!")
        print("  - API key is valid")
        print("  - All endpoints are working")
    
    print("\n" + "="*70)
    print("  NEXT STEPS:")
    print("="*70)
    
    if passed == 0:
        print("\n1. Verify your API key at: https://datamall.lta.gov.sg")
        print("2. Check if you need to re-generate your API key")
        print("3. Review the API documentation PDF for current endpoints")
    elif passed < total:
        print("\n1. Reference data (bus stops, etc.) may be static files now")
        print("2. Download from: https://datamall.lta.gov.sg/content/datamall/en/static-data.html")
        print("3. Focus on OD data endpoints for pipeline")
    else:
        print("\n1. All systems operational!")
        print("2. Proceed with building the rest of the pipeline")
    
    print("\n")


if __name__ == "__main__":
    main()
