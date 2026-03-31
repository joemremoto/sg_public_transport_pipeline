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
        cluster_by=['origin_station_key', 'time_period_key'],
        description='Train journey fact table with dimension foreign keys'
    )
}}

/*
    Fact model: fact_train_journeys
    
    Purpose:
        Central fact table for train journey analytics.
        Contains aggregated trip counts with foreign keys to all dimensions.
        This is the core table for analyzing MRT/LRT passenger flows.
    
    Grain: One row per unique combination of:
           - Origin train station
           - Destination train station
           - Date (year-month)
           - Hour
           - Day type
    
    Sources:
        - {{ ref('stg_train_od') }} - Journey data
        - {{ ref('dim_train_stations') }} - Train station dimensions
    
    Performance optimizations:
        - Partitioned by date_key for query performance
        - Clustered by origin_station_key and time_period_key
*/

WITH journey_data AS (
    SELECT * FROM {{ ref('stg_train_od') }}
),

train_stations AS (
    SELECT 
        station_key,
        station_code
    FROM {{ ref('dim_train_stations') }}
),

joined AS (
    SELECT
        -- Generate surrogate key for this fact record
        {{ dbt_utils.generate_surrogate_key([
            'j.origin_station_code',
            'j.destination_station_code',
            'j.year_month',
            'j.hour',
            'j.day_type'
        ]) }} AS train_journey_key,
        
        -- Foreign keys to dimensions
        o.station_key AS origin_station_key,
        d.station_key AS destination_station_key,
        
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
    
    -- Join to origin station dimension
    LEFT JOIN train_stations o
        ON j.origin_station_code = o.station_code
    
    -- Join to destination station dimension
    LEFT JOIN train_stations d
        ON j.destination_station_code = d.station_code
    
    -- Data quality filter: only include records where we found both stations
    WHERE o.station_key IS NOT NULL
      AND d.station_key IS NOT NULL
)

SELECT * FROM joined
