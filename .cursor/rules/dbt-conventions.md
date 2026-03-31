---
description: dbt modeling standards and best practices
---

# dbt Coding Conventions

## Model Organization

### Layered Architecture
```
models/
├── staging/        # Clean and standardize raw data
├── dimensions/     # Reference data with surrogate keys
└── facts/          # Measurable events with foreign keys
```

### Model Types
- **Staging:** Views that clean, rename, and filter raw tables
- **Dimensions:** Tables with reference/descriptive data
- **Facts:** Tables with measurable events (metrics)

---

## Naming Conventions

### File Names
- Staging: `stg_{source}_{entity}.sql`
  - Example: `stg_bus_stops.sql`, `stg_bus_od.sql`
- Dimensions: `dim_{entity}.sql`
  - Example: `dim_bus_stops.sql`, `dim_date.sql`
- Facts: `fact_{entity}.sql`
  - Example: `fact_bus_journeys.sql`

### Column Names
- Use `snake_case` for all column names
- Surrogate keys: `{entity}_key` (e.g., `bus_stop_key`)
- Natural keys: `{entity}_code` or `{entity}_id` (e.g., `bus_stop_code`)
- Foreign keys: `{referenced_entity}_key` (e.g., `origin_bus_stop_key`)

---

## Surrogate Keys

### Generate Using dbt_utils
```sql
{{ dbt_utils.generate_surrogate_key(['bus_stop_code']) }} AS bus_stop_key
```

### Why Use Them
- **Stability:** Natural keys may change, surrogate keys don't
- **Performance:** Integer joins faster than string joins
- **SCD Support:** Enable Slowly Changing Dimension Type 2
- **Consistency:** Uniform key type across all dimensions

### Key on Natural Keys
Always base surrogate keys on stable natural keys:
```sql
-- ✅ Good - Deterministic, based on natural key
{{ dbt_utils.generate_surrogate_key(['station_code']) }} AS station_key

-- ❌ Bad - Random, not reproducible
ROW_NUMBER() OVER (ORDER BY station_code) AS station_key
```

---

## Model Structure

### Config Block
Always include config at top of model:
```sql
{{
    config(
        materialized='table',
        description='Bus stop dimension with geographic data'
    )
}}
```

### Materialization Strategy
- **Staging:** `view` (lightweight, no storage)
- **Dimensions:** `table` (materialized for join performance)
- **Facts:** `table` (large datasets, need persistence)

### CTE Pattern
Use CTEs for readability:
```sql
WITH source AS (
    SELECT * FROM {{ source('raw', 'bus_stops') }}
),

renamed AS (
    SELECT
        BusStopCode AS bus_stop_code,
        RoadName AS road_name,
        Description AS description,
        Latitude AS latitude,
        Longitude AS longitude
    FROM source
)

SELECT * FROM renamed
```

---

## Performance Optimization

### Partitioning (Facts)
Partition large fact tables by date:
```sql
{{
    config(
        materialized='table',
        partition_by={
            'field': 'date_key',
            'data_type': 'int64',
            'range': {
                'start': 20250101,
                'end': 20280101,
                'interval': 100
            }
        }
    )
}}
```

### Clustering (Facts)
Cluster by common filter columns:
```sql
{{
    config(
        materialized='table',
        cluster_by=['origin_bus_stop_key', 'time_period_key']
    )
}}
```

**When to cluster:**
- Columns frequently used in WHERE clauses
- Columns used in JOIN conditions
- High-cardinality columns

---

## Testing Strategy

### Minimal Essential Tests
Focus on tests that catch real bugs:

**Primary Keys (Dimensions & Facts):**
```yaml
columns:
  - name: bus_stop_key
    tests:
      - unique
      - not_null
```

**Foreign Keys (Facts Only):**
```yaml
columns:
  - name: origin_bus_stop_key
    tests:
      - not_null
      - relationships:
          to: ref('dim_bus_stops')
          field: bus_stop_key
```

**Natural Keys (Staging & Dimensions):**
```yaml
columns:
  - name: bus_stop_code
    tests:
      - unique
      - not_null
```

### Skip Verbose Tests
Don't test things that are guaranteed by upstream:
- ❌ Range checks on well-formatted data
- ❌ Accepted values from trusted sources
- ❌ Not null on descriptive fields
- ❌ Staging relationship tests (redundant with fact tests)

---

## Documentation (schema.yml)

### Model-Level Documentation
```yaml
models:
  - name: dim_bus_stops
    description: >
      Bus stop dimension table with geographic data.
      Contains reference information for all bus stops in Singapore.
      One row per bus stop (5.2k rows as of 2026-03).
```

### Column-Level Documentation
```yaml
columns:
  - name: bus_stop_key
    description: Surrogate key (hash of bus_stop_code) - use for joins
  
  - name: bus_stop_code
    description: Natural key - 5-digit bus stop code from LTA
```

---

## Staging Models

### Purpose
- Clean and standardize raw data
- Rename columns to consistent format
- Apply data quality filters
- NO business logic (save for dimensions/facts)

### Example Pattern
```sql
WITH source AS (
    SELECT * FROM {{ source('raw', 'bus_od') }}
),

cleaned AS (
    SELECT
        -- Standardize date format
        REPLACE(YEAR_MONTH, '-', '') AS year_month,
        
        -- Rename to consistent format
        TIME_PER_HOUR AS hour,
        DAY_TYPE AS day_type,
        ORIGIN_PT_CODE AS origin_bus_stop_code,
        DESTINATION_PT_CODE AS destination_bus_stop_code,
        TOTAL_TRIPS AS trip_count
    
    FROM source
    
    -- Basic data quality filters
    WHERE TOTAL_TRIPS > 0
      AND ORIGIN_PT_CODE != DESTINATION_PT_CODE
)

SELECT * FROM cleaned
```

---

## Dimension Models

### Purpose
- Add surrogate keys to reference data
- Extract derived attributes
- Prepare for Type 1 or Type 2 SCD

### Example Pattern
```sql
WITH staging AS (
    SELECT * FROM {{ ref('stg_bus_stops') }}
),

with_surrogate_key AS (
    SELECT
        -- Surrogate key
        {{ dbt_utils.generate_surrogate_key(['bus_stop_code']) }} AS bus_stop_key,
        
        -- Natural key
        bus_stop_code,
        
        -- Attributes
        road_name,
        description,
        latitude,
        longitude
    
    FROM staging
)

SELECT * FROM with_surrogate_key
```

---

## Fact Models

### Purpose
- Join to dimensions via surrogate keys
- Store measurable events (metrics)
- Enforce referential integrity

### Example Pattern
```sql
WITH journey_data AS (
    SELECT * FROM {{ ref('stg_bus_od') }}
),

dimensions AS (
    SELECT 
        bus_stop_key,
        bus_stop_code
    FROM {{ ref('dim_bus_stops') }}
),

joined AS (
    SELECT
        -- Surrogate key for this fact
        {{ dbt_utils.generate_surrogate_key([
            'j.origin_bus_stop_code',
            'j.destination_bus_stop_code',
            'j.year_month',
            'j.hour',
            'j.day_type'
        ]) }} AS bus_journey_key,
        
        -- Foreign keys
        o.bus_stop_key AS origin_bus_stop_key,
        d.bus_stop_key AS destination_bus_stop_key,
        CAST(CONCAT(j.year_month, '01') AS INT64) AS date_key,
        j.hour AS time_period_key,
        
        -- Degenerate dimensions
        j.day_type,
        j.year_month,
        
        -- Measures
        j.trip_count,
        
        -- Audit
        CURRENT_TIMESTAMP() AS _loaded_at

    FROM journey_data j
    LEFT JOIN dimensions o ON j.origin_bus_stop_code = o.bus_stop_code
    LEFT JOIN dimensions d ON j.destination_bus_stop_code = d.bus_stop_code
    
    -- Data quality filter
    WHERE o.bus_stop_key IS NOT NULL
      AND d.bus_stop_key IS NOT NULL
)

SELECT * FROM joined
```

---

## Common Patterns

### Date Spine (Generate Date Dimension)
```sql
{{ dbt_utils.date_spine(
    datepart="day",
    start_date="cast('2025-01-01' as date)",
    end_date="cast('2027-12-31' as date)"
) }}
```

### Referencing Models
```sql
-- Source (raw table)
{{ source('raw', 'bus_stops') }}

-- Upstream model
{{ ref('stg_bus_stops') }}
```

### Inline Comments
```sql
-- Time period mapping based on Singapore peak hours
CASE
    WHEN hour BETWEEN 7 AND 9 THEN 'AM Peak'
    WHEN hour BETWEEN 17 AND 19 THEN 'PM Peak'
    ELSE 'Off-Peak'
END AS time_period_name
```

---

## Build & Test Commands

```bash
# Build all models
uv run dbt run

# Build specific model
uv run dbt run --select dim_bus_stops

# Build model and downstream dependencies
uv run dbt run --select dim_bus_stops+

# Test all models
uv run dbt test

# Test specific model
uv run dbt test --select fact_bus_journeys

# Build and test (full CI check)
uv run dbt build
```

---

## Documentation Generation

```bash
# Generate documentation site
uv run dbt docs generate

# Serve documentation (opens browser)
uv run dbt docs serve
```

This creates an interactive site with:
- Model lineage graph
- Column-level documentation
- Test results
- Source freshness
