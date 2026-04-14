# Singapore LTA Public Transport Analytics Pipeline

End-to-end data pipeline for analyzing Singapore's public transport demand patterns using LTA (Land Transport Authority) data.

**Data Engineering Zoomcamp 2026 - Capstone Project**

---

## Overview

This pipeline extracts train and bus journey data from Singapore's Land Transport Authority API, processes it through Google Cloud Platform (BigQuery, GCS), transforms it with dbt, and visualizes insights through an interactive Streamlit dashboard.

**Tech Stack:** Python, GCP (BigQuery, GCS), dbt, Terraform, Docker, Apache Airflow, Streamlit

---

## Features

- **Automated Data Extraction:** Monthly bus and train origin-destination (OD) data from LTA DataMall API
- **Cloud Infrastructure:** GCP resources managed with Terraform (BigQuery datasets, GCS buckets, IAM)
- **Data Transformation:** dbt models for cleaning, joining, and creating analytics-ready tables
- **Orchestration:** Apache Airflow DAGs for automated monthly pipeline execution
- **Interactive Dashboard:** Streamlit app with trip count visualizations and filters
- **Data Quality:** Built-in dbt tests and validation checks

---

## Quick Start

Choose your path:

- **Fast Setup (15 min):** [`docs/QUICKSTART.md`](docs/QUICKSTART.md) - Get dashboard running quickly
- **Full Setup (1-2 hours):** [`docs/SETUP-GUIDE.md`](docs/SETUP-GUIDE.md) - Complete step-by-step guide for new machines

### Prerequisites

- Python 3.10+
- Google Cloud account with billing enabled
- LTA DataMall API key (free registration)

### 5-Minute Demo

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/sg_public_transport_pipeline.git
cd sg_public_transport_pipeline

# Setup virtual environment
python -m venv .venv
source .venv/bin/activate  # Mac/Linux: .\.venv\Scripts\Activate.ps1 on Windows

# Install dependencies
pip install -e .

# Configure (see SETUP-GUIDE.md for details)
# 1. Create GCP project and resources (terraform apply)
# 2. Setup credentials/gcp-service-account.json
# 3. Create .env file with GCP_PROJECT_ID and LTA_ACCOUNT_KEY

# Run dashboard
cd streamlit_app
pip install -r requirements.txt
streamlit run app.py
```

---

## Project Structure

```
sg_public_transport_pipeline/
├── .cursor/rules/          # Project conventions and coding standards
├── airflow/                # Airflow DAGs and configuration
│   ├── dags/              # Pipeline orchestration DAGs
│   └── config/            # Airflow profiles.yml
├── credentials/           # GCP service account keys (git-ignored)
├── data/                  # Local data cache (git-ignored)
│   ├── raw/              # Extracted JSON files
│   └── processed/        # Transformed NDJSON files
├── docs/                  # Comprehensive documentation
│   ├── SETUP-GUIDE.md    # Complete setup instructions
│   ├── QUICKSTART.md     # Fast-track setup
│   ├── architecture.md   # System design and data flow
│   └── current-status.md # Project progress and phase details
├── scripts/               # Utility scripts
│   ├── upload_to_gcs.py  # GCS upload automation
│   └── load_to_bq.py     # BigQuery loading
├── sg_transport_dbt/      # dbt transformation project
│   ├── models/
│   │   ├── staging/      # Raw data cleaning
│   │   └── marts/        # Analytics tables
│   └── tests/            # Data quality tests
├── src/                   # Python source code
│   ├── ingestion/        # API extraction modules
│   └── upload/           # GCS upload modules
├── streamlit_app/         # Interactive dashboard
│   ├── app.py            # Main dashboard
│   ├── utils/            # BigQuery client
│   └── requirements.txt
├── terraform/             # Infrastructure as Code
│   ├── main.tf           # GCP resource definitions
│   └── variables.tf
├── .env                   # Environment variables (git-ignored)
├── docker-compose.yml     # Airflow services
├── Dockerfile             # Custom Airflow image
└── pyproject.toml         # Python project config
```

---

## Pipeline Architecture

```
LTA API → Python Extraction → GCS (Raw) → BigQuery (Staging)
    ↓                                              ↓
dbt Transformation ← BigQuery ← Data Quality Tests
    ↓
BigQuery (Marts) → Streamlit Dashboard
    ↑
Apache Airflow (Orchestration)
```

**Detailed architecture:** [`docs/architecture.md`](docs/architecture.md)

---

## Data Sources

**Singapore Land Transport Authority (LTA) DataMall:**
- Bus origin-destination (OD) journeys
- Train origin-destination (OD) journeys
- Bus stop reference data
- Train station reference data

**API Documentation:** https://datamall.lta.gov.sg/content/datamall/en/dynamic-data.html

---

## Project Phases

| Phase | Description | Status |
|-------|-------------|--------|
| Phase 1 | Data Extraction (Python) | ✅ Complete |
| Phase 2 | Infrastructure (Terraform) | ✅ Complete |
| Phase 3 | Data Upload (GCS) | ✅ Complete |
| Phase 4 | Data Loading (BigQuery) | ✅ Complete |
| Phase 5 | Transformation (dbt) | ✅ Complete |
| Phase 6 | Orchestration (Airflow) | ✅ Complete |
| Phase 7 | Visualization (Streamlit) | ✅ Complete |

**All phases complete! 🎉**

**Detailed status:** [`docs/current-status.md`](docs/current-status.md)

---

## Key Commands

### Data Extraction
```bash
# Extract reference data
python -m src.ingestion.extract_bus_stops
python -m src.ingestion.extract_train_stations

# Extract journey data (example: January 2026)
python -m src.ingestion.extract_bus_od --year 2026 --month 1
python -m src.ingestion.extract_train_od --year 2026 --month 1
```

### GCS Upload
```bash
python scripts/upload_to_gcs.py --data-type reference
python scripts/upload_to_gcs.py --data-type journeys --year 2026 --month 1
```

### BigQuery Load
```bash
python scripts/load_to_bq.py --table-type reference
python scripts/load_to_bq.py --table-type od --year 2026 --month 1
```

### dbt Transformation
```bash
cd sg_transport_dbt
dbt deps           # Install dependencies
dbt run            # Run transformations
dbt test           # Run data quality tests
dbt docs generate  # Generate documentation
dbt docs serve     # View docs at localhost:8080
```

### Streamlit Dashboard
```bash
cd streamlit_app
streamlit run app.py  # Opens at localhost:8501
```

### Airflow (Docker)
```bash
# Start Airflow
docker-compose up -d

# Access UI: http://localhost:8080
# Username: admin, Password: admin

# Stop Airflow
docker-compose down
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [`SETUP-GUIDE.md`](docs/SETUP-GUIDE.md) | Complete setup instructions for new machines |
| [`QUICKSTART.md`](docs/QUICKSTART.md) | Fast-track setup for experienced users |
| [`architecture.md`](docs/architecture.md) | System design and data flow diagrams |
| [`current-status.md`](docs/current-status.md) | Project progress and phase details |
| [`phase6-airflow-setup.md`](docs/phase6-airflow-setup.md) | Airflow orchestration guide |
| [`phase7-streamlit-setup.md`](docs/phase7-streamlit-setup.md) | Dashboard setup and features |
| [`QUICKREF-phase6.md`](docs/QUICKREF-phase6.md) | Airflow command reference |
| [`QUICKREF-phase7.md`](docs/QUICKREF-phase7.md) | Dashboard command reference |

---

## Requirements

### Python Dependencies
```
google-cloud-storage==2.18.2
google-cloud-bigquery==3.28.0
dbt-core==1.9.0
dbt-bigquery==1.9.0
requests==2.32.3
pandas==2.2.3
streamlit==1.41.1
plotly==5.24.1
python-dotenv==1.0.1
```

### GCP Resources
- **BigQuery:** 1 dataset with staging and marts tables
- **Cloud Storage:** 2 buckets (raw + processed)
- **IAM:** Service account with BigQuery Admin and Storage Admin roles

### API Access
- **LTA DataMall:** Free account with API key

---

## Environment Variables

Required in `.env` file:

```bash
# GCP Configuration
GOOGLE_APPLICATION_CREDENTIALS=./credentials/gcp-service-account.json
GCP_PROJECT_ID=your-project-id
GCP_REGION=asia-east1

# GCS Buckets
GCS_BUCKET_RAW=your-bucket-raw
GCS_BUCKET_PROCESSED=your-bucket-processed

# BigQuery
BQ_DATASET=sg_public_transport_analytics
BQ_LOCATION=asia-east1

# LTA API
LTA_ACCOUNT_KEY=your-lta-api-key
```

See [`SETUP-GUIDE.md`](docs/SETUP-GUIDE.md) for detailed configuration steps.

---

## Testing

```bash
# Test API extraction
python -m src.ingestion.extract_bus_stops

# Test GCS upload
python scripts/upload_to_gcs.py --data-type reference

# Test BigQuery load
python scripts/load_to_bq.py --table-type reference

# Test dbt
cd sg_transport_dbt
dbt debug  # Test connection
dbt run --select stg_bus_stops  # Test single model
dbt test   # Run all tests

# Test Streamlit
cd streamlit_app
streamlit run app.py
```

---

## Troubleshooting

### Common Issues

**1. Credentials not found**
```bash
# Use absolute path in .env
export GOOGLE_APPLICATION_CREDENTIALS="/full/path/to/credentials/gcp-service-account.json"
```

**2. BigQuery permission denied**
```bash
# Grant roles to service account
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:YOUR_SERVICE_ACCOUNT@YOUR_PROJECT.iam.gserviceaccount.com" \
  --role="roles/bigquery.admin"
```

**3. LTA API 401 error**
- Verify API key in `.env`
- Check key is active in LTA DataMall account
- Ensure no extra spaces/quotes in `.env`

**4. dbt connection fails**
- Check `~/.dbt/profiles.yml` has absolute path to keyfile
- Run `dbt debug` to diagnose
- Verify service account has BigQuery permissions

**Full troubleshooting guide:** [`SETUP-GUIDE.md#troubleshooting`](docs/SETUP-GUIDE.md#troubleshooting)

---

## Performance

- **Data Extraction:** ~10-15 min per month (bus + train)
- **GCS Upload:** ~1-2 min per month
- **BigQuery Load:** ~2-3 min per month
- **dbt Transformation:** ~3-5 min full run
- **Airflow DAG:** ~20-30 min end-to-end
- **Streamlit Dashboard:** <2 sec load time (with caching)

---

## Cost Estimates (GCP)

**Monthly costs for 12 months of data:**
- BigQuery storage: ~$0.02/GB/month (~$0.10-0.50)
- BigQuery queries: First 1TB free (~$5/TB after)
- GCS storage: $0.020/GB/month (~$0.10-0.50)
- **Total: <$5/month for learning/testing**

**Note:** GCP free tier includes $300 credits for 90 days.

---

## Contributing

This is a personal capstone project, but feedback and suggestions are welcome!

1. Fork the repository
2. Create a feature branch
3. Follow existing code conventions (see `.cursor/rules/`)
4. Test changes locally
5. Submit a pull request

---

## License

This project is for educational purposes as part of the Data Engineering Zoomcamp 2026.

---

## Acknowledgments

- **Data Engineering Zoomcamp 2026** - Course structure and guidance
- **Singapore LTA** - Public transport data via DataMall API
- **DataTalks.Club** - Data engineering community

---

## Contact

For questions or collaboration:
- GitHub Issues: [Create an issue](https://github.com/YOUR_USERNAME/sg_public_transport_pipeline/issues)
- Project Author: [Your Name]
- Course: [Data Engineering Zoomcamp 2026](https://github.com/DataTalksClub/data-engineering-zoomcamp)

---

**Status:** All phases complete ✅  
**Last Updated:** 2026-03-31  
**Version:** 1.0
