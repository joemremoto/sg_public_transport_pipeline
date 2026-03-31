{{
    config(
        materialized='table',
        description='Date dimension table for temporal analysis'
    )
}}

/*
    Dimension model: dim_date
    
    Purpose:
        Generate a date dimension table for temporal analysis.
        This is a generated dimension (no source data required).
        Provides rich calendar attributes for analytical queries.
    
    Grain: One row per date (covers 2025-2027, ~1,095 rows)
    
    Source: Generated using dbt_utils.date_spine
    Downstream: fact_bus_journeys, fact_train_journeys
    
    Design Notes:
        - date_key is in YYYYMMDD format as integer for easy joining
        - Covers full range of data we expect (3 years)
        - Can be extended as needed for future data
*/

WITH date_spine AS (
    {{
        dbt_utils.date_spine(
            datepart="day",
            start_date="cast('2025-01-01' as date)",
            end_date="cast('2027-12-31' as date)"
        )
    }}
),

date_dimension AS (
    SELECT
        -- Surrogate key: YYYYMMDD as integer (e.g., 20260115 for 2026-01-15)
        CAST(FORMAT_DATE('%Y%m%d', date_day) AS INT64) AS date_key,
        
        -- Full date
        date_day AS date,
        
        -- Date components
        EXTRACT(YEAR FROM date_day) AS year,
        EXTRACT(MONTH FROM date_day) AS month,
        EXTRACT(DAY FROM date_day) AS day,
        EXTRACT(QUARTER FROM date_day) AS quarter,
        EXTRACT(DAYOFYEAR FROM date_day) AS day_of_year,
        EXTRACT(WEEK FROM date_day) AS week_of_year,
        EXTRACT(DAYOFWEEK FROM date_day) AS day_of_week_number,  -- 1=Sunday, 7=Saturday
        
        -- Formatted date parts
        FORMAT_DATE('%B', date_day) AS month_name,          -- January, February, etc.
        FORMAT_DATE('%b', date_day) AS month_name_short,    -- Jan, Feb, etc.
        FORMAT_DATE('%A', date_day) AS day_name,            -- Monday, Tuesday, etc.
        FORMAT_DATE('%a', date_day) AS day_name_short,      -- Mon, Tue, etc.
        
        -- Boolean flags for analysis
        CASE 
            WHEN EXTRACT(DAYOFWEEK FROM date_day) IN (1, 7) THEN TRUE  -- Sunday or Saturday
            ELSE FALSE 
        END AS is_weekend,
        
        CASE 
            WHEN EXTRACT(DAYOFWEEK FROM date_day) BETWEEN 2 AND 6 THEN TRUE  -- Monday-Friday
            ELSE FALSE 
        END AS is_weekday,
        
        -- First/last flags for period analysis
        CASE 
            WHEN EXTRACT(DAY FROM date_day) = 1 THEN TRUE 
            ELSE FALSE 
        END AS is_first_day_of_month,
        
        CASE 
            WHEN date_day = LAST_DAY(date_day) THEN TRUE 
            ELSE FALSE 
        END AS is_last_day_of_month,
        
        -- Note: is_public_holiday would require external holiday calendar
        -- For now, we'll use NULL or FALSE
        FALSE AS is_public_holiday

    FROM date_spine
)

SELECT * FROM date_dimension
