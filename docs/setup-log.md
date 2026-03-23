# Pipeline Setup Log

> **Purpose**: Track our progress, challenges, and learnings as we build the Singapore Public Transport Analytics Pipeline
> 
> **Audience**: Future me (and anyone learning data engineering!)

---

## Session 1: Foundation & API Client (March 21, 2026)

### 🎯 Goals
- Set up project structure following Python best practices
- Configure environment and dependencies
- Build LTA API client with proper error handling
- Validate API connectivity

---

### ✅ What We Built

#### 1. Project Structure
```
sg_public_transport_pipeline/
├── src/                    # All Python source code
│   ├── config/            # Configuration management
│   │   ├── __init__.py
│   │   └── settings.py    # Centralized config loader
│   ├── ingestion/         # Data extraction scripts
│   │   ├── __init__.py
│   │   └── lta_client.py  # LTA API client
│   └── utils/             # Helper functions (future)
├── tests/                 # All test scripts
│   └── test_api_connection.py  # API endpoint validator
├── data/                  # Local data storage (git-ignored)
│   ├── raw/              # Raw data from API
│   └── processed/        # Cleaned/transformed data
├── docs/                  # Documentation
│   ├── glossary.md       # Technical terms explained
│   └── setup-log.md      # This file!
├── .env                   # Environment variables (git-ignored)
├── .gitignore            # Files to exclude from Git
└── pyproject.toml        # Project metadata & dependencies
```

**Why this structure?**
- `src/` keeps all code organized and importable
- `tests/` separates testing from production code
- `data/` is git-ignored (never commit raw data!)
- `docs/` makes the project easier to understand

---

#### 2. Dependency Management with `uv`

**Created `pyproject.toml`** with:
- Project metadata (name, version, description)
- Python version requirement (>=3.10)
- Core dependencies:
  - `requests` - HTTP requests to LTA API
  - `python-dotenv` - Load environment variables from .env
  - `pandas` - Data manipulation (future use)
  - `google-cloud-storage` - Upload to GCS (future use)
  - `google-cloud-bigquery` - Load to BigQuery (future use)
- Dev dependencies:
  - `pytest` - Testing framework
  - `black` - Code formatter
  - `ruff` - Fast linter

**Commands used:**
```bash
# Install all dependencies
uv sync

# Run Python scripts with the virtual environment
uv run python <script.py>
```

---

#### 3. Configuration Management (`src/config/settings.py`)

**Purpose**: One central place for all configuration
- Loads environment variables from `.env` file
- Validates required variables are set
- Provides easy access via `Config.VARIABLE_NAME`
- Masks secrets when printing config

**Key learnings:**
- `@classmethod` decorator = method that operates on the class itself, not instances
- Class attributes = shared across all instances
- Type hints (`str`, `int`, `Optional[str]`) = document what type each variable should be

**Example usage:**
```python
from src.config.settings import Config

# Access configuration anywhere in the project
api_key = Config.LTA_ACCOUNT_KEY
base_url = Config.LTA_BASE_URL
```

---

#### 4. LTA API Client (`src/ingestion/lta_client.py`)

**Purpose**: Interact with LTA DataMall API safely and reliably

**Features:**
- **Authentication**: Automatically adds API key to request headers
- **Retry logic**: Tries 3 times if request fails (handles temporary network issues)
- **Error handling**: Clear error messages for different failure types
- **Context manager**: Auto-closes HTTP session with `with LTAClient() as client:`
- **Pagination support**: Fetch data in chunks (LTA limits to 500 records per request)

**Methods:**
1. `get_bus_stops()` - Fetch all bus stops (name, location, code)
2. `get_bus_od_data(year, month)` - Download monthly bus journey data
3. `get_train_od_data(year, month)` - Download monthly train journey data

**Key learnings:**
- `__init__` = constructor (runs when creating an object)
- `self` = refers to the specific instance
- `Optional[str] = None` = parameter can be a string or None (optional)
- `for` loops iterate over sequences
- `try`/`except` catches errors without crashing
- Python uses **indentation** (not brackets) for code blocks!

---

#### 5. API Testing Script (`tests/test_api_connection.py`)

**Purpose**: Validate each API endpoint works correctly

**What it tests:**
1. API key is configured
2. Bus stops endpoint returns data
3. Bus services endpoint returns data
4. Bus routes endpoint returns data
5. Bus OD data returns download link
6. Train OD data returns download link

**Output includes:**
- Full request URL
- HTTP status code (200 = success, 404 = not found, 401 = unauthorized)
- Response headers
- Body preview (first 500 characters)

---

### 🐛 Issues We Encountered & Fixed

#### Issue 1: `uv sync` Failed - "Unable to determine which files to ship"

**Problem:**
```
ValueError: Unable to determine which files to ship inside the wheel using the following heuristics...
```

**Root cause:** The `hatchling` build backend didn't know where our Python packages were located.

**Solution:** Added to `pyproject.toml`:
```toml
[tool.hatch.build.targets.wheel]
packages = ["src"]
```

**Lesson:** When using `src/` layout, must explicitly tell the build system where packages are!

---

#### Issue 2: `.env` and Other Files Still Tracked by Git

**Problem:** Added patterns to `.gitignore` but files still showing in `git status`

**Root cause:** `.gitignore` only affects **untracked** files. These files were already committed.

**Solution:**
```bash
# Remove from Git tracking (but keep locally)
git rm --cached .env
git rm --cached rules.md

# Commit the removal
git add .
git commit -m "Remove tracked files now in .gitignore"
```

**Lesson:** `.gitignore` is preventive, not retroactive. Files must be explicitly un-tracked.

---

#### Issue 3: `.gitignore` Patterns Not Working

**Problem:** Patterns like `credentials/` weren't working. Files not graying out in IDE.

**Root cause:** Trailing spaces in `.gitignore` patterns break them!
```gitignore
credentials/     # This has trailing spaces - BREAKS!
credentials/     # This is clean - WORKS!
```

**Solution:** Removed ALL trailing spaces from `.gitignore`

**How to verify:**
```bash
# Check if a file would be ignored
git check-ignore -v <filename>

# Should show which pattern matched
# If no output, the file is NOT being ignored
```

**Lesson:** `.gitignore` patterns must be exact - no trailing whitespace!

---

#### Issue 4: API Returned 404 for All Endpoints

**Problem:** All API calls failed with `HTTP 404 Not Found`

**Root cause #1:** Using `http://` instead of `https://`
- Old URL: `http://datamall2.mytransport.sg/ltaodataservice`
- Correct URL: `https://datamall2.mytransport.sg/ltaodataservice`

**Solution:** Updated `LTA_BASE_URL` in `src/config/settings.py` to use HTTPS

**Result:** Bus Stops, Bus Services, and Bus Routes endpoints now work! ✅

---

#### Issue 5: OD Data Endpoints Still 404

**Problem:** `/PV/ODBus` and `/PV/ODTrain` still returned 404 even with HTTPS

**Root cause #2:** Requested data too old (February 2024)
- LTA only keeps **last 3 months** of historical data
- Today is March 21, 2026
- February 2024 is nearly 2 years old!

**Solution:** Updated test to use recent date:
```python
TEST_YEAR = 2026   # Current year
TEST_MONTH = 1     # January (within 3-month window)
```

**Result:** All endpoints now working! ✅

**Critical learnings:**
1. **Always use HTTPS** for LTA API
2. **OD data limited to last 3 months** - plan data collection accordingly
3. **Download links expire in 5 minutes** - must download immediately after getting URL
4. **Data published monthly** - usually by the 10th of following month

---

### 🎓 Key Concepts Learned

#### Python Fundamentals
- **Modules & Packages**: How to organize Python code
- **Imports**: `from src.config import Config`
- **Classes & Objects**: Blueprint vs instance
- **Methods**: Functions that belong to a class
- **`self` vs `cls`**: Instance vs class reference
- **Type hints**: `Optional[str]`, `int`, `bytes`
- **Decorators**: `@classmethod`, `@staticmethod`
- **Context managers**: `with` statement for cleanup
- **Exception handling**: `try`/`except` blocks
- **For loops**: Iterating over sequences
- **F-strings**: `f"Value is {variable}"`

#### Git & Version Control
- `.gitignore` syntax and limitations
- Difference between tracked/untracked files
- `git rm --cached` to untrack files
- `git check-ignore -v` to debug ignore rules
- Never commit secrets or credentials!

#### APIs & HTTP
- HTTP methods: GET, POST
- Status codes: 200 (OK), 404 (Not Found), 401 (Unauthorized)
- Headers: Metadata about request/response
- Authentication: AccountKey in headers
- Rate limiting and timeouts
- JSON response format
- Download links and expiration

#### Data Engineering Concepts
- Separation of concerns (config, ingestion, transformation)
- Environment-based configuration (.env files)
- Error handling and retries
- Logging for debugging
- Testing API connectivity before building pipeline
- Data freshness and historical windows

---

### 📊 Current Status

✅ **Completed:**
1. Project directory structure
2. Dependency management with `uv`
3. Comprehensive `.gitignore` (with credentials rotation)
4. Centralized configuration (`settings.py`)
5. LTA API client (`lta_client.py`) with 3 endpoints
6. API connection tests (`test_api_connection.py`)
7. All API endpoints validated and working

**All 5 endpoints confirmed working:**
- ✅ Bus Stops (returns 200 OK)
- ✅ Bus Services (returns 200 OK)
- ✅ Bus Routes (returns 200 OK)
- ✅ Bus OD Data (returns 200 OK with S3 link)
- ✅ Train OD Data (returns 200 OK with S3 link)

---

### 🚀 Next Steps

Now that our foundation is solid, we can move forward with:

1. **Data Extraction Scripts** (next immediate step)
   - Script to download and extract OD data
   - Script to fetch and save bus stops/stations
   - Script to download train station CSV from LTA website
   - Save all raw data to `data/raw/`

2. **GCP Setup**
   - Create dedicated GCP project for this pipeline
   - Create GCS bucket for raw data storage
   - Create BigQuery dataset for analytics
   - Set up service account with proper permissions
   - Test upload to GCS and BigQuery

3. **Terraform for Infrastructure**
   - Define GCP project structure as code
   - Automate bucket and dataset creation
   - Manage IAM permissions
   - Enable required APIs

4. **Data Transformation with dbt**
   - Design dimension tables (bus stops, train stations, dates, time periods)
   - Design fact tables (bus journeys, train journeys)
   - Implement star schema
   - Add data quality tests

5. **Orchestration with Airflow**
   - Containerize with Docker
   - Create DAG for monthly data pipeline
   - Schedule automatic runs
   - Set up monitoring and alerts

6. **Visualization with Streamlit**
   - Build interactive dashboard
   - Show journey patterns by time/day
   - Compare bus vs train usage
   - Deploy to cloud

---

### 💡 Reflections

**What went well:**
- Systematic debugging approach (test one thing at a time)
- Creating diagnostic tools (`test_api_connection.py`) before assuming code is correct
- Reading API documentation carefully for constraints (3-month window)
- Using beginner-friendly explanations and extensive comments

**What was challenging:**
- Understanding Python's import system and package structure
- Debugging `.gitignore` issues (trailing spaces are invisible!)
- Discovering LTA's data availability constraints through trial and error
- Balancing between "just make it work" vs "understand how it works"

**Key insight:**
Building a data pipeline isn't just about writing code - it's about:
1. **Understanding the data source** (API constraints, data freshness)
2. **Proper setup** (environment, dependencies, configuration)
3. **Error handling** (what can go wrong? how do we recover?)
4. **Testing** (validate each component works before building on top)
5. **Documentation** (so future-me understands what past-me was thinking!)

---

### 📚 Resources That Helped

- [LTA DataMall API User Guide](https://datamall.lta.gov.sg/content/dam/datamall/datasets/LTA_DataMall_API_User_Guide.pdf)
- [Python Requests Documentation](https://requests.readthedocs.io/)
- [Git Documentation on .gitignore](https://git-scm.com/docs/gitignore)
- [Python Type Hints Guide](https://docs.python.org/3/library/typing.html)
- `docs/glossary.md` - Our custom glossary of pipeline terms!

---

### 📝 Notes for Next Session

**Before starting next session:**
- [ ] Review `glossary.md` for any unclear terms
- [ ] Read through LTA API guide sections on data formats
- [ ] Check LTA website for latest available OD data month
- [ ] Think about GCP project naming convention

**Questions to consider:**
- How much historical data should we backfill? (Last 3 months?)
- Should we partition BigQuery tables by date?
- How should we handle pipeline failures? (Retry? Alert?)
- What metrics are most important for the dashboard?

---

**Last updated**: March 21, 2026  
**Next session**: TBD - Data extraction scripts
