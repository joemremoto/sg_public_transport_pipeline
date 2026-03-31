{{
    config(
        materialized='view',
        description='Cleaned and standardized train origin-destination journey data'
    )
}}

/*
    Staging model: stg_train_od
    
    Purpose:
        Clean and standardize raw train OD data from LTA API.
        This prepares journey data for fact table creation.
    
    Grain: One row per unique combination of:
           - Year-month
           - Day type (weekday/weekend)
           - Hour
           - Origin train station
           - Destination train station
    
    Source: {{ source('raw', 'train_od') }}
    Downstream: fact_train_journeys (fact table)
*/

WITH source AS (
    SELECT * FROM {{ source('raw', 'train_od') }}
),

cleaned AS (
    SELECT
        -- Time dimensions
        REPLACE(YEAR_MONTH, '-', '') AS year_month,  -- Remove dashes if present (202601)
        DAY_TYPE AS day_type,
        TIME_PER_HOUR AS hour,
        
        -- Journey endpoints
        ORIGIN_PT_CODE AS origin_station_code,
        DESTINATION_PT_CODE AS destination_station_code,
        
        -- Measure
        TOTAL_TRIPS AS trip_count,
        
        -- Metadata
        PT_TYPE AS transport_type

    FROM source
    
    -- Data quality filters
    WHERE TOTAL_TRIPS > 0  -- Exclude zero-trip records
      AND ORIGIN_PT_CODE IS NOT NULL
      AND DESTINATION_PT_CODE IS NOT NULL
      AND ORIGIN_PT_CODE != DESTINATION_PT_CODE  -- Exclude same origin-destination
)

SELECT * FROM cleaned
