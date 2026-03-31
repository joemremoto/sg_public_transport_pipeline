{{
    config(
        materialized='table',
        description='Train station dimension with surrogate key'
    )
}}

/*
    Dimension model: dim_train_stations
    
    Purpose:
        Create dimension table for train stations with surrogate keys.
        Provides stable reference data for train journey facts.
    
    Grain: One row per train station (166 rows as of 2026-03)
    
    Source: {{ ref('stg_train_stations') }}
    Downstream: fact_train_journeys
*/

WITH source AS (
    SELECT * FROM {{ ref('stg_train_stations') }}
),

with_surrogate_key AS (
    SELECT
        -- Surrogate key (generated hash-based key)
        {{ dbt_utils.generate_surrogate_key(['station_code']) }} AS station_key,
        
        -- Natural key (station code like NS1, EW12)
        station_code,
        
        -- Station names
        station_name,
        station_name_chinese,
        
        -- Line information
        line_name,
        
        -- Extract line code from station code for easier filtering
        -- E.g., "NS1" -> "NS", "EW12" -> "EW"
        REGEXP_EXTRACT(station_code, r'^([A-Z]+)') AS line_code

    FROM source
)

SELECT * FROM with_surrogate_key
