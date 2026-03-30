# Phase 4: Load Reference Data - Complete Steps

**Date:** 2026-03-30  
**Goal:** Load reference data from GCS → BigQuery (proper architecture)

---

## What Changed

### Fixed Architecture Flow
```
Before (Wrong):
Local JSON Arrays → BigQuery directly ❌

After (Correct):
Local JSON Arrays → Upload as NDJSON to GCS → BigQuery ✅
```

### Files Updated

1. **`src/upload/gcs_uploader.py`**
   - `upload_reference_data()` now converts JSON arrays to NDJSON
   - Uploads as `.ndjson` files to GCS

2. **`src/load/bq_loader.py`**  
   - `load_reference_data()` now reads from GCS NDJSON files
   - No longer loads from local files

---

## Complete Steps to Execute

### Step 1: Re-upload Reference Data (as NDJSON)

```powershell
# Upload reference data with new NDJSON conversion
uv run python scripts/upload_to_gcs.py --reference-only
```

**What this does:**
- ✅ Reads `data/raw/bus_stops.json` (JSON array)
- ✅ Converts to NDJSON format (one JSON object per line)
- ✅ Uploads to `gs://sg-public-transport-data-raw/reference/bus_stops.ndjson`
- ✅ Repeats for `train_stations.json`

**Expected output:**
```
======================================================================
📚 UPLOADING REFERENCE DATA
======================================================================

📄 Processing bus_stops.json...
   Loaded 5,202 records
   Converting to NDJSON format...
   Created NDJSON file: 5,202 lines
📤 Uploading bus_stops.ndjson (X.XX MB)...
   From: C:\...\temp\xxx.ndjson
   To:   gs://sg-public-transport-data-raw/reference/bus_stops.ndjson
✅ Successfully uploaded: reference/bus_stops.ndjson

📄 Processing train_stations.json...
   Loaded 166 records
   Converting to NDJSON format...
   Created NDJSON file: 166 lines
📤 Uploading train_stations.ndjson (X.XX MB)...
✅ Successfully uploaded: reference/train_stations.ndjson
```

### Step 2: Verify NDJSON Files in GCS

```powershell
# List reference files
gcloud storage ls gs://sg-public-transport-data-raw/reference/
```

**Expected output:**
```
gs://sg-public-transport-data-raw/reference/bus_stops.ndjson
gs://sg-public-transport-data-raw/reference/train_stations.ndjson
```

Note: Old `.json` files may still exist - that's fine, we'll use `.ndjson` files.

### Step 3: Load Reference Data into BigQuery

```powershell
# Load from GCS NDJSON files into BigQuery
uv run python scripts/load_to_bq.py --reference
```

**What this does:**
- ✅ Reads NDJSON from GCS (not local files)
- ✅ Creates BigQuery tables (if not exist)
- ✅ Loads data using BigQuery load jobs
- ✅ Reports success with row counts

**Expected output:**
```
2026-03-30 XX:XX:XX - INFO - 🔧 Validating configuration...
2026-03-30 XX:XX:XX - INFO - ✓ Configuration validated
2026-03-30 XX:XX:XX - INFO - 🚀 Initializing BigQuery loader...
2026-03-30 XX:XX:XX - INFO - ✓ BigQuery loader initialized
2026-03-30 XX:XX:XX - INFO - ================================================================================
2026-03-30 XX:XX:XX - INFO - LOADING REFERENCE DATA
2026-03-30 XX:XX:XX - INFO - ================================================================================
2026-03-30 XX:XX:XX - INFO - 
📍 Loading bus_stops...
2026-03-30 XX:XX:XX - INFO - Loading reference data for table: bus_stops
2026-03-30 XX:XX:XX - INFO - ✓ Dataset already exists: sg-public-transport-pipeline.sg_public_transport_analytics
2026-03-30 XX:XX:XX - INFO - ✓ Table already exists: sg-public-transport-pipeline.sg_public_transport_analytics.bus_stops
2026-03-30 XX:XX:XX - INFO -   Source: gs://sg-public-transport-data-raw/reference/bus_stops.ndjson
2026-03-30 XX:XX:XX - INFO -   Starting load job for bus_stops...
2026-03-30 XX:XX:XX - INFO - ✓ Successfully loaded 5,202 rows into sg_public_transport_analytics.bus_stops
2026-03-30 XX:XX:XX - INFO - 
📍 Loading train_stations...
2026-03-30 XX:XX:XX - INFO - Loading reference data for table: train_stations
2026-03-30 XX:XX:XX - INFO - ✓ Table already exists: sg-public-transport-pipeline.sg_public_transport_analytics.train_stations
2026-03-30 XX:XX:XX - INFO -   Source: gs://sg-public-transport-data-raw/reference/train_stations.ndjson
2026-03-30 XX:XX:XX - INFO -   Starting load job for train_stations...
2026-03-30 XX:XX:XX - INFO - ✓ Successfully loaded 166 rows into sg_public_transport_analytics.train_stations
2026-03-30 XX:XX:XX - INFO - ================================================================================
2026-03-30 XX:XX:XX - INFO - ✓ Reference data loading completed
2026-03-30 XX:XX:XX - INFO - ================================================================================
```

### Step 4: Verify Data in BigQuery

```powershell
# Check row counts
bq query --use_legacy_sql=false "
SELECT 
  'bus_stops' as table_name, 
  COUNT(*) as row_count 
FROM sg_public_transport_analytics.bus_stops
UNION ALL
SELECT 
  'train_stations' as table_name, 
  COUNT(*) as row_count 
FROM sg_public_transport_analytics.train_stations
"
```

**Expected output:**
```
+------------------+-----------+
|   table_name     | row_count |
+------------------+-----------+
| bus_stops        |      5202 |
| train_stations   |       166 |
+------------------+-----------+
```

### Step 5: Preview Sample Data

```powershell
# Preview bus stops
bq head -n 5 sg_public_transport_analytics.bus_stops

# Preview train stations
bq head -n 5 sg_public_transport_analytics.train_stations
```

---

## Summary of Architecture Changes

### Before (Wrong Pattern):
```
Extraction → data/raw/file.json (JSON array)
                ↓
            BigQuery (loaded directly from local file)
```

Problems:
- ❌ Skips data lake (GCS)
- ❌ Not reproducible
- ❌ Won't work in Airflow

### After (Correct Pattern):
```
Extraction → data/raw/file.json (JSON array)
                ↓
            Upload Script (converts to NDJSON)
                ↓
            GCS (gs://bucket/reference/file.ndjson)
                ↓
            BigQuery (loads from GCS)
```

Benefits:
- ✅ GCS is source of truth
- ✅ Reproducible (can reload anytime)
- ✅ Works in Airflow (Phase 6)
- ✅ Industry best practices

---

## Troubleshooting

### If Step 1 fails: "File not found"
```powershell
# Verify local files exist
ls data\raw\bus_stops.json
ls data\raw\train_stations.json

# If missing, re-run extraction
uv run python src/ingestion/extract_bus_stops.py
uv run python src/ingestion/extract_train_stations.py
```

### If Step 3 fails: "File not found in GCS"
```powershell
# Check what's actually in GCS
gcloud storage ls -L gs://sg-public-transport-data-raw/reference/

# Re-upload if needed
uv run python scripts/upload_to_gcs.py --reference-only
```

### If load succeeds but row count is 0
```powershell
# Check BigQuery load jobs for errors
bq ls -j --max_results=10

# Get job details
bq show -j <job_id>
```

---

## Next Steps

After reference data loads successfully:

1. **Load OD Data** (bus and train journey data)
   ```powershell
   # Load January 2026 OD data
   uv run python scripts/load_to_bq.py --od
   ```

2. **Verify complete dataset**
   ```powershell
   # List all tables
   bq ls sg_public_transport_analytics
   
   # Should show: bus_stops, train_stations, bus_od, train_od
   ```

3. **Move to Phase 5: dbt transformation**
   - Transform raw tables → dimensional model
   - Create `dim_*` and `fact_*` tables
   - Add data quality tests

---

## Files Modified

- ✅ `src/upload/gcs_uploader.py` - Added NDJSON conversion
- ✅ `src/load/bq_loader.py` - Changed to load from GCS
- ✅ Architecture now follows: Extract → GCS → BigQuery pattern

Ready to execute! Start with Step 1.
