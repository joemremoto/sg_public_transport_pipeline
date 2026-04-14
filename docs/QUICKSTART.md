# Quick Start Guide - 15 Minutes to Running Dashboard

Fast-track setup for experienced developers. For detailed instructions, see `SETUP-GUIDE.md`.

---

## Prerequisites

- Git, Python 3.10+, pip
- Google account
- GCP account with billing enabled

---

## 1. Clone & Setup (2 min)

```bash
# Clone repo
git clone https://github.com/YOUR_USERNAME/sg_public_transport_pipeline.git
cd sg_public_transport_pipeline

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Mac/Linux
.\.venv\Scripts\Activate.ps1  # Windows

# Install dependencies
pip install -e .
```

---

## 2. GCP Setup (5 min)

```bash
# Install gcloud CLI (if not installed)
# https://cloud.google.com/sdk/docs/install

# Login and create project
gcloud auth login
gcloud projects create sg-public-transport-pipeline
gcloud config set project sg-public-transport-pipeline

# Enable APIs
gcloud services enable bigquery.googleapis.com storage.googleapis.com

# Create resources with Terraform
cd terraform
terraform init
terraform apply  # Type 'yes'
cd ..

# Create service account key
gcloud iam service-accounts keys create credentials/gcp-service-account.json \
  --iam-account=sg-transport-pipeline-v2@sg-public-transport-pipeline.iam.gserviceaccount.com
```

---

## 3. Configuration (3 min)

**Create `.env` file:**
```bash
cat > .env << EOF
GOOGLE_APPLICATION_CREDENTIALS=./credentials/gcp-service-account.json
GCP_PROJECT_ID=sg-public-transport-pipeline
GCP_REGION=asia-east1
GCS_BUCKET_RAW=sg-public-transport-data-raw
GCS_BUCKET_PROCESSED=sg-public-transport-data-processed
BQ_DATASET=sg_public_transport_analytics
BQ_LOCATION=asia-east1
LTA_ACCOUNT_KEY=GET_FROM_LTA_DATAMALL
EOF
```

**Get LTA API Key:**
1. Register: https://datamall.lta.gov.sg/
2. Copy API key
3. Update `LTA_ACCOUNT_KEY` in `.env`

**Configure dbt:**
```bash
mkdir -p ~/.dbt
cat > ~/.dbt/profiles.yml << EOF
sg_transport:
  target: dev
  outputs:
    dev:
      type: bigquery
      method: service-account
      project: sg-public-transport-pipeline
      dataset: sg_public_transport_analytics
      location: asia-east1
      keyfile: $(pwd)/credentials/gcp-service-account.json
      threads: 4
      timeout_seconds: 300
EOF
```

---

## 4. Test Pipeline (5 min)

```bash
# Extract sample data
python -m src.ingestion.extract_bus_stops
python -m src.ingestion.extract_train_stations

# Upload to GCS
python scripts/upload_to_gcs.py --data-type reference

# Load to BigQuery
python scripts/load_to_bq.py --table-type reference

# Run dbt (requires journey data - skip for now)
cd sg_transport_dbt
dbt deps
# dbt run  # Skip - no journey data yet
cd ..

# Run Streamlit dashboard
cd streamlit_app
pip install -r requirements.txt
streamlit run app.py
```

**Dashboard opens at:** http://localhost:8501

---

## 5. Next Steps

**Load journey data:**
```bash
# Extract January 2026 data (takes 10-15 min)
python -m src.ingestion.extract_bus_od --year 2026 --month 1
python -m src.ingestion.extract_train_od --year 2026 --month 1

# Upload and load
python scripts/upload_to_gcs.py --data-type journeys --year 2026 --month 1
python scripts/load_to_bq.py --table-type od --year 2026 --month 1

# Transform with dbt
cd sg_transport_dbt
dbt run
dbt test
```

**View dashboard with full data:**
```bash
cd streamlit_app
streamlit run app.py
```

---

## Troubleshooting

**Credentials not found:**
```bash
# Use absolute path in .env
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/credentials/gcp-service-account.json"
```

**Permission denied:**
```bash
# Grant roles to service account
gcloud projects add-iam-policy-binding sg-public-transport-pipeline \
  --member="serviceAccount:sg-transport-pipeline-v2@sg-public-transport-pipeline.iam.gserviceaccount.com" \
  --role="roles/bigquery.admin"

gcloud projects add-iam-policy-binding sg-public-transport-pipeline \
  --member="serviceAccount:sg-transport-pipeline-v2@sg-public-transport-pipeline.iam.gserviceaccount.com" \
  --role="roles/storage.admin"
```

**Module not found:**
```bash
# Ensure virtual environment is activated
source .venv/bin/activate  # Mac/Linux
.\.venv\Scripts\Activate.ps1  # Windows

# Reinstall
pip install -e .
```

---

## Key Files

- **`.env`** - Environment variables
- **`~/.dbt/profiles.yml`** - dbt configuration
- **`credentials/gcp-service-account.json`** - GCP credentials (never commit!)
- **`docs/SETUP-GUIDE.md`** - Full detailed guide

---

## Resources

- Full Setup Guide: `docs/SETUP-GUIDE.md`
- Architecture: `docs/architecture.md`
- Project Rules: `.cursor/rules/project-core.md`
- GCP Console: https://console.cloud.google.com/
- LTA DataMall: https://datamall.lta.gov.sg/

---

**Total Time:** ~15 minutes (plus data extraction time)  
**Result:** Working Streamlit dashboard connected to your GCP project
