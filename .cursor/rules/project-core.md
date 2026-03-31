---
description: Essential project context and current phase status
---

# Singapore LTA Public Transport Analytics Pipeline

## Project Identity

**Name:** Singapore Public Transport Analytics Pipeline  
**Data Source:** Singapore Land Transport Authority (LTA) DataMall API  
**Objective:** End-to-end batch data pipeline analyzing bus and train passenger demand patterns  
**Learning Focus:** Production-grade pipeline with detailed documentation for learning

## Current Status

**Phase 5: Complete** ✅ - dbt transformation (star schema with 19.3M records)  
**Phase 6: Next** ⏳ - Airflow orchestration

See `docs/current-status.md` for detailed phase history.

---

## Technology Stack

- **Orchestration:** Apache Airflow
- **Storage:** Google Cloud Storage (GCS)
- **Warehouse:** BigQuery
- **Transformation:** dbt
- **Visualization:** Streamlit (planned)
- **Infrastructure:** Terraform (IaC)
- **Language:** Python with uv package manager
- **Version Control:** Git/GitHub

---

## Data Model (Star Schema)

### Fact Tables
- `fact_bus_journeys` - Bus OD trips (~17.6M rows)
- `fact_train_journeys` - Train OD trips (~1.7M rows)

### Dimension Tables
- `dim_bus_stops` - Bus stop reference (~5.2k rows)
- `dim_train_stations` - Train station reference (~213 rows)
- `dim_date` - Date dimension (~1.1k rows, 2025-2027)
- `dim_time_period` - Hour categories (24 rows)

**Grain:** One fact row per origin-destination-hour-daytype combination

**Keys:** Hash-based surrogate keys for dimensions, referential integrity enforced

See `docs/architecture.md` for full schema details.

---

## Key Technical Decisions

### Data Flow Architecture
```
LTA API → Python Scripts → GCS (raw) → BigQuery (raw tables) → 
dbt (transform) → BigQuery (star schema) → Streamlit (viz)
```

### What's Included
- Batch processing (monthly updates)
- Separate fact tables by mode (bus/train)
- Hourly granularity (0-23 hour periods)
- Weekday vs Weekend/Holiday segmentation
- Geospatial data (lat/lon for stops/stations)

### What's Excluded
- ❌ Real-time streaming (LTA provides monthly batch data)
- ❌ Multi-modal transfer analysis (data doesn't support it)
- ❌ Individual trip-level data (LTA provides pre-aggregated counts)

**Rationale:** LTA API provides pre-aggregated monthly OD counts, not individual transactions. Batch processing aligns with data release schedule.

---

## Project Structure

```
project/
├── .cursor/rules/              # Project rules
├── docs/                       # Documentation
├── terraform/                  # Infrastructure as Code
├── src/
│   ├── config/                # Centralized settings
│   ├── ingestion/             # LTA API extraction
│   ├── upload/                # GCS uploader
│   └── load/                  # BigQuery loader
├── scripts/                   # CLI tools
├── sg_transport_dbt/          # dbt project (star schema)
├── data/raw/                  # Local storage (git-ignored)
│   ├── bus/                   # Bus OD CSVs
│   ├── train/                 # Train OD CSVs
│   ├── bus_stops.json         # Reference data
│   └── train_stations.json    # Reference data
└── credentials/               # GCP keys (git-ignored)
```

---

## GCP Resources (Provisioned)

**Project:** `sg-public-transport-pipeline`  
**Region:** `asia-east1`

- GCS Bucket: `sg-public-transport-data-raw`
  - `reference/*.ndjson` - Reference data
  - `journeys/{mode}/{year}/{month}/*.csv` - OD data
- GCS Bucket: `sg-public-transport-data-processed`
- BigQuery Dataset: `sg_public_transport_analytics`
  - Raw tables: bus_stops, train_stations, bus_od, train_od
  - dbt models: 10 models (staging, dimensions, facts)
- Service Account: `sg-transport-pipeline-v2@...`

---

## Development Workflow

### User Executes Commands
- Assistant suggests commands but does not run them
- User shares terminal output when needed for debugging
- No hand-holding unless requested

### File Operations
- Always read files before editing
- Check linter errors after substantial edits
- Create files in logical groups when appropriate

### Communication Style
- Direct and concise - no fluff
- No unnecessary praise or validation
- No emoji unless explicitly requested
- Focus on technical accuracy and actionable information
- Avoid superlatives and excessive enthusiasm

---

## Environment Configuration

See `.env` file (git-ignored):
```
LTA_ACCOUNT_KEY=<your_key>
GOOGLE_APPLICATION_CREDENTIALS=./credentials/gcp-service-account.json
GCP_PROJECT_ID=sg-public-transport-pipeline
GCS_BUCKET_RAW=sg-public-transport-data-raw
BQ_DATASET=sg_public_transport_analytics
GCP_REGION=asia-east1
```

---

## Reference Documentation

- **Architecture & Data Model:** `docs/architecture.md`
- **LTA API Reference:** `docs/api-reference.md`
- **Python Conventions:** `.cursor/rules/python-conventions.md`
- **dbt Conventions:** `.cursor/rules/dbt-conventions.md`
- **Setup Guide:** `docs/setup-guide.md`
- **Beginner Resources:** `docs/beginner-guide.md`
- **Current Status:** `docs/current-status.md`
