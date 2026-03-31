# Quick Reference: dbt Star Schema

**Status:** ✅ Phase 5 Complete (2026-03-30)

---

## Build & Test Commands

```powershell
cd sg_transport_dbt

# Full build (all 10 models)
uv run dbt run

# Test everything (100+ tests)
uv run dbt test

# Build + test in one go
uv run dbt build

# Generate & serve documentation
uv run dbt docs generate
uv run dbt docs serve
```

---

## Model Layers

### Staging (4 views)
- `stg_bus_stops` - Clean bus stop reference
- `stg_train_stations` - Clean train station reference
- `stg_bus_od` - Clean bus journey data (filters: trip_count > 0, origin ≠ destination)
- `stg_train_od` - Clean train journey data (same filters)

### Dimensions (4 tables)
- `dim_bus_stops` - ~5.2k rows (surrogate key: bus_stop_key)
- `dim_train_stations` - ~166 rows (surrogate key: station_key)
- `dim_date` - ~1,095 rows (2025-2027)
- `dim_time_period` - 24 rows (hour categories)

### Facts (2 tables)
- `fact_bus_journeys` - ~5.9M rows (partitioned by date_key, clustered)
- `fact_train_journeys` - ~884k rows (partitioned by date_key, clustered)

---

## Selective Builds

```powershell
# Run by layer
uv run dbt run --select staging.*
uv run dbt run --select dimensions.*
uv run dbt run --select facts.*

# Run specific model
uv run dbt run --select dim_bus_stops

# Run model + all downstream dependencies
uv run dbt run --select dim_bus_stops+

# Test specific model
uv run dbt test --select fact_bus_journeys
```

---

## Common Analytics Queries

### Top 10 Bus Routes
```sql
SELECT 
  o.description as origin,
  d.description as destination,
  SUM(f.trip_count) as total_trips
FROM fact_bus_journeys f
JOIN dim_bus_stops o ON f.origin_bus_stop_key = o.bus_stop_key
JOIN dim_bus_stops d ON f.destination_bus_stop_key = d.bus_stop_key
GROUP BY 1, 2
ORDER BY 3 DESC
LIMIT 10;
```

### Peak vs Off-Peak by Mode
```sql
SELECT 
  t.is_peak_hour,
  SUM(CASE WHEN f.bus_journey_key IS NOT NULL THEN f.trip_count ELSE 0 END) as bus_trips,
  SUM(CASE WHEN t2.train_journey_key IS NOT NULL THEN t2.trip_count ELSE 0 END) as train_trips
FROM dim_time_period t
LEFT JOIN fact_bus_journeys f ON t.time_period_key = f.time_period_key
LEFT JOIN fact_train_journeys t2 ON t.time_period_key = t2.time_period_key
GROUP BY 1;
```

---

## Project Structure

```
sg_transport_dbt/
├── dbt_project.yml          # Config
├── packages.yml             # Dependencies (dbt_utils)
├── README.md                # Project overview
└── models/
    ├── staging/             # Raw data cleanup
    ├── dimensions/          # Reference tables
    └── facts/               # Analytics tables
```

---

## Next: Phase 6 (Airflow)

**Goal:** Automate the monthly data pipeline

**Components:**
1. Monthly extraction DAG
2. GCS upload task
3. BigQuery load task
4. dbt transformation task
5. Data quality checks
6. Alerting

**Commands to implement:** All manual `uv run python` commands → Airflow operators

---

**Built:** 10 models | **Tested:** 100+ checks | **Ready for:** Automation
