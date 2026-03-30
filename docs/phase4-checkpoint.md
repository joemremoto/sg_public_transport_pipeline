# Phase 4 Checkpoint: BigQuery Schema & Load - COMPLETE

**Date:** 2026-03-30  
**Status:** ✅ Phase 4 Complete  
**Data Loaded:** Reference data (bus stops, train stations) + January 2026 OD data (bus, train)

---

## What Was Accomplished

### Phase 4 Deliverables - All Complete ✅

1. **BigQuery Schema Definitions** ✅
   - Created `src/load/bq_schemas.py` with schemas for all tables
   - Defined proper field types, modes, and descriptions
   - Schema registry for easy lookup

2. **BigQuery Loader Module** ✅
   - Created `src/load/bq_loader.py` with comprehensive loading logic
   - Handles table creation, schema management
   - Supports both reference data and OD data loads
   - Implements clustering for performance

3. **CLI Script** ✅
   - Created `scripts/load_to_bq.py` with multiple load options
   - Supports: `--reference`, `--od`, `--all`, `--mode`, `--period`
   - Comprehensive logging and error handling

4. **Data Architecture Fix** ✅
   - Fixed JSON array → NDJSON conversion for reference data
   - Implemented proper data flow: Local → GCS → BigQuery
   - GCS is now the source of truth

---

## Tables Created in BigQuery

### Dataset: `sg_public_transport_analytics`
Location: `asia-east1`

**Reference Tables (Dimensions):**
- ✅ `bus_stops` - 5,202 rows
- ✅ `train_stations` - 166 rows

**OD Tables (Facts):**
- ✅ `bus_od` - ~5.9M rows (January 2026)
- ✅ `train_od` - ~884k rows (January 2026)

Total: **~6.8M records loaded**

---

## Data Flow Architecture

### Final Architecture (Correct)
```
┌─────────────────┐
│  LTA API        │
│  (Data Source)  │
└────────┬────────┘
         │ Extract
         ▼
┌─────────────────┐
│  Local Storage  │
│  data/raw/      │
│  - JSON arrays  │
│  - CSV files    │
└────────┬────────┘
         │ Upload
         │ (Convert JSON→NDJSON)
         ▼
┌─────────────────┐
│  GCS (Data Lake)│
│  - reference/   │
│    *.ndjson     │
│  - journeys/    │
│    {mode}/{Y}/  │
│    {M}/*.csv    │
└────────┬────────┘
         │ Load
         ▼
┌─────────────────┐
│  BigQuery       │
│  (Data WH)      │
│  - Raw tables   │
└─────────────────┘
```

**GCS Structure:**
```
sg-public-transport-data-raw/
├── reference/
│   ├── bus_stops.ndjson
│   └── train_stations.ndjson
└── journeys/
    ├── bus/
    │   └── 2026/
    │       └── 01/
    │           └── bus_od_202601.csv
    └── train/
        └── 2026/
            └── 01/
                └── train_od_202601.csv
```

---

## Key Fixes Implemented

### Issue 1: JSON Array Format
**Problem:** BigQuery expects NDJSON, but extraction scripts save JSON arrays

**Solution:**
- Updated `src/upload/gcs_uploader.py` to convert JSON arrays → NDJSON
- Reference data now uploaded as `.ndjson` files
- Conversion happens during upload (transparent to user)

### Issue 2: Path Mismatch
**Problem:** Loader looked for `od_data/{mode}/` but uploader used `journeys/{mode}/{year}/{month}/`

**Solution:**
- Fixed `src/load/bq_loader.py` to use correct path structure
- Fixed `scripts/load_to_bq.py` scanner to match uploader structure
- Aligned with GCS partitioned layout

### Issue 3: Local vs GCS Loading
**Problem:** Initially loaded directly from local files (not production-ready)

**Solution:**
- Changed loader to always load from GCS (not local files)
- GCS is now the single source of truth
- Can reload BigQuery anytime from GCS

---

## Commands Used

### Reference Data Load
```powershell
# 1. Upload reference data (converts to NDJSON)
uv run python scripts/upload_to_gcs.py --reference-only

# 2. Load into BigQuery from GCS
uv run python scripts/load_to_bq.py --reference
```

### OD Data Load
```powershell
# Load all OD data found in GCS
uv run python scripts/load_to_bq.py --od
```

### Verification
```powershell
# List tables
bq ls sg_public_transport_analytics

# Check row counts
bq query --use_legacy_sql=false "
SELECT 
  table_name,
  row_count
FROM sg_public_transport_analytics.INFORMATION_SCHEMA.TABLES
ORDER BY table_name
"
```

---

## Data Validation Results

### Reference Data
| Table | Expected Rows | Actual Rows | Status |
|-------|--------------|-------------|--------|
| bus_stops | 5,202 | 5,202 | ✅ |
| train_stations | 166 | 166 | ✅ |

### OD Data (January 2026)
| Table | Expected Rows | Actual Rows | Status |
|-------|--------------|-------------|--------|
| bus_od | ~5.9M | ~5,900,000 | ✅ |
| train_od | ~884k | ~884,000 | ✅ |

---

## Files Created/Modified

### New Files Created:
- ✅ `src/load/__init__.py`
- ✅ `src/load/bq_schemas.py` (310 lines)
- ✅ `src/load/bq_loader.py` (482 lines)
- ✅ `scripts/load_to_bq.py` (410 lines)
- ✅ `docs/phase4-reference-data-steps.md`
- ✅ `docs/phase4-checkpoint.md` (this file)

### Files Modified:
- ✅ `src/upload/gcs_uploader.py` - Added NDJSON conversion
- ✅ `.cursor/rules/singapore-lta-project.cursorrules` - Updated status

---

## Lessons Learned

### 1. Data Format Matters
BigQuery has specific format requirements:
- NDJSON for JSON data (not JSON arrays)
- CSV with proper headers
- Schema must match data exactly

### 2. GCS as Source of Truth
Always load from GCS, not local files:
- ✅ Reproducible
- ✅ Works in production (Airflow)
- ✅ Single source of truth
- ✅ Can reload anytime

### 3. Path Consistency
Uploader and loader must use same directory structure:
- Document the structure clearly
- Use constants/config for paths
- Test end-to-end

### 4. Batch vs Streaming
For this use case:
- Reference data: Small, load via BigQuery load jobs
- OD data: Large, load via BigQuery load jobs from GCS
- Streaming insert would be for real-time data

---

## What's Next: Phase 5 - dbt Transformation

Phase 4 loaded **raw/staging tables**. Phase 5 will transform into dimensional model:

### Phase 5 Goals:
1. **Set up dbt project**
   - Initialize dbt
   - Configure BigQuery connection
   - Set up dbt project structure

2. **Create staging models**
   - Clean and standardize raw data
   - Handle data quality issues
   - Add data type conversions

3. **Create dimension tables**
   - `dim_bus_stops` (from `bus_stops`)
   - `dim_train_stations` (from `train_stations`)
   - `dim_date` (generated)
   - `dim_time_period` (generated)
   - Add surrogate keys

4. **Create fact tables**
   - `fact_bus_journeys` (from `bus_od`)
   - `fact_train_journeys` (from `train_od`)
   - Join to dimensions
   - Add foreign keys

5. **Add data quality tests**
   - Uniqueness tests
   - Not null tests
   - Referential integrity tests
   - Value range tests

---

## Current Project State

### Data Pipeline Progress:
- ✅ Phase 1: Data Extraction (4 scripts, ~175 MB data)
- ✅ Phase 2: Infrastructure Setup (Terraform, GCS, BigQuery, IAM)
- ✅ Phase 3: Data Upload (GCS uploader, NDJSON conversion)
- ✅ **Phase 4: BigQuery Schema & Load** (4 tables, 6.8M+ rows)
- ⏳ Phase 5: Transformation (dbt) - NEXT
- ⏳ Phase 6: Orchestration (Airflow)
- ⏳ Phase 7: Visualization (Streamlit)

### Infrastructure Status:
- ✅ GCP Project: `sg-public-transport-pipeline`
- ✅ GCS Buckets: `sg-public-transport-data-raw`, `sg-public-transport-data-processed`
- ✅ BigQuery Dataset: `sg_public_transport_analytics` (asia-east1)
- ✅ Service Account: `sg-transport-pipeline-v2@...`
- ✅ IAM Roles: Storage Admin, BigQuery Data Editor, BigQuery Job User

### Data Available:
- ✅ Reference data: Bus stops (5.2k), Train stations (166)
- ✅ OD data: January 2026 (bus + train, 6.8M+ records)
- ⏳ Additional months: December 2025, February 2026 (extracted locally, can upload)

---

## Verification Commands

### BigQuery Console
```
https://console.cloud.google.com/bigquery?project=sg-public-transport-pipeline
```

### Sample Queries
```sql
-- Check all tables
SELECT table_name, row_count
FROM sg_public_transport_analytics.INFORMATION_SCHEMA.TABLES
WHERE table_type = 'BASE TABLE'
ORDER BY table_name;

-- Preview bus stops
SELECT * 
FROM sg_public_transport_analytics.bus_stops 
LIMIT 10;

-- Preview train stations
SELECT *
FROM sg_public_transport_analytics.train_stations
LIMIT 10;

-- Top 10 busiest bus routes (January 2026)
SELECT 
  ORIGIN_PT_CODE,
  DESTINATION_PT_CODE,
  SUM(TOTAL_TRIPS) as total_trips
FROM sg_public_transport_analytics.bus_od
GROUP BY ORIGIN_PT_CODE, DESTINATION_PT_CODE
ORDER BY total_trips DESC
LIMIT 10;

-- Peak hour train usage
SELECT 
  TIME_PER_HOUR,
  SUM(TOTAL_TRIPS) as total_trips
FROM sg_public_transport_analytics.train_od
WHERE DAY_TYPE = 'WEEKDAY'
GROUP BY TIME_PER_HOUR
ORDER BY TIME_PER_HOUR;
```

---

## Success Criteria - Met ✅

Phase 4 success criteria (all met):
- ✅ BigQuery tables created with proper schemas
- ✅ Data loaded from GCS (not local files)
- ✅ Reference data loaded (5,368 total rows)
- ✅ OD data loaded (6.8M+ rows)
- ✅ Proper partitioning/clustering configured
- ✅ Load process is reproducible
- ✅ CLI supports multiple load scenarios
- ✅ Comprehensive logging and error handling

---

**Phase 4 Status:** ✅ COMPLETE  
**Ready for:** Phase 5 - dbt Transformation  
**Checkpoint Date:** 2026-03-30
