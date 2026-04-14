# Setup Checklist - New Machine

Use this checklist to track your progress when setting up the project on a new machine.

**Date Started:** ___________  
**Machine:** ___________  
**Setup By:** ___________

---

## Pre-Setup Requirements

### Software Installation

- [ ] Git installed and configured
  ```bash
  git --version
  git config --global user.name "Your Name"
  git config --global user.email "your.email@example.com"
  ```

- [ ] Python 3.10+ installed
  ```bash
  python --version
  ```

- [ ] pip updated
  ```bash
  python -m pip install --upgrade pip
  ```

- [ ] Code editor installed (VS Code, Cursor, PyCharm, etc.)

### Account Setup

- [ ] Google account created/available
- [ ] LTA DataMall account created
- [ ] LTA API key obtained
- [ ] GCP account created
- [ ] GCP billing enabled

---

## Repository Setup

- [ ] Repository cloned
  ```bash
  git clone https://github.com/YOUR_USERNAME/sg_public_transport_pipeline.git
  cd sg_public_transport_pipeline
  ```

- [ ] Virtual environment created
  ```bash
  python -m venv .venv
  ```

- [ ] Virtual environment activated
  ```bash
  # Windows PowerShell:
  .\.venv\Scripts\Activate.ps1
  
  # Mac/Linux:
  source .venv/bin/activate
  ```

- [ ] Core dependencies installed
  ```bash
  pip install -e .
  ```

- [ ] dbt dependencies installed
  ```bash
  pip install dbt-core==1.9.0 dbt-bigquery==1.9.0
  ```

- [ ] Streamlit dependencies installed
  ```bash
  cd streamlit_app
  pip install -r requirements.txt
  cd ..
  ```

---

## GCP Setup

### gcloud CLI

- [ ] gcloud CLI downloaded and installed
  - Windows: https://cloud.google.com/sdk/docs/install#windows
  - Mac: `brew install --cask google-cloud-sdk`
  - Linux: `curl https://sdk.cloud.google.com | bash`

- [ ] gcloud initialized
  ```bash
  gcloud init
  ```

- [ ] Authenticated with Google account
  ```bash
  gcloud auth login
  ```

- [ ] Application default credentials set
  ```bash
  gcloud auth application-default login
  ```

- [ ] gcloud version verified
  ```bash
  gcloud --version
  ```

### GCP Project

- [ ] GCP project created
  ```bash
  gcloud projects create sg-public-transport-pipeline
  ```
  **Project ID:** ___________________________

- [ ] Default project set
  ```bash
  gcloud config set project sg-public-transport-pipeline
  ```

- [ ] Billing account linked
  ```bash
  gcloud beta billing projects link sg-public-transport-pipeline \
    --billing-account=YOUR-BILLING-ACCOUNT-ID
  ```

- [ ] Required APIs enabled
  ```bash
  gcloud services enable bigquery.googleapis.com
  gcloud services enable storage.googleapis.com
  gcloud services enable cloudresourcemanager.googleapis.com
  gcloud services enable iam.googleapis.com
  ```

### Terraform Resources

- [ ] Terraform initialized
  ```bash
  cd terraform
  terraform init
  ```

- [ ] Terraform plan reviewed
  ```bash
  terraform plan
  ```

- [ ] Terraform applied successfully
  ```bash
  terraform apply
  ```

- [ ] Terraform outputs recorded:
  - **BigQuery Dataset:** ___________________________
  - **GCS Bucket (Raw):** ___________________________
  - **GCS Bucket (Processed):** ___________________________
  - **Service Account Email:** ___________________________

### Service Account & Credentials

- [ ] Service account key created
  ```bash
  gcloud iam service-accounts keys create credentials/gcp-service-account.json \
    --iam-account=sg-transport-pipeline-v2@sg-public-transport-pipeline.iam.gserviceaccount.com
  ```

- [ ] Credentials file exists at `credentials/gcp-service-account.json`
  ```bash
  ls credentials/gcp-service-account.json
  ```

- [ ] Service account has required roles:
  - [ ] BigQuery Admin
  - [ ] Storage Admin
  
  ```bash
  gcloud projects add-iam-policy-binding sg-public-transport-pipeline \
    --member="serviceAccount:sg-transport-pipeline-v2@sg-public-transport-pipeline.iam.gserviceaccount.com" \
    --role="roles/bigquery.admin"
  
  gcloud projects add-iam-policy-binding sg-public-transport-pipeline \
    --member="serviceAccount:sg-transport-pipeline-v2@sg-public-transport-pipeline.iam.gserviceaccount.com" \
    --role="roles/storage.admin"
  ```

---

## Configuration Files

### `.env` File

- [ ] `.env` file created in project root
- [ ] All required variables set:

```bash
# GCP Configuration
GOOGLE_APPLICATION_CREDENTIALS=./credentials/gcp-service-account.json
GCP_PROJECT_ID=sg-public-transport-pipeline  # Your project ID
GCP_REGION=asia-east1

# GCS Buckets (from terraform output)
GCS_BUCKET_RAW=sg-public-transport-data-raw
GCS_BUCKET_PROCESSED=sg-public-transport-data-processed

# BigQuery
BQ_DATASET=sg_public_transport_analytics
BQ_LOCATION=asia-east1

# LTA API
LTA_ACCOUNT_KEY=YOUR_LTA_API_KEY_HERE  # Replace with actual key
```

- [ ] LTA_ACCOUNT_KEY updated with real API key

### dbt `profiles.yml`

- [ ] dbt profiles directory created
  ```bash
  # Mac/Linux:
  mkdir -p ~/.dbt
  
  # Windows:
  mkdir %USERPROFILE%\.dbt
  ```

- [ ] `profiles.yml` created at `~/.dbt/profiles.yml`
- [ ] Absolute path to keyfile set correctly

```yaml
sg_transport:
  target: dev
  outputs:
    dev:
      type: bigquery
      method: service-account
      project: sg-public-transport-pipeline
      dataset: sg_public_transport_analytics
      location: asia-east1
      keyfile: /ABSOLUTE/PATH/TO/credentials/gcp-service-account.json  # UPDATE THIS!
      threads: 4
      timeout_seconds: 300
      priority: interactive
      retries: 1
```

**Absolute keyfile path:** ___________________________

---

## Testing & Validation

### API Access Test

- [ ] LTA API test successful
  ```bash
  python -c "
  import os
  from dotenv import load_dotenv
  import requests
  
  load_dotenv()
  api_key = os.getenv('LTA_ACCOUNT_KEY')
  headers = {'AccountKey': api_key}
  response = requests.get('http://datamall2.mytransport.sg/ltaodataservice/BusStops?$top=1', headers=headers)
  print(f'Status: {response.status_code}')
  print('Success!' if response.status_code == 200 else 'Failed!')
  "
  ```
  **Expected:** Status 200, Success!

### Data Extraction Test

- [ ] Bus stops extracted
  ```bash
  python -m src.ingestion.extract_bus_stops
  ```
  **Expected:** `data/raw/bus_stops.json` created with 5,202 stops

- [ ] Train stations extracted
  ```bash
  python -m src.ingestion.extract_train_stations
  ```
  **Expected:** `data/raw/train_stations.json` created with 213 stations

### GCP Resources Test

- [ ] GCS buckets visible
  ```bash
  gcloud storage buckets list
  ```
  **Expected:** Both raw and processed buckets listed

- [ ] BigQuery dataset visible
  ```bash
  bq ls
  ```
  **Expected:** `sg_public_transport_analytics` dataset listed

### GCS Upload Test

- [ ] Reference data uploaded to GCS
  ```bash
  python scripts/upload_to_gcs.py --data-type reference
  ```

- [ ] Files visible in GCS bucket
  ```bash
  gsutil ls gs://sg-public-transport-data-raw/reference/
  ```
  **Expected:** `bus_stops.ndjson`, `train_stations.ndjson`

### BigQuery Load Test

- [ ] Reference tables loaded
  ```bash
  python scripts/load_to_bq.py --table-type reference
  ```

- [ ] Bus stops table has data
  ```bash
  bq query --use_legacy_sql=false \
    'SELECT COUNT(*) as count FROM `sg_public_transport_analytics.bus_stops`'
  ```
  **Expected:** 5,202 rows

- [ ] Train stations table has data
  ```bash
  bq query --use_legacy_sql=false \
    'SELECT COUNT(*) as count FROM `sg_public_transport_analytics.train_stations`'
  ```
  **Expected:** 213 rows

### dbt Test

- [ ] dbt connection successful
  ```bash
  cd sg_transport_dbt
  dbt debug
  ```
  **Expected:** All checks pass, connection OK

- [ ] dbt packages installed
  ```bash
  dbt deps
  ```

- [ ] dbt models can be parsed
  ```bash
  dbt parse
  ```

### Streamlit Test

- [ ] Streamlit dependencies installed
  ```bash
  cd streamlit_app
  pip install -r requirements.txt
  ```

- [ ] Streamlit app runs
  ```bash
  streamlit run app.py
  ```
  **Expected:** Browser opens at http://localhost:8501

- [ ] Dashboard loads without errors
- [ ] BigQuery connection successful
- [ ] Filters populate (if journey data exists)

---

## Full Pipeline Test (Optional)

Only if you want to test with real journey data:

### Extract Journey Data

- [ ] Bus OD data extracted (takes ~10 min)
  ```bash
  python -m src.ingestion.extract_bus_od --year 2026 --month 1
  ```
  **Expected:** `data/raw/bus_od_2026_01.json` created

- [ ] Train OD data extracted (takes ~5 min)
  ```bash
  python -m src.ingestion.extract_train_od --year 2026 --month 1
  ```
  **Expected:** `data/raw/train_od_2026_01.json` created

### Upload Journey Data

- [ ] Journey data uploaded to GCS
  ```bash
  python scripts/upload_to_gcs.py --data-type journeys --year 2026 --month 1
  ```

### Load Journey Data

- [ ] Journey tables loaded to BigQuery
  ```bash
  python scripts/load_to_bq.py --table-type od --year 2026 --month 1
  ```

### Run dbt Transformation

- [ ] dbt models run successfully
  ```bash
  cd sg_transport_dbt
  dbt run
  ```
  **Expected:** All models complete successfully

- [ ] dbt tests pass
  ```bash
  dbt test
  ```
  **Expected:** All tests pass

### Verify Dashboard with Data

- [ ] Streamlit dashboard shows January 2026 data
  ```bash
  cd streamlit_app
  streamlit run app.py
  ```

- [ ] Filters work correctly:
  - [ ] Year-month dropdown shows "2026-01"
  - [ ] Day type filter works (Weekday/Weekend)
  - [ ] Origin filter works
  - [ ] Mode selector works (Train/Bus)

- [ ] Visualizations display:
  - [ ] Trip count by origin chart shows data
  - [ ] Trip count by time period chart shows data

---

## Optional: Airflow Setup (Docker Required)

Only if you want to test Airflow orchestration:

- [ ] Docker installed
- [ ] Docker Compose installed
- [ ] Airflow environment file configured (`.env.airflow`)
- [ ] Airflow services started
  ```bash
  docker-compose up -d
  ```
- [ ] Airflow UI accessible at http://localhost:8080
- [ ] DAG visible and can be triggered

---

## Common Issues & Solutions

### Issue: "Module not found" error

**Solution:**
```bash
# Ensure virtual environment is activated
source .venv/bin/activate  # Mac/Linux
.\.venv\Scripts\Activate.ps1  # Windows

# Reinstall dependencies
pip install -e .
```

### Issue: "Credentials file not found"

**Solution:**
```bash
# Check file exists
ls credentials/gcp-service-account.json

# Use absolute path in .env
# Mac/Linux:
GOOGLE_APPLICATION_CREDENTIALS=/full/path/to/sg_public_transport_pipeline/credentials/gcp-service-account.json

# Windows:
GOOGLE_APPLICATION_CREDENTIALS=C:\Users\YourName\projects\sg_public_transport_pipeline\credentials\gcp-service-account.json
```

### Issue: "Permission denied" from GCP

**Solution:**
```bash
# Grant required roles
gcloud projects add-iam-policy-binding sg-public-transport-pipeline \
  --member="serviceAccount:sg-transport-pipeline-v2@sg-public-transport-pipeline.iam.gserviceaccount.com" \
  --role="roles/bigquery.admin"

gcloud projects add-iam-policy-binding sg-public-transport-pipeline \
  --member="serviceAccount:sg-transport-pipeline-v2@sg-public-transport-pipeline.iam.gserviceaccount.com" \
  --role="roles/storage.admin"
```

### Issue: "LTA API returns 401"

**Solution:**
- Verify API key in LTA DataMall account
- Check `.env` has correct key (no extra spaces/quotes)
- Ensure LTA account is active

### Issue: "dbt connection failed"

**Solution:**
```bash
# Check profiles.yml has absolute path to keyfile
cat ~/.dbt/profiles.yml  # Mac/Linux
type %USERPROFILE%\.dbt\profiles.yml  # Windows

# Test connection
cd sg_transport_dbt
dbt debug
```

---

## Final Verification

- [ ] All tests passed
- [ ] Dashboard runs locally
- [ ] Journey data can be extracted and loaded
- [ ] dbt transformations work
- [ ] Documentation reviewed

---

## Setup Complete! 🎉

**Setup completed on:** ___________  
**Total time taken:** ___________ hours

### Next Steps

1. **Extract more data:**
   ```bash
   python -m src.ingestion.extract_bus_od --year 2026 --month 2
   python -m src.ingestion.extract_train_od --year 2026 --month 2
   ```

2. **Run full pipeline:**
   ```bash
   python scripts/upload_to_gcs.py --data-type journeys --year 2026 --month 2
   python scripts/load_to_bq.py --table-type od --year 2026 --month 2
   cd sg_transport_dbt && dbt run && dbt test
   ```

3. **Explore dashboard:**
   ```bash
   cd streamlit_app
   streamlit run app.py
   ```

4. **Set up Airflow (optional):**
   - See `docs/phase6-airflow-setup.md`

---

## Resources

- **Full Setup Guide:** `docs/SETUP-GUIDE.md`
- **Quick Start:** `docs/QUICKSTART.md`
- **Architecture:** `docs/architecture.md`
- **Current Status:** `docs/current-status.md`
- **Troubleshooting:** `docs/SETUP-GUIDE.md#troubleshooting`

---

**Notes:**

(Use this space for any setup-specific notes, issues encountered, or reminders)

___________________________________________
___________________________________________
___________________________________________
___________________________________________
___________________________________________
