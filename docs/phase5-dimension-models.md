# Phase 5: Dimension Models Created

**Date:** 2026-03-30  
**Status:** 🔄 Dimensions Complete - Ready to Test

---

## What Was Created

### 4 Dimension Models ✅

| Model | Type | Rows | Purpose |
|-------|------|------|---------|
| `dim_bus_stops` | Reference | ~5.2k | Bus stops with surrogate keys |
| `dim_train_stations` | Reference | ~166 | Train stations with surrogate keys |
| `dim_date` | Generated | ~1,095 | Date dimension (2025-2027) |
| `dim_time_period` | Generated | 24 | Hour-level time periods |

---

## Dimension Details

### 1. dim_bus_stops
**Transformation:**
- ✅ Added surrogate key (`bus_stop_key`) using hash of `bus_stop_code`
- ✅ Kept natural key (`bus_stop_code`) for reference
- ✅ Materialized as TABLE for performance

**Key Columns:**
- `bus_stop_key` - Surrogate key for fact table joins
- `bus_stop_code` - Natural key (5-digit code)
- `road_name`, `description` - Descriptive attributes
- `latitude`, `longitude` - Geographic coordinates

### 2. dim_train_stations
**Transformation:**
- ✅ Added surrogate key (`station_key`) using hash of `station_code`
- ✅ Extracted `line_code` from station code (e.g., "NS" from "NS1")
- ✅ Materialized as TABLE

**Key Columns:**
- `station_key` - Surrogate key for fact table joins
- `station_code` - Natural key (e.g., NS1, EW12)
- `station_name`, `station_name_chinese` - Names
- `line_name`, `line_code` - Line information

### 3. dim_date (Generated)
**Transformation:**
- ✅ Generated using `dbt_utils.date_spine` (2025-01-01 to 2027-12-31)
- ✅ Rich calendar attributes
- ✅ Boolean flags for analysis

**Key Columns:**
- `date_key` - Integer in YYYYMMDD format (e.g., 20260115)
- `date` - Actual date value
- `year`, `month`, `day`, `quarter` - Date components
- `day_name`, `month_name` - Formatted labels
- `is_weekend`, `is_weekday` - Boolean flags

**Time Periods Covered:** ~1,095 days (3 years)

### 4. dim_time_period (Generated)
**Transformation:**
- ✅ Generated using `GENERATE_ARRAY(0, 23)`
- ✅ Maps hours to business categories
- ✅ Peak hour classification

**Key Columns:**
- `time_period_key` - Hour (0-23)
- `hour` - Hour of day
- `time_period_name` - Category (Night, AM Peak, Inter-Peak, PM Peak, Evening)
- `is_peak_hour` - TRUE for hours 7, 8, 17, 18, 19
- `part_of_day` - General classification

**Time Period Categories:**
- **Night** (00:00-05:59): Hours 0-5
- **AM Peak** (06:00-08:59): Hours 6-8
- **Inter-Peak** (09:00-16:59): Hours 9-16
- **PM Peak** (17:00-19:59): Hours 17-19
- **Evening** (20:00-23:59): Hours 20-23

---

## Key Concepts Implemented

### Surrogate Keys
**What:** Hash-based keys independent of source system
**Why:**
- Stable joins (source codes can change)
- Better performance (integers vs strings)
- Support for slowly changing dimensions

**How:** Using `dbt_utils.generate_surrogate_key()`
```sql
{{ dbt_utils.generate_surrogate_key(['bus_stop_code']) }} AS bus_stop_key
```

### Materialization: TABLE
All dimensions use `materialized='table'`:
- Physical tables in BigQuery
- Fast query performance
- Updated on each `dbt run`

### Generated Dimensions
`dim_date` and `dim_time_period` don't have source data:
- Generated using SQL logic
- Provide rich attributes for analysis
- Standard dimensional modeling practice

---

## Tests Implemented

### Dimension Tests (40+ tests):
- ✅ Uniqueness on surrogate keys
- ✅ Not null on primary keys
- ✅ Uniqueness on natural keys
- ✅ Value range checks (dates, hours, months)
- ✅ Accepted values (time periods, parts of day)

---

## Next Steps: Run Dimension Models

### Step 1: Run Dimensions
```powershell
cd sg_transport_dbt

# Run all dimension models
uv run dbt run --select dimensions.*
```

Expected output:
```
1 of 4 START sql table model dim_bus_stops ........... [RUN]
2 of 4 START sql table model dim_train_stations ...... [RUN]
3 of 4 START sql table model dim_date ................ [RUN]
4 of 4 START sql table model dim_time_period ......... [RUN]
...
Completed successfully
```

### Step 2: Test Dimensions
```powershell
# Run all dimension tests
uv run dbt test --select dimensions.*
```

### Step 3: Verify in BigQuery
```sql
-- Check all dimension tables
SELECT table_name, row_count
FROM sg_public_transport_analytics.INFORMATION_SCHEMA.TABLES
WHERE table_name LIKE 'dim_%'
ORDER BY table_name;
```

Expected:
- `dim_bus_stops`: ~5,202 rows
- `dim_date`: ~1,095 rows (3 years)
- `dim_time_period`: 24 rows
- `dim_train_stations`: ~166 rows

### Step 4: Sample Queries
```sql
-- Preview bus stops with surrogate keys
SELECT bus_stop_key, bus_stop_code, description
FROM dim_bus_stops
LIMIT 10;

-- Check date dimension coverage
SELECT 
  MIN(date) as earliest_date,
  MAX(date) as latest_date,
  COUNT(*) as total_days
FROM dim_date;

-- Preview time periods
SELECT time_period_key, time_period_name, is_peak_hour
FROM dim_time_period
ORDER BY time_period_key;
```

---

## File Structure

```
sg_transport_dbt/models/
├── staging/                      ← Created earlier ✅
│   ├── _sources.yml
│   ├── schema.yml
│   ├── stg_bus_stops.sql
│   ├── stg_train_stations.sql
│   ├── stg_bus_od.sql
│   └── stg_train_od.sql
└── dimensions/                   ← Created now ✅
    ├── schema.yml                # Tests and docs
    ├── dim_bus_stops.sql         # Bus stops dimension
    ├── dim_train_stations.sql    # Train stations dimension
    ├── dim_date.sql              # Date dimension (generated)
    └── dim_time_period.sql       # Time period dimension (generated)
```

---

## After Testing: Next Step

Once dimension tests pass, we'll create **fact tables**:
- `fact_bus_journeys` - Bus trips with dimension FKs
- `fact_train_journeys` - Train trips with dimension FKs

These will complete the star schema!

---

**Dimension Models Status:** ✅ Created, Ready to Test  
**Next Command:** `uv run dbt run --select dimensions.*`
