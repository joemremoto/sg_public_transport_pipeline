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

**Last updated**: March 25, 2026  
**Next session**: Session 3 completed - Infrastructure setup with Terraform

---

## Session 3: Infrastructure Setup with Terraform (March 25, 2026)

### 🎯 Goals
- Install and configure Terraform
- Install and authenticate gcloud CLI
- Create Terraform configuration for GCP infrastructure
- Provision cloud resources (GCS buckets, BigQuery dataset, service account)

---

### ✅ What We Built

#### 1. Terraform Configuration Files

**Created 5 Terraform files in `terraform/` folder:**

**`main.tf` (347 lines)**
- Terraform and provider configuration
- 2 GCS buckets (raw and processed data)
- 1 BigQuery dataset for analytics
- 1 Service account for pipeline authentication
- IAM permissions for service account
- Service account key generation
- Enabled required APIs (Storage, BigQuery, IAM)
- Lifecycle rules for cost optimization
- Labels for organization

**`variables.tf` (262 lines)**
- Variable declarations with types and descriptions
- Default values for optional parameters
- Validation rules (bucket name format, environment values, etc.)
- Configuration for:
  - Project ID (required)
  - Region (default: asia-east1)
  - Bucket names
  - BigQuery dataset name
  - Service account name
  - Data retention periods
  - Cost optimization settings

**`outputs.tf` (199 lines)**
- Resource names and IDs
- Console URLs for easy access
- Service account credentials (sensitive)
- Infrastructure summary
- Next steps instructions

**`terraform.tfvars.example` (75 lines)**
- Template for user configuration
- Comments explaining each variable
- Example values

**`README.md` (398 lines)**
- Complete usage guide
- Prerequisites and installation instructions
- Step-by-step workflow
- Common commands reference
- Troubleshooting section

#### 2. GCP Resources Provisioned

**Successfully created:**
- **GCS Bucket (Raw):** `sg-public-transport-data-raw`
  - Location: asia-east1
  - Storage class: STANDARD
  - Lifecycle: Move to NEARLINE after 30 days, delete after 90 days
  - Versioning enabled
  
- **GCS Bucket (Processed):** `sg-public-transport-data-processed`
  - Location: asia-east1
  - Storage class: STANDARD
  - Lifecycle: Move to COLDLINE after 60 days, delete after 180 days
  - Versioning enabled

- **BigQuery Dataset:** `sg_public_transport_analytics`
  - Location: asia-east1
  - Default partition expiration: 180 days
  - Ready for fact and dimension tables

- **Service Account:** `sg-transport-pipeline-v2`
  - IAM roles:
    - Storage Object Admin (both buckets)
    - BigQuery Admin (project-level)
    - BigQuery Data Editor (dataset-level)
  - JSON key extracted and saved

#### 3. Updated `.gitignore`

Added comprehensive Terraform ignore rules:
- `*.tfstate` - State files (contain sensitive data)
- `terraform.tfvars` - Actual values (may contain secrets)
- `.terraform/` - Terraform working directory
- `*.tfplan` - Plan output files

---

### 🐛 Issues Encountered & Fixed

#### Issue 1: Invalid `self` Reference in outputs.tf

**Problem:**
```hcl
- BigQuery Console: ${self.value.bigquery_dataset_url}
```
Error: The "self" object is not available in output blocks

**Solution:** Replaced with direct variable/resource references:
```hcl
- BigQuery Console: https://console.cloud.google.com/bigquery?project=${var.project_id}&...
```

**Lesson:** `self` only works in resource provisioner blocks, not outputs

---

#### Issue 2: BigQuery Dataset Name Validation

**Problem:**
```
Dataset name must be alphanumeric and underscores only.
```
Used hyphens in dataset name: `sg-public-transport-analytics`

**Solution:** Changed to underscores in `.env` and `terraform.tfvars`:
```hcl
bq_dataset = "sg_public_transport_analytics"
```

**Lesson:** BigQuery has different naming rules than GCS (GCS allows hyphens, BigQuery doesn't)

---

#### Issue 3: Service Account Already Exists

**Problem:**
```
Error: Service account sg-lta-pipeline-sa already exists
```
Manually created service account before Terraform

**Solution:** Changed service account name in `terraform.tfvars`:
```hcl
service_account_name = "sg-transport-pipeline-v2"
```

**Result:** Terraform created new service account, extracted new credentials

**Lesson:** Terraform manages resources it creates; existing resources cause conflicts unless imported

---

#### Issue 4: Extracting Service Account Key (Windows)

**Problem:** Base64 decoding failed in Git Bash and PowerShell:
```bash
base64: invalid input  # Git Bash
Exception: FormatException  # PowerShell
```

**Solution:** Created Python helper script `terraform/extract_key.py`:
```python
import subprocess
import base64

result = subprocess.run(["terraform", "output", "-raw", "service_account_key_json"], ...)
key_json = base64.b64decode(result.stdout).decode('utf-8')
# Save to file
```

**Lesson:** Windows has different base64 tools; Python is more portable

---

#### Issue 5: gcloud CLI Python Version Mismatch

**Problem:**
```
WARNING: Python 3.9.x is no longer officially supported
module 'OpenSSL.crypto' has no attribute 'sign'
```
gcloud bundled with Python 3.9, system has Python 3.10

**Solution (pending):** Set environment variable to use system Python:
```powershell
$env:CLOUDSDK_PYTHON = "C:\Users\...\Python310\python.exe"
```

**Lesson:** gcloud has bundled Python; can override with CLOUDSDK_PYTHON

---

### 🎓 Key Concepts Learned

#### Terraform Fundamentals
- **Infrastructure as Code (IaC)** - Define infrastructure in text files
- **Declarative syntax** - Describe desired state, Terraform figures out how
- **State management** - Terraform tracks what it created in `.tfstate` files
- **Variables system**:
  - `variables.tf` - Declarations (what inputs exist)
  - `terraform.tfvars` - Values (your actual config)
  - `main.tf` - Usage (how to use variables)
- **Outputs** - Display important info after apply
- **Providers** - Plugins that talk to cloud platforms (Google, AWS, etc.)

#### Terraform vs .env
- **Terraform (.tfvars)** - Build-time config (creates infrastructure)
- **Python (.env)** - Runtime config (uses infrastructure)
- Must keep values in sync manually
- Example: Terraform creates bucket "xyz", .env must reference same "xyz"

#### GCP Resource Naming
- **GCS buckets** - Must be globally unique, lowercase, hyphens allowed
- **BigQuery datasets** - Project-unique, underscores allowed, NO hyphens
- **Service accounts** - Project-unique, 6-30 chars, lowercase with hyphens

#### Cost Optimization Strategies
- **Storage classes** - STANDARD → NEARLINE → COLDLINE (cheaper but slower access)
- **Lifecycle rules** - Automatically move/delete old data
- **Partition expiration** - Auto-delete old BigQuery partitions
- **Versioning** - Protect against accidental deletion (costs extra storage)

#### IAM Best Practices
- **Service accounts** - For applications (not personal accounts)
- **Least privilege** - Grant minimum permissions needed
- **Scope permissions** - Bucket-level vs project-level
- **Separate accounts** - Different SA for dev/staging/prod

---

### 📊 Current Status

✅ **Completed:**
1. Terraform installed (via Scoop)
2. gcloud CLI installed and authenticated
3. Terraform configuration written (5 files)
4. GCP project selected: `sg-public-transport-pipeline`
5. Infrastructure provisioned:
   - 2 GCS buckets
   - 1 BigQuery dataset
   - 1 service account with permissions
6. Service account credentials extracted
7. `.env` values aligned with Terraform outputs

**Infrastructure Summary:**
```yaml
Project: sg-public-transport-pipeline
Region: asia-east1

Storage:
  - sg-public-transport-data-raw (raw data)
  - sg-public-transport-data-processed (transformed data)

BigQuery:
  - sg_public_transport_analytics (analytics tables)

Service Account:
  - sg-transport-pipeline-v2@sg-public-transport-pipeline.iam.gserviceaccount.com
```

---

### 🚀 Next Steps

Now that infrastructure exists, we can:

1. **Test access** - Verify service account can access GCS and BigQuery
2. **Upload data** - Create scripts to upload local data to GCS
3. **Load to BigQuery** - Create scripts to load from GCS to BigQuery tables
4. **Define schema** - Design BigQuery table schemas (fact and dimension tables)
5. **dbt project** - Set up transformation layer

---

### 💡 Reflections

**What went well:**
- Terraform abstracts away cloud console clicking
- Infrastructure changes are version-controlled and reviewable
- Outputs provide clear next steps
- Validation rules catch mistakes early
- Comprehensive documentation (README) makes it easy to remember commands

**What was challenging:**
- Windows-specific issues (base64 decoding, gcloud Python version)
- Understanding Terraform's three-file system (variables.tf, main.tf, tfvars)
- Keeping .env and terraform.tfvars in sync manually
- GCS vs BigQuery naming differences
- Service account conflicts from manual pre-creation

**Key insight:**
Terraform brings software engineering practices to infrastructure:
1. **Version control** - Track changes over time
2. **Code review** - Review infra changes before applying
3. **Documentation** - Code is self-documenting
4. **Reproducibility** - Same code = same infrastructure
5. **Collaboration** - Team can share configurations

But it requires thinking differently:
- Declarative (what you want) vs imperative (step-by-step)
- State management (Terraform needs to know what exists)
- Plan before apply (always preview changes)

---

### 📚 Resources That Helped

- [Terraform Documentation](https://www.terraform.io/docs)
- [Google Provider Docs](https://registry.terraform.io/providers/hashicorp/google/latest/docs)
- [GCS Lifecycle Management](https://cloud.google.com/storage/docs/lifecycle)
- [BigQuery Datasets](https://cloud.google.com/bigquery/docs/datasets)
- [IAM Service Accounts](https://cloud.google.com/iam/docs/service-accounts)

---

### 📝 Notes for Next Session

**Before starting next session:**
- [ ] Test service account credentials work
- [ ] Verify GCS bucket access: `gcloud storage ls gs://sg-public-transport-data-raw`
- [ ] Check BigQuery dataset exists in console
- [ ] Review Python google-cloud-storage library docs
- [ ] Think about GCS folder structure (year/month/mode)

**Questions to consider:**
- How to organize data in GCS? (flat vs hierarchical folders)
- Should we upload JSON as-is or convert to Parquet first?
- How to handle file versioning in GCS?
- Should BigQuery load be automatic (external tables) or manual (load jobs)?

---

**Last updated**: March 25, 2026  
**Next session**: Data Upload - Move local data to GCS, load to BigQuery
