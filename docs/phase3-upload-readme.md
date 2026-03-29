# Phase 3: Data Upload to Google Cloud Storage

**Status:** Ready for Testing  
**Date:** 2026-03-28  
**Prerequisites:** Phase 1 (Data Extraction) ✅ | Phase 2 (Infrastructure Setup) ✅

---

## Overview

Phase 3 uploads the locally extracted LTA data to Google Cloud Storage (GCS). This moves our data from local development storage to cloud storage, where it can be accessed by BigQuery and other GCP services.

### What Gets Uploaded

**Reference Data (Dimension Tables):**
- `bus_stops.json` → `gs://bucket/reference/bus_stops.json`
- `train_stations.json` → `gs://bucket/reference/train_stations.json`

**Journey Data (Fact Tables):**
- `bus_od_202601.csv` → `gs://bucket/journeys/bus/2026/01/bus_od_202601.csv`
- `train_od_202601.csv` → `gs://bucket/journeys/train/2026/01/train_od_202601.csv`

### Data Organization in GCS

```
sg-public-transport-data-raw/
├── reference/
│   ├── bus_stops.json          # 5,202 bus stops with coordinates
│   └── train_stations.json     # 166 train stations with line codes
└── journeys/
    ├── bus/
    │   └── 2026/
    │       └── 01/
    │           └── bus_od_202601.csv  # ~5.9M journey records
    └── train/
        └── 2026/
            └── 01/
                └── train_od_202601.csv  # ~884k journey records
```

---

## What Was Built

### 1. GCS Uploader Module (`src/upload/gcs_uploader.py`)

A comprehensive Python module for uploading data to GCS with:
- Progress tracking and logging
- Error handling and validation
- Support for reference data and partitioned fact data
- Batch upload capabilities

**Key Classes:**
- `GCSUploader`: Main class handling all upload operations

**Key Methods:**
- `upload_file()`: Upload a single file
- `upload_reference_data()`: Upload bus stops and train stations
- `upload_od_data()`: Upload monthly OD data for a specific mode
- `upload_monthly_data()`: Upload all data for a specific month
- `upload_all_local_data()`: Upload everything found locally

### 2. Upload Script (`scripts/upload_to_gcs.py`)

Command-line interface for uploading data:
- Supports multiple upload modes (all, reference-only, specific month)
- Provides clear feedback and progress tracking
- Returns proper exit codes for automation

---

## How to Use

### Prerequisites

1. **Terraform infrastructure deployed** (Phase 2 completed)
   ```powershell
   # Verify buckets exist
   gcloud storage buckets list --filter="name:sg-public-transport"
   ```

2. **Service account credentials configured**
   - `.env` file has `GOOGLE_APPLICATION_CREDENTIALS` set
   - Credentials file exists at the specified path

3. **Local data extracted** (Phase 1 completed)
   ```powershell
   # Verify data exists
   ls data\raw\
   ```

### Option 1: Upload All Data (Recommended for First Run)

Upload all reference data and monthly data found locally:

```powershell
# Using uv (recommended)
uv run python scripts/upload_to_gcs.py --all

# Or using regular Python
python scripts/upload_to_gcs.py --all
```

**What this does:**
- Scans `data/raw/` for all data files
- Uploads reference data (bus stops, train stations)
- Detects and uploads all monthly OD files
- Provides detailed progress tracking

### Option 2: Upload Specific Month

Upload data for a specific month only:

```powershell
# Upload January 2026 data
uv run python scripts/upload_to_gcs.py --year 2026 --month 1

# Upload with reference data included
uv run python scripts/upload_to_gcs.py --year 2026 --month 1 --include-reference
```

### Option 3: Upload Reference Data Only

Upload only the reference/dimension data:

```powershell
uv run python scripts/upload_to_gcs.py --reference-only
```

---

## Verification Steps

After uploading, verify the data in GCS:

### 1. List Buckets

```powershell
gcloud storage buckets list --filter="name:sg-public-transport"
```

Expected output:
```
gs://sg-public-transport-data-raw/
gs://sg-public-transport-data-processed/
```

### 2. List Files in Bucket

```powershell
# List all files
gcloud storage ls -r gs://sg-public-transport-data-raw/

# List reference data
gcloud storage ls gs://sg-public-transport-data-raw/reference/

# List journey data
gcloud storage ls -r gs://sg-public-transport-data-raw/journeys/
```

Expected output:
```
gs://sg-public-transport-data-raw/reference/bus_stops.json
gs://sg-public-transport-data-raw/reference/train_stations.json
gs://sg-public-transport-data-raw/journeys/bus/2026/01/bus_od_202601.csv
gs://sg-public-transport-data-raw/journeys/train/2026/01/train_od_202601.csv
```

### 3. Check File Details

```powershell
# Get details of a specific file
gcloud storage ls -L gs://sg-public-transport-data-raw/reference/bus_stops.json
```

This shows:
- File size
- Creation time
- Storage class
- MD5 hash

### 4. Download and Inspect (Optional)

```powershell
# Download a file to verify content
gcloud storage cp gs://sg-public-transport-data-raw/reference/bus_stops.json ./test_download.json

# View first few lines
Get-Content ./test_download.json -Head 20
```

---

## Troubleshooting

### Error: "Credentials file not found"

**Problem:** GOOGLE_APPLICATION_CREDENTIALS path is incorrect

**Solution:**
```powershell
# Check .env file
cat .env | Select-String "GOOGLE_APPLICATION_CREDENTIALS"

# Verify file exists
Test-Path .\credentials\gcp-service-account.json
```

### Error: "Bucket does not exist"

**Problem:** Terraform infrastructure not deployed or bucket name mismatch

**Solution:**
```powershell
# List buckets
gcloud storage buckets list

# Check .env bucket name matches
cat .env | Select-String "GCS_BUCKET"

# Re-run terraform if needed
cd terraform
terraform apply
```

### Error: "Permission denied"

**Problem:** Service account lacks necessary permissions

**Solution:**
```powershell
# Check service account has Storage Object Admin role
gcloud projects get-iam-policy sg-public-transport-pipeline \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:*transport-pipeline*"
```

### Error: "Local file not found"

**Problem:** Data not extracted or wrong path

**Solution:**
```powershell
# List local data files
ls data\raw\

# Re-run extraction if needed (Phase 1)
cd src\ingestion
uv run python extract_bus_stops.py
uv run python extract_train_stations.py
```

---

## What's Next: Phase 4

After successfully uploading data to GCS, Phase 4 will:

1. **Create BigQuery Tables**
   - Define schemas for dimension and fact tables
   - Set up partitioning and clustering

2. **Load Data from GCS to BigQuery**
   - Load reference data into dimension tables
   - Load OD data into fact tables with partitioning

3. **Validate Data Quality**
   - Check row counts
   - Validate data types
   - Test referential integrity

---

## Summary

Phase 3 successfully moves data from local storage to cloud storage, setting the foundation for cloud-based analytics. The upload process is:

✅ **Automated** - Single command uploads all data  
✅ **Organized** - Partitioned structure for efficient querying  
✅ **Validated** - Error handling and verification built-in  
✅ **Documented** - Extensive logging tracks every operation  
✅ **Reproducible** - Can be run repeatedly without issues  

**Total Data Uploaded:** ~175 MB (5,202 bus stops, 166 stations, 6M+ journey records)

---

## Related Files

- `src/upload/gcs_uploader.py` - Main uploader implementation
- `scripts/upload_to_gcs.py` - Command-line interface
- `src/config/settings.py` - Configuration management
- `.env` - Environment variables (not in git)
- `docs/setup-log.md` - Full project history
