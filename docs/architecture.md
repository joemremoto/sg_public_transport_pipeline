# Architecture & Data Model

## Pipeline Architecture

### High-Level Data Flow
```
┌─────────────┐
│  LTA API    │ Monthly OD data + reference data
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│  Python Scripts     │ Extract, download, parse
│  (src/ingestion/)   │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  Local Storage      │ Temporary CSV/JSON storage
│  (data/raw/)        │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  GCS Upload         │ Convert to NDJSON, partition
│  (src/upload/)      │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  Google Cloud       │ Raw data lake
│  Storage (GCS)      │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  BigQuery Loader    │ Batch load from GCS
│  (src/load/)        │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  BigQuery (Raw)     │ Raw tables (bus_od, train_od, etc.)
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  dbt Transform      │ Staging → Dimensions → Facts
│  (sg_transport_dbt/)│
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  BigQuery (Star)    │ Analytical star schema
│  Schema             │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  Streamlit          │ Interactive dashboards
│  (planned)          │
└─────────────────────┘
```

---

## Star Schema Data Model

### Fact Tables

#### fact_bus_journeys (~17.6M rows)
```sql
bus_journey_key          STRING    (PK, surrogate - MD5 hash)
origin_bus_stop_key      STRING    (FK → dim_bus_stops)
destination_bus_stop_key STRING    (FK → dim_bus_stops)
date_key                 INT64     (FK → dim_date, YYYYMMDD format)
time_period_key          INT64     (FK → dim_time_period, 0-23)
day_type                 STRING    (Degenerate: WEEKDAY | WEEKENDS/HOLIDAY)
year_month               STRING    (Degenerate: YYYYMM)
trip_count               INT64     (Measure: aggregated passenger count)
_loaded_at               TIMESTAMP (Audit: load timestamp)

-- Partitioned by: date_key
-- Clustered by: origin_bus_stop_key, time_period_key
-- Grain: One row per origin-destination-hour-daytype combination
```

#### fact_train_journeys (~1.7M rows)
```sql
train_journey_key        STRING    (PK, surrogate - MD5 hash)
origin_station_key       STRING    (FK → dim_train_stations)
destination_station_key  STRING    (FK → dim_train_stations)
date_key                 INT64     (FK → dim_date)
time_period_key          INT64     (FK → dim_time_period)
day_type                 STRING    (Degenerate: WEEKDAY | WEEKENDS/HOLIDAY)
year_month               STRING    (Degenerate: YYYYMM)
trip_count               INT64     (Measure: aggregated passenger count)
_loaded_at               TIMESTAMP (Audit: load timestamp)

-- Partitioned by: date_key
-- Clustered by: origin_station_key, time_period_key
-- Grain: One row per origin-destination-hour-daytype combination
```

### Dimension Tables

#### dim_bus_stops (~5.2k rows)
```sql
bus_stop_key    STRING      (PK, surrogate - MD5 hash of bus_stop_code)
bus_stop_code   STRING      (Natural Key - 5-digit code from LTA)
road_name       STRING      (Road location)
description     STRING      (Human-readable landmark/location)
latitude        FLOAT64     (Geographic coordinate)
longitude       FLOAT64     (Geographic coordinate)

-- SCD Type: Type 1 (overwrite on change)
```

#### dim_train_stations (~213 rows)
```sql
station_key          STRING  (PK, surrogate - MD5 hash of station_code)
station_code         STRING  (Natural Key - e.g., NS1, EW12)
station_name         STRING  (English name)
station_name_chinese STRING  (Chinese name)
line_name            STRING  (Full line name - e.g., "North South Line")
line_code            STRING  (Derived: NS, EW, CC, etc.)

-- SCD Type: Type 1 (overwrite on change)
```

#### dim_date (~1,095 rows - 2025-2027)
```sql
date_key            INT64   (PK, YYYYMMDD format - e.g., 20260115)
date                DATE    (Actual date value)
year                INT64   (YYYY)
month               INT64   (1-12)
day                 INT64   (1-31)
quarter             INT64   (1-4)
day_of_week         STRING  (Sunday, Monday, ...)
day_of_week_number  INT64   (1=Sunday, 7=Saturday)
week_of_year        INT64   (1-53)
is_weekend          BOOL    (Saturday or Sunday)
is_weekday          BOOL    (Monday-Friday)

-- Generated via dbt_utils.date_spine
```

#### dim_time_period (24 rows)
```sql
time_period_key   INT64   (PK, 0-23 representing hour)
hour              INT64   (0-23, same as key)
time_period_name  STRING  (Night, AM Peak, Inter-Peak, PM Peak, Evening)
is_peak_hour      BOOL    (TRUE for 7, 8, 17, 18, 19)
part_of_day       STRING  (Late Night, Morning, Afternoon, Evening)

-- Manually generated in dbt
```

---

## Performance Optimizations

### Partitioning
**Why:** Improves query performance and reduces cost by scanning only relevant partitions.

**Applied to:**
- `fact_bus_journeys` - Partitioned by `date_key` (range partitioning)
- `fact_train_journeys` - Partitioned by `date_key` (range partitioning)

**Example Query Benefit:**
```sql
-- Only scans January 2026 partition (not entire 17.6M rows)
SELECT * 
FROM fact_bus_journeys 
WHERE date_key BETWEEN 20260101 AND 20260131
```

### Clustering
**Why:** Physically organizes data by common filter columns for faster queries.

**Applied to:**
- `fact_bus_journeys` - Clustered by `[origin_bus_stop_key, time_period_key]`
- `fact_train_journeys` - Clustered by `[origin_station_key, time_period_key]`

**Example Query Benefit:**
```sql
-- Quickly locates all trips from a specific stop during peak hours
SELECT * 
FROM fact_bus_journeys 
WHERE origin_bus_stop_key = '...' 
  AND time_period_key IN (7, 8, 17, 18, 19)
```

### Materialization Strategy
- **Staging models:** Views (no storage, always fresh)
- **Dimension tables:** Tables (materialized for fast joins)
- **Fact tables:** Tables (large datasets, need persistence)

---

## Data Lineage

```
┌──────────────┐
│ Raw Tables   │ BigQuery (loaded from GCS)
└──────┬───────┘
       │
       ├─→ bus_stops ──→ stg_bus_stops ──→ dim_bus_stops ──┐
       │                                                     │
       ├─→ train_stations ──→ stg_train_stations ──→ dim_train_stations ──┐
       │                                                     │              │
       ├─→ bus_od ──→ stg_bus_od ────────┐                 │              │
       │                                  │                 │              │
       └─→ train_od ──→ stg_train_od ────┤                 │              │
                                          │                 │              │
                                          ▼                 ▼              ▼
                     (Generated) ──→ dim_date ──→ fact_bus_journeys
                     (Generated) ──→ dim_time_period ──→ fact_train_journeys
```

---

## GCS Data Layout

### Raw Data Bucket: `sg-public-transport-data-raw`

```
reference/
├── bus_stops.ndjson          # 5.2k rows, ~740 KB
└── train_stations.ndjson     # 213 rows, ~30 KB

journeys/
├── bus/
│   ├── 2025/
│   │   └── 12/
│   │       └── bus_od_202512.csv
│   └── 2026/
│       ├── 01/
│       │   └── bus_od_202601.csv
│       └── 02/
│           └── bus_od_202602.csv
└── train/
    ├── 2025/
    │   └── 12/
    │       └── train_od_202512.csv
    └── 2026/
        ├── 01/
        │   └── train_od_202601.csv
        └── 02/
            └── train_od_202602.csv
```

**Naming Convention:**
- Reference: `{entity}.ndjson`
- Journeys: `{mode}_od_{YYYYMM}.csv`

**File Formats:**
- Reference data: NDJSON (newline-delimited JSON)
- Journey data: CSV with headers

---

## BigQuery Dataset: `sg_public_transport_analytics`

### Raw Tables (Loaded from GCS)
```
bus_stops        5,202 rows       ~274 KB
train_stations   213 rows         ~9 KB
bus_od           17,574,644 rows  ~870 MB
train_od         2,639,048 rows   ~129 MB
```

### dbt Models (Transformed)
```
-- Staging (Views)
stg_bus_stops        5,202 rows
stg_train_stations   213 rows
stg_bus_od           ~17.6M rows (filtered)
stg_train_od         ~1.7M rows (filtered)

-- Dimensions (Tables)
dim_bus_stops        5,202 rows       ~275 KB
dim_train_stations   213 rows         ~9 KB
dim_date             1,095 rows       ~20 KB
dim_time_period      24 rows          ~1 KB

-- Facts (Tables, Partitioned)
fact_bus_journeys    17,574,644 rows  ~870 MB
fact_train_journeys  1,700,000 rows   ~129 MB
```

---

## Technology Stack Details

### Data Extraction
- **Language:** Python 3.10+
- **Libraries:** requests, zipfile, pandas
- **Package Manager:** uv
- **Key Modules:**
  - `src/ingestion/lta_client.py` - API wrapper
  - `src/ingestion/extract_bus_od.py` - Bus journey extraction
  - `src/ingestion/extract_train_od.py` - Train journey extraction
  - `src/ingestion/extract_bus_stops.py` - Bus stop reference
  - `src/ingestion/extract_train_stations.py` - Train station reference

### Data Upload
- **Cloud Storage:** Google Cloud Storage (GCS)
- **Key Module:** `src/upload/gcs_uploader.py`
- **Features:**
  - JSON → NDJSON conversion for reference data
  - Retry logic with exponential backoff
  - Dynamic timeout based on file size
  - Partitioned upload structure

### Data Loading
- **Data Warehouse:** Google BigQuery
- **Key Modules:**
  - `src/load/bq_schemas.py` - Schema definitions
  - `src/load/bq_loader.py` - Loader with batch operations
- **Features:**
  - Schema validation
  - Clustering on fact tables
  - NDJSON/CSV format handling

### Data Transformation
- **Tool:** dbt (Data Build Tool)
- **Adapter:** dbt-bigquery
- **Dependencies:** dbt-utils (for surrogate keys)
- **Models:** 10 models (4 staging, 4 dimensions, 2 facts)

### Infrastructure
- **IaC Tool:** Terraform
- **Resources Provisioned:**
  - 2 GCS buckets
  - 1 BigQuery dataset
  - 1 Service account with appropriate IAM roles
- **Location:** asia-east1 (Singapore region)

### Orchestration (Planned - Phase 6)
- **Tool:** Apache Airflow
- **Deployment:** Docker containers
- **DAGs:** Monthly extraction → upload → load → transform

### Visualization (Planned - Phase 7)
- **Tool:** Streamlit
- **Queries:** Direct BigQuery connection
- **Features:** Interactive dashboards, geospatial maps

---

## Key Design Decisions

### Surrogate Keys
**Decision:** Use MD5 hash-based surrogate keys for all dimensions.

**Rationale:**
- Deterministic (same input = same key)
- Supports Slowly Changing Dimensions (SCD Type 2)
- Better query performance (hash string vs. composite natural keys)
- Stable even if natural keys change

**Implementation:**
```sql
{{ dbt_utils.generate_surrogate_key(['bus_stop_code']) }} AS bus_stop_key
```

### Separate Fact Tables by Mode
**Decision:** Create separate fact tables for bus and train (not combined).

**Rationale:**
- Different dimension tables (stops vs. stations)
- Different analysis patterns
- Easier to partition and optimize separately
- Clearer data model

### Batch Processing (Not Streaming)
**Decision:** Monthly batch processing, not real-time streaming.

**Rationale:**
- LTA releases data monthly (by 10th of following month)
- No real-time data source available
- Batch aligns with business cadence
- Simpler architecture for learning

### No Multi-Modal Analysis
**Decision:** Track bus and train separately, no cross-mode journeys.

**Rationale:**
- LTA API provides separate OD counts per mode
- No way to link bus→train transfers in public dataset
- Would require estimation/modeling (violates "use actual data only" principle)

---

## Data Quality Checks

### dbt Tests (36 total)
- **Primary Keys:** Unique + not null (10 tests)
- **Foreign Keys:** Relationships to dimensions (10 tests)
- **Natural Keys:** Unique + not null in staging/dims (16 tests)

### Manual Reconciliation
- Total trip counts match LTA published statistics
- All 24 hours represented in each day
- No orphaned foreign keys (enforced by WHERE clauses)

---

## Scalability Considerations

### Current Scale
- **Records:** 19.3M fact records
- **Storage:** ~1 GB total in BigQuery
- **Build Time:** ~15 seconds for full dbt run
- **Test Time:** ~13 seconds for all tests

### Future Scale (12+ months)
- **Estimated Records:** 200M+ fact records
- **Storage:** ~10-15 GB
- **Build Time:** Incremental models recommended
- **Optimization:** Partition pruning, clustering will maintain performance
