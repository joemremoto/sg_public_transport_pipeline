{{
    config(
        materialized='table',
        description='Bus stop dimension with surrogate key'
    )
}}

/*
    Dimension model: dim_bus_stops
    
    Purpose:
        Create dimension table for bus stops with surrogate keys.
        Surrogate keys provide:
        - Stable keys for fact tables (independent of source system changes)
        - Better join performance (integers vs strings)
        - Support for slowly changing dimensions (future enhancement)
    
    Grain: One row per bus stop (5,202 rows as of 2026-03)
    
    Source: {{ ref('stg_bus_stops') }}
    Downstream: fact_bus_journeys
*/

WITH source AS (
    SELECT * FROM {{ ref('stg_bus_stops') }}
),

with_surrogate_key AS (
    SELECT
        -- Surrogate key (generated hash-based key for stable identification)
        {{ dbt_utils.generate_surrogate_key(['bus_stop_code']) }} AS bus_stop_key,
        
        -- Natural key (original identifier from source system)
        bus_stop_code,
        
        -- Descriptive attributes
        road_name,
        description,
        
        -- Geographic coordinates
        latitude,
        longitude

    FROM source
)

SELECT * FROM with_surrogate_key
