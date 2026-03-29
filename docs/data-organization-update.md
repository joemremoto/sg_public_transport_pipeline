# Data Organization Update

**Date:** 2026-03-29  
**Status:** Updated to use mode-specific subdirectories

---

## What Changed

Updated the project to use a cleaner directory structure where OD data files are organized by transport mode.

### New Structure

```
data/
└── raw/
    ├── bus_stops.json              # Reference data (root level)
    ├── train_stations.json         # Reference data (root level)
    ├── bus/                        # Bus OD data subdirectory
    │   ├── bus_od_202512.csv
    │   ├── bus_od_202601.csv
    │   └── bus_od_202602.csv
    └── train/                      # Train OD data subdirectory
        ├── train_od_202512.csv
        ├── train_od_202601.csv
        └── train_od_202602.csv
```

### Benefits

1. **Better Organization** - Clear separation between bus and train data
2. **Matches GCS Structure** - Mirrors cloud storage layout (journeys/bus/, journeys/train/)
3. **Easier Maintenance** - Scripts know exactly where to find files
4. **Scalability** - Can add more modes or file types without confusion

---

## Files Updated

### 1. Extraction Scripts
- `src/ingestion/extract_bus_od.py` - Now saves to `data/raw/bus/`
- `src/ingestion/extract_train_od.py` - Now saves to `data/raw/train/`

### 2. Upload Script
- `src/upload/gcs_uploader.py` - Now looks in mode-specific subdirectories

### 3. Test Script (NEW)
- `tests/test_data_organization.py` - Validates file organization

---

## Migration Steps

If you have existing CSV files in `data/raw/`, move them to the correct subdirectories:

### Manual Move (PowerShell)

```powershell
# Move bus OD files
Move-Item data\raw\bus_od_*.csv data\raw\bus\

# Move train OD files
Move-Item data\raw\train_od_*.csv data\raw\train\
```

### Verify Organization

After moving files, run the validation test:

```powershell
python tests/test_data_organization.py
```

This will check:
- ✓ Reference data files exist in `data/raw/`
- ✓ OD data files exist in mode-specific subdirectories
- ✓ No files are misplaced
- ✓ All filenames follow naming conventions

---

## Expected Output

When you run the validation test, you should see:

```
======================================================================
DATA ORGANIZATION VALIDATION TEST
======================================================================

======================================================================
1. CHECKING REFERENCE DATA FILES
======================================================================

✓ Found bus_stops.json (0.90 MB)
✓ Found train_stations.json (0.02 MB)

======================================================================
2. CHECKING OD DATA ORGANIZATION
======================================================================

Checking BUS directory:
  Path: C:\...\data\raw\bus
✓   Found 3 bus OD files
    • bus_od_202512.csv (232.42 MB)
    • bus_od_202601.csv (232.42 MB)
    • bus_od_202602.csv (232.42 MB)

Checking TRAIN directory:
  Path: C:\...\data\raw\train
✓   Found 3 train OD files
    • train_od_202512.csv (36.12 MB)
    • train_od_202601.csv (36.12 MB)
    • train_od_202602.csv (36.12 MB)

======================================================================
3. CHECKING FOR MISPLACED FILES
======================================================================

✓ No misplaced OD files found - all files are organized correctly!

======================================================================
4. VALIDATING FILE NAMING CONVENTIONS
======================================================================

✓ All file names follow the correct convention

======================================================================
VALIDATION SUMMARY
======================================================================

📊 Statistics:
   • Reference files: 2 expected
   • Bus OD files: 3
   • Train OD files: 3
   • Total OD files: 6

🔍 Check Results:
✓ Reference data files
✓ OD data organization
✓ No misplaced files
✓ File naming conventions

======================================================================

✓ ALL VALIDATION CHECKS PASSED!

Your data files are organized correctly.
Scripts can now reliably find and process your data.
```

---

## Impact on Other Phases

### Phase 3: Upload (Already Updated)
- Upload script now looks in correct subdirectories
- No changes needed to GCS structure (already partitioned correctly)

### Phase 4: BigQuery Load (Next)
- Will reference GCS paths: `gs://bucket/journeys/bus/2026/01/bus_od_202601.csv`
- No impact - GCS structure remains the same

### Phase 6: Airflow (Future)
- DAGs will use updated extraction scripts
- Automatically saves to correct locations

---

## Quick Reference

### Extraction
```powershell
# Extract bus data → saves to data/raw/bus/
uv run python src/ingestion/extract_bus_od.py --year 2026 --month 1

# Extract train data → saves to data/raw/train/
uv run python src/ingestion/extract_train_od.py --year 2026 --month 1
```

### Upload
```powershell
# Upload all data (looks in subdirectories automatically)
uv run python scripts/upload_to_gcs.py --all

# Upload specific month
uv run python scripts/upload_to_gcs.py --year 2026 --month 1 --mode bus
```

### Validation
```powershell
# Check if files are organized correctly
python tests/test_data_organization.py
```

---

## Troubleshooting

### "Missing directory" error
```powershell
# Create directories if they don't exist
mkdir data\raw\bus
mkdir data\raw\train
```

### "Misplaced files" warning
```powershell
# Move files to correct location
Move-Item data\raw\*_od_*.csv data\raw\bus\  # or train\
```

### "No OD files found" (but you have data)
- Check if files are in old location (`data/raw/` instead of `data/raw/bus/`)
- Run validation test to identify misplaced files
- Move files to correct subdirectories

---

This structure is now consistent throughout the pipeline and ready for Phase 4!
