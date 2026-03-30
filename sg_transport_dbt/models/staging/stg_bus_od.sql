{{
    config(
        materialized='view',
        description='Cleaned and standardized bus origin-destination journey data'
    )
}}

/*
    Staging model: stg_bus_od
    
    Purpose:
        Clean and standardize raw bus OD data from LTA API.
        This prepares journey data for fact table creation.
    
    Grain: One row per unique combination of:
           - Year-month
           - Day type (weekday/weekend)
           - Hour
           - Origin bus stop
           - Destination bus stop
    
    Source: {{ source('raw', 'bus_od') }}
    Downstream: fact_bus_journeys (fact table)
*/

WITH source AS (
    SELECT * FROM {{ source('raw', 'bus_od') }}
),

cleaned AS (
    SELECT
        -- Time dimensions
        YEAR_MONTH AS year_month,
        DAY_TYPE AS day_type,
        TIME_PER_HOUR AS hour,
        
        -- Journey endpoints
        ORIGIN_PT_CODE AS origin_bus_stop_code,
        DESTINATION_PT_CODE AS destination_bus_stop_code,
        
        -- Measure
        TOTAL_TRIPS AS trip_count,
        
        -- Metadata
        PT_TYPE AS transport_type

    FROM source
    
    -- Data quality filters
    WHERE TOTAL_TRIPS > 0  -- Exclude zero-trip records (data quality)
      AND ORIGIN_PT_CODE IS NOT NULL
      AND DESTINATION_PT_CODE IS NOT NULL
      AND ORIGIN_PT_CODE != DESTINATION_PT_CODE  -- Exclude same origin-destination
)

SELECT * FROM cleaned
