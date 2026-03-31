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
        },
        cluster_by=['origin_bus_stop_key', 'time_period_key'],
        description='Bus journey fact table with dimension foreign keys'
    )
}}

/*
    Fact model: fact_bus_journeys
    
    Purpose:
        Central fact table for bus journey analytics.
        Contains aggregated trip counts with foreign keys to all dimensions.
        This is the core table for analyzing bus passenger flows.
    
    Grain: One row per unique combination of:
           - Origin bus stop
           - Destination bus stop  
           - Date (year-month)
           - Hour
           - Day type
    
    Sources:
        - {{ ref('stg_bus_od') }} - Journey data
        - {{ ref('dim_bus_stops') }} - Bus stop dimensions
    
    Performance optimizations:
        - Partitioned by date_key for query performance
        - Clustered by origin_bus_stop_key and time_period_key
*/

WITH journey_data AS (
    SELECT * FROM {{ ref('stg_bus_od') }}
),

bus_stops AS (
    SELECT 
        bus_stop_key,
        bus_stop_code
    FROM {{ ref('dim_bus_stops') }}
),

joined AS (
    SELECT
        -- Generate surrogate key for this fact record
        {{ dbt_utils.generate_surrogate_key([
            'j.origin_bus_stop_code',
            'j.destination_bus_stop_code', 
            'j.year_month',
            'j.hour',
            'j.day_type'
        ]) }} AS bus_journey_key,
        
        -- Foreign keys to dimensions
        o.bus_stop_key AS origin_bus_stop_key,
        d.bus_stop_key AS destination_bus_stop_key,
        
        -- Date key (convert YYYYMM to YYYYMMDD format for first day of month)
        CAST(CONCAT(j.year_month, '01') AS INT64) AS date_key,
        
        -- Time period key (hour maps directly)
        j.hour AS time_period_key,
        
        -- Degenerate dimensions (attributes that don't warrant their own dimension)
        j.day_type,
        j.year_month,
        
        -- Measures
        j.trip_count,
        
        -- Audit columns
        CURRENT_TIMESTAMP() AS _loaded_at

    FROM journey_data j
    
    -- Join to origin bus stops dimension
    LEFT JOIN bus_stops o
        ON j.origin_bus_stop_code = o.bus_stop_code
    
    -- Join to destination bus stops dimension
    LEFT JOIN bus_stops d
        ON j.destination_bus_stop_code = d.bus_stop_code
    
    -- Data quality filter: only include records where we found both stops
    WHERE o.bus_stop_key IS NOT NULL
      AND d.bus_stop_key IS NOT NULL
)

SELECT * FROM joined
