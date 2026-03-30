# Phase 4 Complete - Quick Reference

**Checkpoint Date:** 2026-03-30  
**Status:** ✅ All data loaded into BigQuery

---

## Current State

### BigQuery Tables (sg_public_transport_analytics)
```
bus_stops        →  5,202 rows    (reference data)
train_stations   →    166 rows    (reference data)
bus_od           →  5.9M rows     (January 2026 journeys)
train_od         →  884k rows     (January 2026 journeys)
────────────────────────────────
Total:              ~6.8M rows
```

### GCS Structure
```
sg-public-transport-data-raw/
├── reference/
│   ├── bus_stops.ndjson      ← Loaded to BQ ✅
│   └── train_stations.ndjson ← Loaded to BQ ✅
└── journeys/
    ├── bus/2026/01/
    │   └── bus_od_202601.csv ← Loaded to BQ ✅
    └── train/2026/01/
        └── train_od_202601.csv ← Loaded to BQ ✅
```

---

## Key Commands

### Load Data
```powershell
# Load reference data
uv run python scripts/load_to_bq.py --reference

# Load OD data
uv run python scripts/load_to_bq.py --od

# Load everything
uv run python scripts/load_to_bq.py --all
```

### Verify in BigQuery
```powershell
# List tables
bq ls sg_public_transport_analytics

# Quick row count
bq query --use_legacy_sql=false "
SELECT table_name, row_count
FROM sg_public_transport_analytics.INFORMATION_SCHEMA.TABLES
WHERE table_type = 'BASE TABLE'
ORDER BY table_name
"
```

### Query Examples
```sql
-- Top 10 busiest bus routes
SELECT 
  ORIGIN_PT_CODE,
  DESTINATION_PT_CODE,
  SUM(TOTAL_TRIPS) as total_trips
FROM sg_public_transport_analytics.bus_od
GROUP BY 1, 2
ORDER BY 3 DESC
LIMIT 10;

-- Hourly train demand (weekdays)
SELECT 
  TIME_PER_HOUR as hour,
  SUM(TOTAL_TRIPS) as total_trips
FROM sg_public_transport_analytics.train_od
WHERE DAY_TYPE = 'WEEKDAY'
GROUP BY 1
ORDER BY 1;
```

---

## Architecture Pattern (Final)

```
Extract Scripts → Local Storage → Upload (convert to NDJSON) → GCS → BigQuery
     Phase 1          Phase 1              Phase 3           ✅    Phase 4 ✅
```

**Key Points:**
- ✅ GCS is the source of truth
- ✅ Reference data: JSON arrays → NDJSON in GCS → BigQuery
- ✅ OD data: CSV → GCS partitioned → BigQuery clustered
- ✅ Can reload BigQuery anytime from GCS

---

## What's Next: Phase 5 (dbt)

Transform raw tables → dimensional model:

**Current (Raw Tables):**
- `bus_stops`, `train_stations`
- `bus_od`, `train_od`

**Phase 5 (Dimensional Model):**
- `dim_bus_stops`, `dim_train_stations`, `dim_date`, `dim_time_period`
- `fact_bus_journeys`, `fact_train_journeys`
- With surrogate keys, foreign keys, data quality tests

---

## Important Files

**Documentation:**
- `docs/phase4-checkpoint.md` - Complete Phase 4 summary
- `docs/phase4-reference-data-steps.md` - Step-by-step guide

**Code:**
- `src/load/bq_schemas.py` - Table schemas
- `src/load/bq_loader.py` - BigQuery loader
- `scripts/load_to_bq.py` - CLI interface
- `src/upload/gcs_uploader.py` - GCS uploader (with NDJSON conversion)

**Config:**
- `.cursor/rules/singapore-lta-project.cursorrules` - Updated with Phase 4 status

---

## Troubleshooting

**If tables are missing:**
```powershell
uv run python scripts/load_to_bq.py --all
```

**If data in GCS but not loading:**
```powershell
# Check GCS paths
gcloud storage ls -r gs://sg-public-transport-data-raw/

# Verify correct structure:
# reference/*.ndjson
# journeys/{mode}/{year}/{month}/*.csv
```

**If need to reload:**
BigQuery tables use `WRITE_TRUNCATE` - just re-run load commands to refresh data.

---

**Phase 4:** ✅ COMPLETE  
**Ready for:** Phase 5 - dbt Transformation
