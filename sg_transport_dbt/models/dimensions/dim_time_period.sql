{{
    config(
        materialized='table',
        description='Time period dimension for hourly analysis'
    )
}}

/*
    Dimension model: dim_time_period
    
    Purpose:
        Generate a time period dimension for hourly analysis.
        Maps hours (0-23) to meaningful time period categories.
        This is a generated dimension (no source data required).
    
    Grain: One row per hour (24 rows)
    
    Source: Generated using GENERATE_ARRAY
    Downstream: fact_bus_journeys, fact_train_journeys
    
    Time Period Definitions:
        - Night:       00:00-05:59 (hours 0-5)
        - AM Peak:     06:00-08:59 (hours 6-8)
        - Inter-Peak:  09:00-16:59 (hours 9-16)
        - PM Peak:     17:00-19:59 (hours 17-19)
        - Evening:     20:00-23:59 (hours 20-23)
*/

WITH hours AS (
    SELECT hour 
    FROM UNNEST(GENERATE_ARRAY(0, 23)) AS hour
),

time_periods AS (
    SELECT
        -- Surrogate key: hour itself serves as the key
        hour AS time_period_key,
        
        -- Hour attributes
        hour,
        
        -- Formatted hour for display
        FORMAT('%02d:00', hour) AS hour_start,           -- e.g., "08:00"
        FORMAT('%02d:59', hour) AS hour_end,             -- e.g., "08:59"
        FORMAT('%02d:00-%02d:59', hour, hour) AS hour_range,  -- e.g., "08:00-08:59"
        
        -- 12-hour format
        CASE 
            WHEN hour = 0 THEN '12 AM'
            WHEN hour < 12 THEN FORMAT('%d AM', hour)
            WHEN hour = 12 THEN '12 PM'
            ELSE FORMAT('%d PM', hour - 12)
        END AS hour_12h,
        
        -- Time period classification
        CASE
            WHEN hour BETWEEN 0 AND 5 THEN 'Night'
            WHEN hour BETWEEN 6 AND 8 THEN 'AM Peak'
            WHEN hour BETWEEN 9 AND 16 THEN 'Inter-Peak'
            WHEN hour BETWEEN 17 AND 19 THEN 'PM Peak'
            WHEN hour BETWEEN 20 AND 23 THEN 'Evening'
        END AS time_period_name,
        
        -- Peak hour flag
        CASE
            WHEN hour IN (7, 8, 17, 18, 19) THEN TRUE
            ELSE FALSE
        END AS is_peak_hour,
        
        -- Part of day classification
        CASE
            WHEN hour BETWEEN 0 AND 5 THEN 'Late Night'
            WHEN hour BETWEEN 6 AND 11 THEN 'Morning'
            WHEN hour BETWEEN 12 AND 17 THEN 'Afternoon'
            WHEN hour BETWEEN 18 AND 23 THEN 'Evening'
        END AS part_of_day,
        
        -- Business hours flag
        CASE
            WHEN hour BETWEEN 9 AND 17 THEN TRUE
            ELSE FALSE
        END AS is_business_hours

    FROM hours
)

SELECT * FROM time_periods
