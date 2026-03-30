{{
    config(
        materialized='view',
        description='Cleaned and standardized train station reference data'
    )
}}

/*
    Staging model: stg_train_stations
    
    Purpose:
        Clean and standardize raw train station data from LTA.
        Prepares station reference data for dimensional modeling.
    
    Grain: One row per train station (166 rows as of 2026-03)
    
    Source: {{ source('raw', 'train_stations') }}
    Downstream: dim_train_stations (dimension model)
*/

WITH source AS (
    SELECT * FROM {{ source('raw', 'train_stations') }}
),

renamed AS (
    SELECT
        -- Natural key (station code)
        stn_code AS station_code,
        
        -- Station names
        mrt_station_english AS station_name,
        mrt_station_chinese AS station_name_chinese,
        
        -- Line information
        mrt_line_english AS line_name

    FROM source
)

SELECT * FROM renamed
