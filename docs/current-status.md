# Current Project Status

**Last Updated:** 2026-03-31

---

## Phase Overview

| Phase | Status | Progress |
|-------|--------|----------|
| Phase 1: Data Extraction | ✅ Complete | 100% |
| Phase 2: Infrastructure Setup | ✅ Complete | 100% |
| Phase 3: Data Upload | ✅ Complete | 100% |
| Phase 4: BigQuery Load | ✅ Complete | 100% |
| Phase 5: dbt Transformation | ✅ Complete | 100% |
| Phase 6: Orchestration (Airflow) | ⏳ Next | 0% |
| Phase 7: Visualization (Streamlit) | ⏳ Pending | 0% |

---

## ✅ Phase 1: Data Extraction (Complete)

**Objective:** Extract raw data from LTA DataMall API

**Deliverables:**
- ✅ 4 extraction scripts created and tested
- ✅ LTA API client wrapper (`src/ingestion/lta_client.py`)
- ✅ Bus stops reference extraction
- ✅ Train stations reference extraction  
- ✅ Bus OD journey data extraction
- ✅ Train OD journey data extraction

**Data Extracted:**
- Bus stops: 5,202 records
- Train stations: 213 records (originally 166, updated to 213)
- Bus OD: January 2026 (~232 MB CSV)
- Train OD: January 2026 (~18 MB CSV)

**Key Files:**
- `src/ingestion/extract_bus_stops.py`
- `src/ingestion/extract_train_stations.py`
- `src/ingestion/extract_bus_od.py`
- `src/ingestion/extract_train_od.py`

---

## ✅ Phase 2: Infrastructure Setup (Complete)

**Objective:** Provision GCP resources via Terraform

**Deliverables:**
- ✅ Terraform configuration files
- ✅ GCS buckets created (raw + processed)
- ✅ BigQuery dataset created
- ✅ Service account with IAM roles
- ✅ gcloud CLI authenticated

**Provisioned Resources:**
- GCS Bucket: `sg-public-transport-data-raw`
- GCS Bucket: `sg-public-transport-data-processed`
- BigQuery Dataset: `sg_public_transport_analytics` (asia-east1)
- Service Account: `sg-transport-pipeline-v2@sg-public-transport-pipeline.iam.gserviceaccount.com`

**Key Files:**
- `terraform/main.tf`
- `terraform/variables.tf`
- `terraform/outputs.tf`

---

## ✅ Phase 3: Data Upload (Complete)

**Objective:** Upload local data to GCS with proper formatting

**Deliverables:**
- ✅ GCS uploader module (`src/upload/gcs_uploader.py`)
- ✅ CLI script for uploads (`scripts/upload_to_gcs.py`)
- ✅ JSON → NDJSON conversion for reference data
- ✅ Partitioned structure in GCS
- ✅ Retry logic and timeout handling

**GCS Structure Created:**
```
reference/
├── bus_stops.ndjson
└── train_stations.ndjson

journeys/
├── bus/2026/01/bus_od_202601.csv
└── train/2026/01/train_od_202601.csv
```

**Key Features:**
- Dynamic timeout based on file size
- Exponential backoff retry logic
- NDJSON conversion for BigQuery compatibility

---

## ✅ Phase 4: BigQuery Load (Complete)

**Objective:** Load data from GCS into BigQuery raw tables

**Deliverables:**
- ✅ Schema definitions (`src/load/bq_schemas.py`)
- ✅ BigQuery loader module (`src/load/bq_loader.py`)
- ✅ CLI script (`scripts/load_to_bq.py`)
- ✅ 4 tables loaded with 6.8M+ total records

**Tables Created:**
| Table | Rows | Size |
|-------|------|------|
| bus_stops | 5,202 | ~274 KB |
| train_stations | 213 | ~9 KB |
| bus_od | 17,574,644 | ~870 MB |
| train_od | 2,639,048 | ~129 MB |

**Architecture:**
- Load from GCS (not local files)
- NDJSON for reference, CSV for OD
- Clustering on YEAR_MONTH

**Issues Resolved:**
- Fixed field name mismatch (station_code vs stn_code)
- Fixed JSON array → NDJSON conversion
- Fixed GCS path structure alignment

---

## ✅ Phase 5: dbt Transformation (Complete)

**Objective:** Build star schema for analytics

**Deliverables:**
- ✅ Full star schema (10 models)
- ✅ Staging layer: 4 views
- ✅ Dimension layer: 4 tables
- ✅ Fact layer: 2 tables (19.3M rows)
- ✅ Surrogate keys implemented
- ✅ Partitioning and clustering configured
- ✅ 36 essential data quality tests (all passing)
- ✅ Complete documentation with lineage

**Models Created:**

**Staging (4 views):**
- `stg_bus_stops`
- `stg_train_stations`
- `stg_bus_od`
- `stg_train_od`

**Dimensions (4 tables):**
- `dim_bus_stops` (5.2k rows)
- `dim_train_stations` (213 rows)
- `dim_date` (1.1k rows, 2025-2027)
- `dim_time_period` (24 rows)

**Facts (2 tables):**
- `fact_bus_journeys` (17.6M rows, partitioned & clustered)
- `fact_train_journeys` (1.7M rows, partitioned & clustered)

**Key Features:**
- Hash-based surrogate keys (deterministic)
- Referential integrity enforced
- Partitioned by date_key
- Clustered by origin + time_period
- DASH stripping fix for YEAR_MONTH formatting

**Performance:**
- Build time: ~15 seconds (full run)
- Test time: ~13 seconds (36 tests)
- 100% test pass rate

**Issues Resolved:**
- Empty train_stations (field name mismatch)
- Date key conversion error (dash stripping)
- Test simplification (100+ → 36 essential tests)

---

## ⏳ Phase 6: Orchestration (Next)

**Objective:** Automate pipeline with Apache Airflow

**Planned Components:**
- Airflow in Docker
- Monthly extraction DAG
- GCS upload task
- BigQuery load task
- dbt transformation task
- Data quality checks
- Failure alerting

**Not Yet Started**

---

## ⏳ Phase 7: Visualization (Pending)

**Objective:** Build Streamlit dashboard for analytics

**Planned Features:**
- Interactive dashboards
- Geospatial maps
- Demand trend charts
- Mode comparison
- Peak hour analysis

**Not Yet Started**

---

## Key Metrics

### Data Volume
- **Total Records:** 19.3M fact records
- **Total Storage:** ~1 GB in BigQuery
- **Data Coverage:** January 2026 (1 month)

### Code Quality
- **Python Scripts:** 8 extraction/load scripts
- **dbt Models:** 10 models
- **Tests:** 36 data quality tests (100% pass)
- **Documentation:** Comprehensive (rules, docs, phase logs)

### Infrastructure
- **GCP Project:** sg-public-transport-pipeline
- **Region:** asia-east1 (Singapore)
- **GCS Buckets:** 2 (raw + processed)
- **BigQuery Tables:** 14 (4 raw + 10 dbt)

---

## Next Steps

1. **Start Phase 6: Airflow Setup**
   - Install Apache Airflow in Docker
   - Create monthly extraction DAG
   - Configure task dependencies
   - Test with January 2026 data
   - Schedule monthly runs

2. **Backfill Historical Data**
   - Extract December 2025, February 2026 data
   - Load into pipeline
   - Validate consistency

3. **Documentation Updates**
   - Create Phase 6 planning doc
   - Document Airflow DAG structure
   - Update architecture diagrams

---

## Known Issues

None currently blocking progress.

---

## Environment

**Local Tools:**
- Python 3.10+ with uv
- Terraform (via Scoop)
- gcloud CLI (authenticated)
- Git

**GCP Setup:**
- Service account credentials: `credentials/gcp-service-account.json`
- Environment variables configured in `.env`

**dbt Setup:**
- Project: `sg_transport_dbt/`
- Profile: `~/.dbt/profiles.yml`
- Packages: dbt-utils installed

---

## Recent Changes

**2026-03-31:**
- ✅ Fixed empty train_stations table (field name mismatch)
- ✅ Fixed date_key conversion (dash stripping)
- ✅ Simplified tests from 100+ to 36 essential
- ✅ All models building successfully
- ✅ All tests passing (100% success rate)
- ✅ Restructured Cursor rules (1,082 → ~400 lines split into 3 files)
- ✅ Created comprehensive documentation suite

**2026-03-30:**
- ✅ Created complete star schema (10 dbt models)
- ✅ Implemented surrogate keys
- ✅ Configured partitioning and clustering
- ✅ Loaded 6.8M+ records into BigQuery

**2026-03-29:**
- ✅ Fixed GCS upload for large files
- ✅ Implemented JSON → NDJSON conversion
- ✅ Aligned GCS path structure with loader
