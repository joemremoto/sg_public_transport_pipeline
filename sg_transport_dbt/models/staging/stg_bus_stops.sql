{{
    config(
        materialized='view',
        description='Cleaned and standardized bus stop reference data'
    )
}}

/*
    Staging model: stg_bus_stops
    
    Purpose:
        Clean and standardize raw bus stop data from LTA API.
        This is the first transformation step - we:
        1. Rename columns to consistent naming convention (lowercase, underscores)
        2. Cast to appropriate data types
        3. Add data quality checks
        4. Document the model
    
    Grain: One row per bus stop (5,202 rows as of 2026-03)
    
    Source: {{ source('raw', 'bus_stops') }}
    Downstream: dim_bus_stops (dimension model)
*/

WITH source AS (
    SELECT * FROM {{ source('raw', 'bus_stops') }}
),

renamed AS (
    SELECT
        -- Natural key (from API)
        BusStopCode AS bus_stop_code,
        
        -- Descriptive attributes
        RoadName AS road_name,
        Description AS description,
        
        -- Geographic coordinates
        CAST(Latitude AS FLOAT64) AS latitude,
        CAST(Longitude AS FLOAT64) AS longitude

    FROM source
)

SELECT * FROM renamed
