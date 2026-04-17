# Singapore Public Transport Analytics Pipeline - Setup Guide

Complete setup guide for cloning and running this project on a new machine with a fresh GCP account.

**Time Required:** 1-2 hours  
**Prerequisites:** Windows/Mac/Linux with internet connection

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Clone Repository](#clone-repository)
3. [GCP Account Setup](#gcp-account-setup)
4. [GCP Project & Resources](#gcp-project--resources)
5. [Service Account & Credentials](#service-account--credentials)
6. [gcloud CLI Setup](#gcloud-cli-setup)
7. [Python Environment](#python-environment)
8. [Environment Variables](#environment-variables)
9. [LTA API Setup](#lta-api-setup)
10. [Testing the Pipeline](#testing-the-pipeline)
    - [Phase 1: Test Data Extraction](#phase-1-test-data-extraction)
    - [Phase 2: Test Infrastructure](#phase-2-test-infrastructure-already-done-via-terraform)
    - [Phase 3: Test GCS Upload](#phase-3-test-gcs-upload)
    - [Phase 4: Test BigQuery Load](#phase-4-test-bigquery-load)
    - [Phase 5: Test dbt Transformation](#phase-5-test-dbt-transformation)
    - [Phase 6: Docker & Airflow Setup](#phase-6-docker--airflow-setup)
    - [Phase 7: Test Streamlit Dashboard](#phase-7-test-streamlit-dashboard)
11. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

- **Git** (version control)
  - Windows: https://git-scm.com/download/win
  - Mac: `brew install git`
  - Linux: `sudo apt install git`

- **Python 3.10+**
  - Download: https://www.python.org/downloads/
  - Verify: `python --version`

- **pip** (Python package manager)
  - Comes with Python
  - Upgrade: `python -m pip install --upgrade pip`

### Optional but Recommended

- **uv** (fast Python package manager)
  - Install: `pip install uv`
  - Or follow: https://github.com/astral-sh/uv

- **VS Code** or **Cursor** (code editor)
  - VS Code: https://code.visualstudio.com/
  - Cursor: https://cursor.sh/

### For Airflow Orchestration (Phase 6)

- **Docker Desktop** (for running Airflow)
  - Windows: https://docs.docker.com/desktop/install/windows-install/
  - Mac: https://docs.docker.com/desktop/install/mac-install/
  - Linux: https://docs.docker.com/desktop/install/linux-install/
  - Requires: 4GB+ RAM available
  - Note: Can skip if you prefer running pipeline manually

---

## Clone Repository

### Step 1: Clone the Repository

```bash
# Navigate to your projects folder
cd ~/projects  # Mac/Linux
# or
cd C:\Users\YourName\projects  # Windows

# Clone the repository
git clone https://github.com/YOUR_USERNAME/sg_public_transport_pipeline.git

# Navigate into the project
cd sg_public_transport_pipeline

# Verify project structure
ls -la  # Mac/Linux
dir     # Windows
```

**Expected structure:**
```
sg_public_transport_pipeline/
├── .cursor/
├── airflow/
├── credentials/       # Will be empty (git-ignored)
├── data/             # Will be empty (git-ignored)
├── docs/
├── scripts/
├── sg_transport_dbt/
├── src/
├── streamlit_app/
├── terraform/
├── .gitignore
├── pyproject.toml
└── README.md
```

---

## GCP Account Setup

### Step 1: Create Google Account (if needed)

1. Go to: https://accounts.google.com/signup
2. Create new Gmail account
3. Verify email address

### Step 2: Create GCP Account

1. Go to: https://console.cloud.google.com/
2. Sign in with your Google account
3. Accept Terms of Service
4. **Setup Billing:**
   - Click "Activate" or "Enable Billing"
   - Enter payment information
   - New accounts get $300 free credits (90 days)

### Step 3: Note Your GCP Information

Keep track of:
- **Google Account Email:** your-email@gmail.com
- **Billing Account ID:** (visible in GCP Console → Billing)

---

## GCP Project & Resources

### Step 1: Create GCP Project

**Option A: Via GCP Console (Web UI)**

1. Go to: https://console.cloud.google.com/
2. Click project dropdown (top bar)
3. Click "New Project"
4. Enter details:
   - **Project Name:** `sg-public-transport-pipeline`
   - **Project ID:** `sg-public-transport-pipeline` (or custom)
   - **Location:** Leave as default organization
5. Click "Create"
6. **Note your Project ID** (you'll need this)

**Option B: Via gcloud CLI (after installing, see below)**

```bash
# Create project
gcloud projects create sg-public-transport-pipeline --name="Singapore Transport Analytics"

# Set as default project
gcloud config set project sg-public-transport-pipeline

# Link billing account (replace with your billing account ID)
gcloud beta billing projects link sg-public-transport-pipeline \
  --billing-account=YOUR-BILLING-ACCOUNT-ID
```

### Step 2: Enable Required APIs

**Via GCP Console:**
1. Go to: https://console.cloud.google.com/apis/library
2. Search and enable each:
   - ✅ BigQuery API
   - ✅ Cloud Storage API
   - ✅ Cloud Resource Manager API
   - ✅ Identity and Access Management (IAM) API

**Via gcloud CLI:**
```bash
gcloud services enable bigquery.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable cloudresourcemanager.googleapis.com
gcloud services enable iam.googleapis.com
```

### Step 3: Create Resources with Terraform

**Navigate to terraform directory:**
```bash
cd terraform
```

**Initialize Terraform:**
```bash
terraform init
```

**Review what will be created:**
```bash
terraform plan
```

**Create resources:**
```bash
terraform apply
```

Type `yes` when prompted.

**Resources created:**
- 2 GCS buckets (raw + processed)
- 1 BigQuery dataset
- 1 Service account with IAM roles

**Expected output:**
```
Apply complete! Resources: 5 added, 0 changed, 0 destroyed.

Outputs:
bigquery_dataset = "sg_public_transport_analytics"
gcs_bucket_processed = "sg-public-transport-data-processed"
gcs_bucket_raw = "sg-public-transport-data-raw"
project_id = "sg-public-transport-pipeline"
service_account_email = "sg-transport-pipeline-v2@sg-public-transport-pipeline.iam.gserviceaccount.com"
```

**Save these outputs!** You'll need them for configuration.

---

## Service Account & Credentials

### Step 1: Create Service Account Key

**Via GCP Console:**

1. Go to: https://console.cloud.google.com/iam-admin/serviceaccounts
2. Find service account: `sg-transport-pipeline-v2@...`
3. Click on the service account
4. Go to "Keys" tab
5. Click "Add Key" → "Create new key"
6. Select "JSON" format
7. Click "Create"
8. **Key will download automatically** (e.g., `sg-public-transport-pipeline-abc123.json`)

**Via gcloud CLI:**
```bash
gcloud iam service-accounts keys create credentials/gcp-service-account.json \
  --iam-account=sg-transport-pipeline-v2@sg-public-transport-pipeline.iam.gserviceaccount.com
```

### Step 2: Save Credentials File

```bash
# Create credentials directory (from project root)
mkdir -p credentials

# Move downloaded key to credentials folder
# Rename it to: gcp-service-account.json
mv ~/Downloads/sg-public-transport-pipeline-*.json credentials/gcp-service-account.json

# Verify file exists
ls credentials/
# Should show: gcp-service-account.json
```

**⚠️ IMPORTANT:**
- Never commit this file to git (already in `.gitignore`)
- Keep it secure
- Don't share publicly

---

## gcloud CLI Setup

### Step 1: Install gcloud CLI

**Windows:**
1. Download installer: https://cloud.google.com/sdk/docs/install#windows
2. Run `GoogleCloudSDKInstaller.exe`
3. Follow installation wizard
4. Check "Run 'gcloud init'" at the end

**Mac:**
```bash
# Using Homebrew
brew install --cask google-cloud-sdk

# Or using direct download
curl https://sdk.cloud.google.com | bash
```

**Linux:**
```bash
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
```

### Step 2: Initialize gcloud

```bash
# Initialize gcloud
gcloud init

# Follow prompts:
# 1. Log in with your Google account
# 2. Select project: sg-public-transport-pipeline
# 3. Select default region: asia-east1
```

### Step 3: Verify Installation

```bash
# Check gcloud version
gcloud --version
# Should show: Google Cloud SDK 4xx.x.x

# Check authenticated account
gcloud auth list
# Should show your email with (active) marker

# Check current project
gcloud config get-value project
# Should show: sg-public-transport-pipeline

# Check default region
gcloud config get-value compute/region
# Should show: asia-east1
```

### Step 4: Authenticate for Application

```bash
# Set application default credentials
gcloud auth application-default login

# This will:
# 1. Open browser for authentication
# 2. Create credentials file at:
#    - Windows: %APPDATA%\gcloud\application_default_credentials.json
#    - Mac/Linux: ~/.config/gcloud/application_default_credentials.json
```

---

## Python Environment

### Step 1: Create Virtual Environment

**Using venv (built-in):**
```bash
# From project root
python -m venv .venv

# Activate environment
# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1

# Mac/Linux:
source .venv/bin/activate
```

**Using uv (faster):**
```bash
# Install uv if not already installed
pip install uv

# Create virtual environment
uv venv

# Activate
# Windows:
.\.venv\Scripts\Activate.ps1

# Mac/Linux:
source .venv/bin/activate
```

### Step 2: Install Dependencies

**Core project dependencies:**
```bash
uv sync
# Alternative: Using pip (if you don't have uv)
pip install -e .
```

**Streamlit dependencies:**
```bash
cd streamlit_app
pip install -r requirements.txt
cd ..
```

### Step 3: Verify Installation

```bash
# Check Python packages
pip list

# Should include:
# - google-cloud-bigquery
# - google-cloud-storage
# - dbt-core
# - dbt-bigquery
# - pandas
# - requests
# - streamlit
# - plotly
```

---

## Environment Variables

### Step 1: Create `.env` File

```bash
# From project root
# Copy the example file
cp .env.example .env

# Or create manually
touch .env  # Mac/Linux
New-Item .env  # Windows PowerShell
```

### Step 2: Configure Environment Variables

**Edit `.env` file:**

```bash
# GCP Configuration
GOOGLE_APPLICATION_CREDENTIALS=./credentials/gcp-service-account.json
GCP_PROJECT_ID=sg-public-transport-pipeline
GCP_REGION=asia-east1

# GCS Buckets (from terraform output)
GCS_BUCKET_RAW=sg-public-transport-data-raw
GCS_BUCKET_PROCESSED=sg-public-transport-data-processed

# BigQuery
BQ_DATASET=sg_public_transport_analytics
BQ_LOCATION=asia-east1

# LTA API (get from LTA DataMall - see next section)
LTA_ACCOUNT_KEY=YOUR_LTA_API_KEY_HERE
```

**⚠️ IMPORTANT:**
- Replace `YOUR_LTA_API_KEY_HERE` with actual LTA API key
- Verify `GCP_PROJECT_ID` matches your project
- Verify bucket names match terraform outputs

### Step 3: Configure dbt Profile

**Create dbt profiles directory:**
```bash
# Mac/Linux
mkdir -p ~/.dbt

# Windows
mkdir %USERPROFILE%\.dbt
```

**Create `~/.dbt/profiles.yml`:**

```yaml
sg_transport:
  target: dev
  outputs:
    dev:
      type: bigquery
      method: service-account
      project: sg-public-transport-pipeline  # Your project ID
      dataset: sg_public_transport_analytics
      location: asia-east1
      keyfile: /full/path/to/credentials/gcp-service-account.json  # Absolute path!
      threads: 4
      timeout_seconds: 300
      priority: interactive
      retries: 1
```

**⚠️ IMPORTANT:**
- Use **absolute path** for `keyfile`
- Windows example: `C:\Users\YourName\projects\sg_public_transport_pipeline\credentials\gcp-service-account.json`
- Mac/Linux example: `/Users/yourname/projects/sg_public_transport_pipeline/credentials/gcp-service-account.json`

### Step 4: Test dbt Connection

```bash
# Navigate to dbt project
cd sg_transport_dbt

# Test connection
dbt debug

# Should show:
# Connection test: OK connection ok
```

---

## LTA API Setup

### Step 1: Register for LTA DataMall Account

1. Go to: https://datamall.lta.gov.sg/content/datamall/en.html
2. Click "Request for API Access"
3. Fill in registration form:
   - Email address
   - Purpose: "Data analytics / learning project"
4. Verify email
5. Log in to account

### Step 2: Get API Key

1. Log in to LTA DataMall
2. Go to "My Account" or "API Access"
3. Copy your **Account Key** (API key)
4. Should look like: `abcd1234EFGH5678==`

### Step 3: Update `.env` File

```bash
# Update the LTA_ACCOUNT_KEY in .env
LTA_ACCOUNT_KEY=your_actual_key_here
```

### Step 4: Test API Access

```bash
# Test with a simple script
python -c "
import os
from dotenv import load_dotenv
import requests

load_dotenv()
api_key = os.getenv('LTA_ACCOUNT_KEY')
headers = {'AccountKey': api_key}
response = requests.get('https://datamall2.mytransport.sg/ltaodataservice/BusStops?$top=1', headers=headers)
print(f'Status: {response.status_code}')
print(f'Success!' if response.status_code == 200 else 'Failed!')
"
```

**Expected output:**
```
Status: 200
Success!
```

---

## Testing the Pipeline

### Phase 1: Test Data Extraction

```bash
# From project root
python -m src.ingestion.extract_bus_stops
python -m src.ingestion.extract_train_stations

# Check data was created
ls data/raw/
# Should show: bus_stops.json, train_stations.json
```

### Phase 2: Test Infrastructure (already done via Terraform)

```bash
# Verify resources exist
gcloud storage buckets list
gcloud bigquery datasets list
```

### Phase 3: Test GCS Upload

```bash
# Upload reference data
python scripts/upload_to_gcs.py --reference-only

# Verify in GCS
gsutil ls gs://sg-public-transport-data-raw/reference/
# Should show: bus_stops.ndjson, train_stations.ndjson
```

### Phase 4: Test BigQuery Load

```bash
# Load reference tables
python scripts/load_to_bq.py --reference

# Verify in BigQuery
bq query --use_legacy_sql=false \
  'SELECT COUNT(*) as count FROM `sg_public_transport_analytics.bus_stops`'
# Should show: 5,202 rows

bq query --use_legacy_sql=false \
  'SELECT COUNT(*) as count FROM `sg_public_transport_analytics.train_stations`'
# Should show: 213 rows
```

### Phase 5: Test dbt Transformation

```bash
# Navigate to dbt project
cd sg_transport_dbt

# Install dbt packages
dbt deps

# Run dbt models
dbt run

# Run tests
dbt test

# Expected output:
# Completed successfully
# All tests passed
```

---

## Phase 6: Docker & Airflow Setup

**Note:** Airflow orchestrates the pipeline automatically, but you can run the pipeline manually without it.

### Prerequisites

- **Docker Desktop** installed and running
  - Windows: https://docs.docker.com/desktop/install/windows-install/
  - Mac: https://docs.docker.com/desktop/install/mac-install/
  - Linux: https://docs.docker.com/desktop/install/linux-install/
- **Docker Compose** (included with Docker Desktop)
- At least 4GB RAM available for Docker

### Step 1: Verify Docker Installation

```bash
# Check Docker is installed and running
docker --version
docker-compose --version

# Test Docker works
docker run hello-world
```

**Expected output:** Docker version info and "Hello from Docker!" message

---

### Step 2: Create Airflow Environment File

Create `.env.airflow` in project root:

```bash
# Create file
# Windows PowerShell:
New-Item .env.airflow -ItemType File

# Mac/Linux:
touch .env.airflow
```

**Add these contents:**

```bash
# Airflow Web UI credentials
_AIRFLOW_WWW_USER_USERNAME=admin
_AIRFLOW_WWW_USER_PASSWORD=admin

# Airflow UID (for volume permissions)
AIRFLOW_UID=50000

# LTA API Key (copy from main .env)
LTA_ACCOUNT_KEY=YOUR_LTA_API_KEY_HERE
```

**⚠️ Important:**
- Replace `YOUR_LTA_API_KEY_HERE` with your actual LTA API key
- Change the password for production use

---

### Step 3: Build Custom Airflow Image

The project uses a custom Docker image with all dependencies pre-installed.

```bash
# From project root
docker-compose build

# This takes 5-10 minutes on first build
# Subsequent builds are faster (uses cache)
```

**What's being built:**
- Base: Apache Airflow 2.10.4 with Python 3.10
- Installed: Google Cloud libraries, dbt, project dependencies
- Configured: Volume mounts for DAGs, logs, credentials

---

### Step 4: Initialize Airflow Database

```bash
# Initialize Airflow (one-time setup)
docker-compose up airflow-init

# Wait for message: "Airflow initialized successfully"
# Then press Ctrl+C
```

**What this does:**
- Creates PostgreSQL database for Airflow metadata
- Creates admin user account
- Sets up Airflow configuration

---

### Step 5: Start Airflow Services

```bash
# Start all services in background
docker-compose up -d

# Check services are running
docker-compose ps

# Expected output: 3 services running
# - postgres (database)
# - airflow-webserver (UI on port 8080)
# - airflow-scheduler (runs DAGs)
```

**Wait 30-60 seconds** for services to fully start.

---

### Step 6: Access Airflow Web UI

1. Open browser: http://localhost:8080
2. **Login:**
   - Username: `admin`
   - Password: `admin` (or what you set in `.env.airflow`)

**You should see:**
- Airflow dashboard
- List of DAGs
- One DAG: `sg_public_transport_monthly_pipeline`

---

### Step 7: Test the Pipeline DAG

**In the Airflow UI:**

1. Find `sg_public_transport_monthly_pipeline` in the DAG list
2. Toggle the switch to **ON** (activates the DAG)
3. Click on the DAG name to open details
4. Click **"Trigger DAG"** button (play icon)
5. Optionally set configuration (or leave default for current month)
6. Click **"Trigger"**

**Monitor execution:**
- Click **"Graph"** view to see task dependencies
- Click **"Grid"** view to see run history
- Click individual tasks to view logs
- Green = success, Red = failure, Yellow = running

**Expected duration:** 20-30 minutes for full pipeline

---

### Step 8: Verify Pipeline Results

**Check BigQuery for new data:**

```bash
# Query fact table for the processed month
bq query --use_legacy_sql=false \
  'SELECT year_month, COUNT(*) as trip_count 
   FROM `sg_public_transport_analytics.fact_od_trips` 
   GROUP BY year_month 
   ORDER BY year_month DESC 
   LIMIT 5'
```

**Check Airflow logs:**

```bash
# View scheduler logs
docker-compose logs -f airflow-scheduler

# View webserver logs
docker-compose logs -f airflow-webserver

# View all logs
docker-compose logs -f
```

---

### Step 9: Understanding the DAG

**The DAG orchestrates 13 tasks in 5 groups:**

1. **Extract from LTA** (4 tasks)
   - Extract bus stops
   - Extract train stations
   - Extract bus OD (previous month)
   - Extract train OD (previous month)

2. **Upload to GCS** (2 tasks)
   - Upload reference data
   - Upload journey data

3. **Load to BigQuery** (2 tasks)
   - Load reference tables
   - Load OD tables

4. **dbt Transform** (3 tasks)
   - Install dbt packages
   - Run dbt models
   - Run dbt tests

5. **Data Quality** (1 task)
   - Validate fact table counts

**Schedule:** Monthly on the 15th at 9:00 AM UTC (after LTA releases data)

---

### Common Airflow Commands

```bash
# Start Airflow
docker-compose up -d

# Stop Airflow
docker-compose down

# Stop and remove all data (WARNING: destructive!)
docker-compose down -v

# Restart services
docker-compose restart

# Rebuild after code changes
docker-compose build --no-cache
docker-compose up -d

# View logs
docker-compose logs -f airflow-scheduler
docker-compose logs -f airflow-webserver

# Access Airflow CLI
docker-compose exec airflow-webserver bash

# Inside container, run:
airflow dags list
airflow dags test sg_public_transport_monthly_pipeline 2026-01-01
```

---

### Airflow Directory Structure

```
airflow/
├── dags/                         # DAG definitions
│   └── sg_transport_monthly_pipeline.py
├── logs/                         # Task execution logs (auto-generated)
├── config/
│   ├── profiles.yml             # dbt BigQuery connection
│   └── ALERTING.md              # Alerting setup guide
├── requirements.txt             # Python dependencies
└── README.md                    # Quick reference
```

---

### Troubleshooting Airflow

**Issue: Services won't start**

```bash
# Check Docker is running
docker ps

# Check logs for errors
docker-compose logs

# Restart Docker Desktop
# Then try: docker-compose up -d
```

---

**Issue: DAG not appearing in UI**

```bash
# Check for syntax errors
docker-compose exec airflow-webserver python -m py_compile /opt/airflow/dags/sg_transport_monthly_pipeline.py

# Check scheduler logs
docker-compose logs airflow-scheduler | grep ERROR
```

---

**Issue: Tasks failing with credential errors**

**Verify credentials are mounted:**

```bash
# Check if credentials are accessible in container
docker-compose exec airflow-webserver ls -l /opt/airflow/credentials/

# Should show: gcp-service-account.json
```

**If missing:**
- Ensure `credentials/gcp-service-account.json` exists in project root
- Check `docker-compose.yml` has correct volume mount
- Restart services: `docker-compose down && docker-compose up -d`

---

**Issue: Permission denied errors**

```bash
# Check Airflow UID in .env.airflow
cat .env.airflow | grep AIRFLOW_UID

# Should be: AIRFLOW_UID=50000

# Fix permissions (if needed)
# Linux/Mac:
sudo chown -R 50000:0 airflow/logs/

# Windows: Usually not needed
```

---

**Issue: Port 8080 already in use**

```bash
# Find what's using port 8080
# Windows:
netstat -ano | findstr :8080

# Mac/Linux:
lsof -i :8080

# Change Airflow port in docker-compose.yml:
# Find: "8080:8080"
# Change to: "8081:8080"
# Then: docker-compose up -d
# Access at: http://localhost:8081
```

---

### When to Use Airflow

**Use Airflow when:**
- ✅ You want automated monthly pipeline runs
- ✅ You need monitoring and alerting
- ✅ You want task retry and failure handling
- ✅ You need to track pipeline history
- ✅ Multiple people need to monitor the pipeline

**Skip Airflow when:**
- ⏭️ Just learning the pipeline
- ⏭️ Running pipeline manually is sufficient
- ⏭️ Docker installation issues
- ⏭️ Limited system resources (< 4GB RAM)

**Alternative:** Run pipeline steps manually (already tested in Phases 1-5)

---

### Phase 7: Test Streamlit Dashboard

```bash
# Navigate to streamlit app
cd ../streamlit_app

# Run dashboard
streamlit run app.py

# Should open browser at: http://localhost:8501
```

**Verify:**
- ✅ Dashboard loads without errors
- ✅ Year-month dropdown populated
- ✅ Charts display data
- ✅ Filters work

---

## Troubleshooting

### Issue: "Permission Denied" errors

**Cause:** Service account lacks necessary permissions

**Fix:**
```bash
# Grant necessary roles to service account
gcloud projects add-iam-policy-binding sg-public-transport-pipeline \
  --member="serviceAccount:sg-transport-pipeline-v2@sg-public-transport-pipeline.iam.gserviceaccount.com" \
  --role="roles/bigquery.admin"

gcloud projects add-iam-policy-binding sg-public-transport-pipeline \
  --member="serviceAccount:sg-transport-pipeline-v2@sg-public-transport-pipeline.iam.gserviceaccount.com" \
  --role="roles/storage.admin"
```

---

### Issue: "Credentials file not found"

**Cause:** Wrong path to credentials file

**Fix:**
```bash
# Check file exists
ls credentials/gcp-service-account.json

# Use absolute path in .env
# Windows:
GOOGLE_APPLICATION_CREDENTIALS=C:\Users\YourName\projects\sg_public_transport_pipeline\credentials\gcp-service-account.json

# Mac/Linux:
GOOGLE_APPLICATION_CREDENTIALS=/Users/yourname/projects/sg_public_transport_pipeline/credentials/gcp-service-account.json
```

---

### Issue: "LTA API returns 401 Unauthorized"

**Cause:** Invalid or missing API key

**Fix:**
1. Verify API key in LTA DataMall account
2. Check `.env` file has correct key
3. No spaces or quotes around the key
4. Key should look like: `abcd1234EFGH5678==`

---

### Issue: dbt connection fails

**Cause:** Incorrect profiles.yml configuration

**Fix:**
```bash
# Check profiles.yml location
# Mac/Linux: ~/.dbt/profiles.yml
# Windows: %USERPROFILE%\.dbt\profiles.yml

# Verify path to keyfile is absolute
# Test connection
cd sg_transport_dbt
dbt debug

# Should show all checks passing
```

---

### Issue: "Module not found" errors

**Cause:** Virtual environment not activated or dependencies not installed

**Fix:**
```bash
# Activate virtual environment
# Windows:
.\.venv\Scripts\Activate.ps1

# Mac/Linux:
source .venv/bin/activate

# Reinstall dependencies
pip install -e .
```

---

### Issue: BigQuery quota exceeded

**Cause:** Too many queries or large data scans

**Fix:**
- Wait 24 hours for quota reset
- Check BigQuery quotas in GCP Console
- Use partitioning and clustering to reduce scans
- Cache results in Streamlit (already implemented)

---

## Quick Reference

### Essential Commands

```bash
# Activate virtual environment
source .venv/bin/activate  # Mac/Linux
.\.venv\Scripts\Activate.ps1  # Windows

# Run data extraction
python -m src.ingestion.extract_bus_stops
python -m src.ingestion.extract_train_stations

# Upload to GCS
python scripts/upload_to_gcs.py --reference-only

# Load to BigQuery
python scripts/load_to_bq.py --reference

# Run dbt
cd sg_transport_dbt
dbt run
dbt test

# Run Streamlit
cd streamlit_app
streamlit run app.py
```

### Essential Files to Configure

1. **`.env`** - Environment variables (credentials, project ID, API keys)
2. **`~/.dbt/profiles.yml`** - dbt connection settings
3. **`credentials/gcp-service-account.json`** - GCP service account key

### GCP Resources

- **Console:** https://console.cloud.google.com/
- **BigQuery:** https://console.cloud.google.com/bigquery
- **GCS:** https://console.cloud.google.com/storage
- **IAM:** https://console.cloud.google.com/iam-admin

---

## Next Steps

After successful setup:

1. **Extract journey data:**
   ```bash
   python -m src.ingestion.extract_bus_od --year 2026 --month 1
   python -m src.ingestion.extract_train_od --year 2026 --month 1
   ```

2. **Run full pipeline:**
   ```bash
   python scripts/upload_to_gcs.py --year 2026 --month 1
   python scripts/load_to_bq.py --od
   cd sg_transport_dbt && dbt run && dbt test
   ```

3. **Explore dashboard:**
   ```bash
   cd streamlit_app
   streamlit run app.py
   ```

4. **Setup Airflow** (requires Docker)

---

## Support & Documentation

- **Project Documentation:** `docs/` directory
- **Architecture:** `docs/architecture.md`
- **Current Status:** `docs/current-status.md`
- **Python Conventions:** `.cursor/rules/python-conventions.md`
- **dbt Conventions:** `.cursor/rules/dbt-conventions.md`

---

## Checklist

Use this checklist to track your setup progress:

- [ ] Clone repository
- [ ] Create GCP account
- [ ] Create GCP project
- [ ] Enable required APIs
- [ ] Run terraform to create resources
- [ ] Create service account key
- [ ] Install gcloud CLI
- [ ] Authenticate gcloud
- [ ] Create Python virtual environment
- [ ] Install dependencies
- [ ] Configure `.env` file
- [ ] Configure dbt `profiles.yml`
- [ ] Register for LTA API
- [ ] Test LTA API access
- [ ] Test data extraction
- [ ] Test GCS upload
- [ ] Test BigQuery load
- [ ] Test dbt transformation
- [ ] Test Streamlit dashboard

---

**Last Updated:** April 17, 2026  
**Version:** 1.0

For questions or issues, refer to the troubleshooting section or check the project documentation in `docs/`.