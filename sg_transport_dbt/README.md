# Singapore Public Transport Analytics - dbt Project

This dbt project transforms raw LTA (Land Transport Authority) data into a dimensional model for analytics.

## Project Structure

```
models/
├── staging/          # Cleaned and standardized raw data
│   ├── _sources.yml  # Source definitions
│   ├── schema.yml    # Tests and documentation
│   ├── stg_bus_stops.sql
│   ├── stg_train_stations.sql
│   ├── stg_bus_od.sql
│   └── stg_train_od.sql
├── dimensions/       # Dimension tables (coming next)
└── facts/            # Fact tables (coming next)
```

## Quick Start

### 1. Install dependencies
```bash
uv add dbt-core dbt-bigquery dbt-utils
```

### 2. Test connection
```bash
cd dbt/sg_transport_dbt
uv run dbt debug
```

### 3. Run staging models
```bash
uv run dbt run --select staging.*
```

### 4. Test staging models
```bash
uv run dbt test --select staging.*
```

## Data Flow

```
Raw Tables (BigQuery)
    ↓
Staging Models (clean & standardize)
    ↓
Dimension Models (add surrogate keys)
    ↓
Fact Models (join dimensions, create star schema)
```

## Models Built So Far

### Staging Layer ✅
- `stg_bus_stops` - Cleaned bus stop reference data
- `stg_train_stations` - Cleaned train station reference data
- `stg_bus_od` - Cleaned bus journey data
- `stg_train_od` - Cleaned train journey data

### Dimensions Layer (Next)
- `dim_bus_stops` - Bus stops with surrogate keys
- `dim_train_stations` - Train stations with surrogate keys
- `dim_date` - Date dimension (generated)
- `dim_time_period` - Time period dimension (generated)

### Facts Layer (Next)
- `fact_bus_journeys` - Bus trips with dimension FKs
- `fact_train_journeys` - Train trips with dimension FKs

## Commands

```bash
# Run all models
uv run dbt run

# Run specific model
uv run dbt run --select stg_bus_stops

# Run all staging models
uv run dbt run --select staging.*

# Test all models
uv run dbt test

# Generate documentation
uv run dbt docs generate
uv run dbt docs serve

# Full refresh (rebuild all tables)
uv run dbt run --full-refresh
```

## Testing

Models include:
- Uniqueness tests on primary keys
- Not null tests on critical fields
- Referential integrity tests (relationships)
- Value range tests (accepted values, ranges)
- Data quality filters (exclude invalid records)

## Resources

- dbt Documentation: https://docs.getdbt.com/
- BigQuery dbt adapter: https://docs.getdbt.com/reference/warehouse-setups/bigquery-setup
- dbt Utils: https://github.com/dbt-labs/dbt-utils
