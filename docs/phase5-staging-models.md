# Phase 5 Progress: Staging Models Created

**Date:** 2026-03-30  
**Status:** 🔄 Staging Layer Complete - Ready to Test

---

## What Was Created

### 1. Source Definitions ✅
**File:** `models/staging/_sources.yml`
- Defined all 4 raw tables as dbt sources
- Documented columns and update frequencies
- Enables dbt to track lineage

### 2. Staging Models ✅
Created 4 staging models that clean and standardize raw data:

| Model | Purpose | Grain | Rows |
|-------|---------|-------|------|
| `stg_bus_stops` | Clean bus stop data | 1 per stop | ~5.2k |
| `stg_train_stations` | Clean station data | 1 per station | ~166 |
| `stg_bus_od` | Clean bus journey data | 1 per OD-hour-daytype | ~5.9M |
| `stg_train_od` | Clean train journey data | 1 per OD-hour-daytype | ~884k |

### 3. Data Quality Tests ✅
**File:** `models/staging/schema.yml`

Tests implemented:
- ✅ **Uniqueness**: Primary keys must be unique
- ✅ **Not null**: Critical fields cannot be null
- ✅ **Referential integrity**: OD data references valid stops/stations
- ✅ **Value ranges**: Coordinates within Singapore, hours 0-23
- ✅ **Accepted values**: Day types match expected values
- ✅ **Data quality filters**: Exclude zero-trip and same-origin-destination records

### 4. Documentation ✅
- `README.md` - Project overview and commands
- `packages.yml` - dbt-utils dependency

---

## Staging Model Changes

### What Staging Models Do:

1. **Rename columns** to consistent naming convention
   ```sql
   -- Before (raw): BusStopCode, RoadName
   -- After (staging): bus_stop_code, road_name
   ```

2. **Cast data types** explicitly
   ```sql
   CAST(Latitude AS FLOAT64) AS latitude
   ```

3. **Apply data quality filters**
   ```sql
   WHERE TOTAL_TRIPS > 0  -- Exclude zero trips
     AND ORIGIN_PT_CODE != DESTINATION_PT_CODE  -- No same-origin-destination
   ```

4. **Add documentation** and tests

---

## Next Steps: Run and Test

### Step 1: Install dbt-utils Package
```powershell
cd dbt/sg_transport_dbt
uv run dbt deps
```

This installs the `dbt-utils` package (used for testing).

### Step 2: Run Staging Models
```powershell
# Run all staging models
uv run dbt run --select staging.*
```

Expected output:
```
Running with dbt=1.x.x
Found 4 models, 0 tests, 0 snapshots, 0 analyses...

Concurrency: 4 threads

12:00:00  1 of 4 START sql view model stg_bus_stops ............... [RUN]
12:00:00  2 of 4 START sql view model stg_train_stations .......... [RUN]
12:00:01  1 of 4 OK created sql view model stg_bus_stops .......... [SUCCESS in 1.23s]
12:00:01  2 of 4 OK created sql view model stg_train_stations ..... [SUCCESS in 1.24s]
12:00:01  3 of 4 START sql view model stg_bus_od .................. [RUN]
12:00:01  4 of 4 START sql view model stg_train_od ................ [RUN]
12:00:02  3 of 4 OK created sql view model stg_bus_od ............. [SUCCESS in 1.45s]
12:00:02  4 of 4 OK created sql view model stg_train_od ........... [SUCCESS in 1.46s]

Completed successfully
```

### Step 3: Test Staging Models
```powershell
# Run all tests
uv run dbt test --select staging.*
```

This will run ~20+ tests checking:
- Primary key uniqueness
- Not null constraints
- Referential integrity
- Value ranges
- Accepted values

### Step 4: Verify in BigQuery

Check that views were created:
```sql
SELECT table_name, table_type
FROM sg_public_transport_analytics.INFORMATION_SCHEMA.TABLES
WHERE table_name LIKE 'stg_%'
ORDER BY table_name;
```

Should show 4 views:
- `stg_bus_stops` (VIEW)
- `stg_train_stations` (VIEW)
- `stg_bus_od` (VIEW)
- `stg_train_od` (VIEW)

---

## File Structure Created

```
dbt/sg_transport_dbt/
├── README.md                           # Project documentation
├── packages.yml                        # dbt-utils dependency
└── models/
    └── staging/
        ├── _sources.yml                # Source definitions
        ├── schema.yml                  # Tests and docs
        ├── stg_bus_stops.sql           # Bus stops staging
        ├── stg_train_stations.sql      # Train stations staging
        ├── stg_bus_od.sql              # Bus OD staging
        └── stg_train_od.sql            # Train OD staging
```

---

## After Testing: Next Models to Create

Once staging tests pass, we'll create:

### Dimension Models (Next Session)
1. `dim_bus_stops.sql` - Add surrogate keys to bus stops
2. `dim_train_stations.sql` - Add surrogate keys to stations
3. `dim_date.sql` - Generate date dimension (2025-2027)
4. `dim_time_period.sql` - Generate time periods (0-23 hours)

### Fact Models (After Dimensions)
1. `fact_bus_journeys.sql` - Bus trips with dimension FKs
2. `fact_train_journeys.sql` - Train trips with dimension FKs

---

## Commands Reference

```powershell
# Navigate to dbt project
cd dbt/sg_transport_dbt

# Install packages
uv run dbt deps

# Test connection
uv run dbt debug

# Run staging models
uv run dbt run --select staging.*

# Test staging models
uv run dbt test --select staging.*

# Run specific model
uv run dbt run --select stg_bus_stops

# Generate documentation
uv run dbt docs generate
uv run dbt docs serve  # Opens browser with docs

# See compiled SQL
uv run dbt compile
# Check: target/compiled/sg_transport_dbt/models/staging/
```

---

## Troubleshooting

### If `dbt deps` fails:
```powershell
# Install dbt-utils manually
uv add dbt-utils
```

### If tests fail on relationships:
This means OD data references stops/stations not in reference tables.
Check:
```sql
-- Find orphaned bus stop codes
SELECT DISTINCT origin_bus_stop_code
FROM stg_bus_od
WHERE origin_bus_stop_code NOT IN (
    SELECT bus_stop_code FROM stg_bus_stops
)
```

### If `dbt run` fails with permissions:
Ensure service account has BigQuery Data Editor role.

---

**Staging Models Status:** ✅ Created, Ready to Test  
**Next:** Run `dbt deps`, then `dbt run --select staging.*`
