---
description: Python coding standards and best practices
---

# Python Coding Conventions

## Documentation Standards

**ALL Python scripts must be extensively documented for learning purposes.**

### Module Docstrings
Every Python file must have a docstring at the top:
```python
"""
Module: data_ingestion.py
Purpose: Downloads public transport data from Singapore's LTA API.
         Handles API authentication, file downloads, and data extraction.

Why this exists:
- LTA provides monthly OD data via API (not direct downloads)
- Links expire after 5 minutes, so immediate processing required
- Part of Phase 1: Data Extraction

Author: Joseph Emmanuel Remoto
Date: 2026-03-30
Dependencies: requests, zipfile, os, dotenv
"""
```

### Function Docstrings
Every function must explain what, why, inputs, outputs:
```python
def download_lta_data(year: int, month: int, mode: str) -> str:
    """
    Download public transport data from LTA API for a specific month.
    
    This function:
    1. Constructs the API endpoint URL
    2. Makes an HTTP request to download the data
    3. Saves the downloaded ZIP file to disk
    
    Parameters:
        year (int): The year we want data for (e.g., 2024)
        month (int): The month number (1-12, where 1=January)
        mode (str): Type of transport - either "bus" or "train"
    
    Returns:
        str: The file path where the downloaded ZIP file was saved
        
    Example:
        file_path = download_lta_data(2024, 3, "bus")
        # Result: "data/raw/bus/2024/03/od_bus_202403.zip"
    
    Notes:
        - API links expire after 5 minutes
        - Requires LTA_ACCOUNT_KEY in .env file
    """
    pass
```

### Inline Comments
Explain WHY, not WHAT:
```python
# ✅ Good - Explains reasoning
# Use timeout to prevent hanging on slow API responses
response = requests.get(url, timeout=30)

# ❌ Bad - States the obvious
# Make a GET request
response = requests.get(url, timeout=30)
```

### Beginner-Friendly Explanations
```python
# Load environment variables from .env file
# Environment variables = secret values (like API keys) stored separately from code
load_dotenv()

# Get the API key from environment variables
# getenv() = "get environment variable" - fetches the value safely
account_key = os.getenv('LTA_ACCOUNT_KEY')
```

---

## Code Style (PEP 8)

### Naming Conventions
- Variables: `snake_case` - `bus_stop_count`, `year_month`
- Functions: `snake_case` - `download_data()`, `parse_csv()`
- Classes: `PascalCase` - `LTAClient`, `GCSUploader`
- Constants: `UPPER_SNAKE_CASE` - `API_BASE_URL`, `MAX_RETRIES`

### Type Hints
Always use type hints for function parameters and returns:
```python
def format_date(year: int, month: int) -> str:
    return f"{year}{month:02d}"

def parse_csv(file_path: Path) -> list[dict]:
    # Implementation
    pass
```

### String Formatting
Use f-strings (Python 3.6+):
```python
# ✅ Good
message = f"Processing {count} records from {source}"

# ❌ Bad
message = "Processing " + str(count) + " records from " + source
message = "Processing {} records from {}".format(count, source)
```

### Line Length
- Maximum 100 characters per line
- Break long lines logically:
```python
# ✅ Good
result = some_function(
    param1=value1,
    param2=value2,
    param3=value3
)

# ❌ Bad
result = some_function(param1=value1, param2=value2, param3=value3, param4=value4, param5=value5)
```

---

## Error Handling

### Use Logging (Not Print)
```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_data(url: str) -> dict:
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        logger.info(f"Successfully fetched data from {url}")
        return response.json()
        
    except requests.exceptions.Timeout:
        logger.error(f"Request timed out after 30 seconds: {url}")
        raise
        
    except requests.exceptions.HTTPError as e:
        logger.error(f"API returned error status: {e}")
        raise
```

### Specific Exceptions
Catch specific exceptions, not bare `except`:
```python
# ✅ Good
try:
    data = json.load(file)
except json.JSONDecodeError as e:
    logger.error(f"Invalid JSON format: {e}")
    raise

# ❌ Bad
try:
    data = json.load(file)
except:  # Too broad!
    print("Error")
```

---

## Configuration Management

### Centralized Config
Use `src/config/settings.py` for all configuration:
```python
import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

class Config:
    """Centralized application configuration."""
    
    # LTA API
    LTA_ACCOUNT_KEY = os.getenv('LTA_ACCOUNT_KEY')
    LTA_BASE_URL = 'http://datamall2.mytransport.sg/ltaodataservice'
    
    # Google Cloud
    GCP_PROJECT_ID = os.getenv('GCP_PROJECT_ID')
    GCS_BUCKET_RAW = os.getenv('GCS_BUCKET_RAW')
    
    # Paths
    RAW_DATA_DIR = Path(__file__).parent.parent.parent / 'data' / 'raw'
    
    @classmethod
    def validate(cls):
        """Validate required environment variables are set."""
        if not cls.LTA_ACCOUNT_KEY:
            raise ValueError("LTA_ACCOUNT_KEY not found in .env")
        if not cls.GCP_PROJECT_ID:
            raise ValueError("GCP_PROJECT_ID not found in .env")

Config.validate()
```

### Never Hardcode Secrets
```python
# ✅ Good
api_key = os.getenv('LTA_ACCOUNT_KEY')

# ❌ Bad - NEVER DO THIS
api_key = "abc123xyz456"  # Exposed in version control!
```

---

## Package Management (uv)

**Use `uv` exclusively, not pip.**

```bash
# Add a new package
uv add requests

# Remove a package
uv remove requests

# Install all dependencies
uv sync

# Run a script (ensures correct virtual environment)
uv run python script.py

# Run tests
uv run pytest tests/
```

---

## File I/O

### Use Pathlib (Not os.path)
```python
from pathlib import Path

# ✅ Good
data_dir = Path(__file__).parent / 'data'
file_path = data_dir / 'raw' / 'bus_stops.json'

# ❌ Bad
import os
file_path = os.path.join(os.path.dirname(__file__), 'data', 'raw', 'bus_stops.json')
```

### Context Managers
Always use `with` for file operations:
```python
# ✅ Good - File automatically closes
with open(file_path, 'r') as f:
    data = json.load(f)

# ❌ Bad - Must remember to close
f = open(file_path, 'r')
data = json.load(f)
f.close()
```

---

## Testing

### Write Tests for Core Functions
```python
import pytest

def test_date_formatting():
    """Test that date formatting works correctly."""
    from utils.date_helper import format_date_for_api
    
    assert format_date_for_api(2024, 3) == "202403"
    assert format_date_for_api(2024, 1) == "202401"
    assert format_date_for_api(2024, 12) == "202412"

def test_api_connection():
    """Test that we can connect to LTA API."""
    # Test implementation
    pass
```

Run tests:
```bash
uv run pytest tests/
```

---

## Git Commit Messages

Use conventional commit format:
```
feat: Add bus data extraction script
fix: Handle API timeout errors correctly
docs: Update README with Docker setup instructions
refactor: Extract API client into separate module
test: Add tests for date formatting functions
chore: Update dependencies in pyproject.toml
```

---

## Common Patterns

### API Client Pattern
```python
import requests
from typing import Optional

class LTAClient:
    """Client for LTA DataMall API."""
    
    def __init__(self, account_key: str, base_url: str):
        self.account_key = account_key
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({'AccountKey': account_key})
    
    def get(self, endpoint: str, params: Optional[dict] = None) -> dict:
        """Make GET request to LTA API."""
        url = f"{self.base_url}/{endpoint}"
        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
```

### Retry Logic Pattern
```python
import time
from typing import Callable, TypeVar

T = TypeVar('T')

def retry_on_failure(func: Callable[..., T], max_retries: int = 3) -> T:
    """Retry function on failure with exponential backoff."""
    for attempt in range(1, max_retries + 1):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries:
                raise
            wait_time = 2 ** attempt
            logger.warning(f"Attempt {attempt} failed, retrying in {wait_time}s: {e}")
            time.sleep(wait_time)
```
