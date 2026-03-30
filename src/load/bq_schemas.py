"""
Module: bq_schemas.py
Purpose: Define BigQuery table schemas for raw/staging data.
         These schemas match the structure of CSV files from LTA API.

Why this exists:
- BigQuery needs to know data types and field names before loading data
- Schemas define how data should be stored and what types to use
- Having schemas in code makes them version-controlled and reproducible

This is part of Phase 4: BigQuery Schema & Load
For Phase 5, dbt will transform these raw tables into dimensional models.

Author: Joseph Emmanuel Remoto
Date: 2026-03-30
"""

# Import BigQuery schema definition classes
# SchemaField = defines one column in a BigQuery table
from google.cloud import bigquery


# =============================================================================
# Schema Definitions
# =============================================================================
# Each schema is a list of SchemaField objects
# SchemaField(name, field_type, mode)
# - name: column name (matches CSV header)
# - field_type: data type (STRING, INTEGER, FLOAT, DATE, TIMESTAMP, etc.)
# - mode: NULLABLE (can be empty), REQUIRED (cannot be empty), REPEATED (array)
# =============================================================================


def get_bus_stops_schema() -> list[bigquery.SchemaField]:
    """
    Schema for bus_stops table (reference/dimension data).
    
    This table stores static information about all bus stops in Singapore.
    Data comes from: /BusStops API endpoint
    Updates: Ad-hoc (infrequent) - bus stops don't change often
    
    Fields:
    - BusStopCode: Unique 5-digit identifier for each bus stop (e.g., "01012")
    - RoadName: Name of the road where bus stop is located
    - Description: Human-readable description (usually nearby landmark)
    - Latitude: Geographic coordinate (north-south position)
    - Longitude: Geographic coordinate (east-west position)
    
    Returns:
        list[SchemaField]: BigQuery schema definition
        
    Example row:
        BusStopCode: "01012"
        RoadName: "Victoria St"
        Description: "Hotel Grand Pacific"
        Latitude: 1.29684825487647
        Longitude: 103.85253591654006
    """
    return [
        bigquery.SchemaField(
            "BusStopCode", 
            "STRING", 
            mode="REQUIRED",  # Every bus stop must have a code
            description="5-digit unique bus stop identifier"
        ),
        bigquery.SchemaField(
            "RoadName", 
            "STRING", 
            mode="NULLABLE",  # Some stops might not have road name
            description="Name of the road where bus stop is located"
        ),
        bigquery.SchemaField(
            "Description", 
            "STRING", 
            mode="NULLABLE",
            description="Human-readable description (usually nearby landmark)"
        ),
        bigquery.SchemaField(
            "Latitude", 
            "FLOAT64",  # FLOAT64 = double-precision decimal number
            mode="REQUIRED",
            description="Geographic latitude coordinate"
        ),
        bigquery.SchemaField(
            "Longitude", 
            "FLOAT64", 
            mode="REQUIRED",
            description="Geographic longitude coordinate"
        ),
    ]


def get_train_stations_schema() -> list[bigquery.SchemaField]:
    """
    Schema for train_stations table (reference/dimension data).
    
    This table stores static information about all MRT/LRT stations in Singapore.
    Data comes from: Excel file download from LTA DataMall Portal
    Updates: Ad-hoc (infrequent) - new stations added when lines open
    
    Fields:
    - stn_code: Station code used in OD data (e.g., "NS1", "EW12")
    - mrt_station_english: Official English name of station
    - mrt_station_chinese: Chinese name of station
    - mrt_line_english: Line that station belongs to (e.g., "North South Line")
    
    Returns:
        list[SchemaField]: BigQuery schema definition
        
    Example row:
        stn_code: "NS1"
        mrt_station_english: "Jurong East"
        mrt_station_chinese: "裕廊东"
        mrt_line_english: "North South Line"
    """
    return [
        bigquery.SchemaField(
            "stn_code", 
            "STRING", 
            mode="REQUIRED",
            description="Station code used in origin-destination data (e.g., NS1, EW12)"
        ),
        bigquery.SchemaField(
            "mrt_station_english", 
            "STRING", 
            mode="REQUIRED",
            description="Official English name of MRT/LRT station"
        ),
        bigquery.SchemaField(
            "mrt_station_chinese", 
            "STRING", 
            mode="NULLABLE",  # Some stations might not have Chinese name
            description="Chinese name of station"
        ),
        bigquery.SchemaField(
            "mrt_line_english", 
            "STRING", 
            mode="REQUIRED",
            description="Name of the MRT/LRT line (e.g., North South Line)"
        ),
    ]


def get_bus_od_schema() -> list[bigquery.SchemaField]:
    """
    Schema for bus_od (origin-destination) table - monthly passenger flow data.
    
    This is FACT data - records of aggregated passenger journeys.
    Data comes from: /PV/ODBus?Date=YYYYMM API endpoint
    Updates: Monthly (by 10th of month for previous month's data)
    
    Fields:
    - YEAR_MONTH: Period identifier (YYYYMM format, e.g., "202601")
    - DAY_TYPE: Whether data is for weekdays or weekends/holidays
    - TIME_PER_HOUR: Hour of day when journey started (0-23)
    - PT_TYPE: Public transport type (always "BUS" for this table)
    - ORIGIN_PT_CODE: Bus stop code where journey started
    - DESTINATION_PT_CODE: Bus stop code where journey ended
    - TOTAL_TRIPS: Number of passenger trips for this combination
    
    Grain: One row per unique combination of month-day_type-hour-origin-destination
    
    Returns:
        list[SchemaField]: BigQuery schema definition
        
    Example row:
        YEAR_MONTH: "202601"
        DAY_TYPE: "WEEKDAY"
        TIME_PER_HOUR: 8
        PT_TYPE: "BUS"
        ORIGIN_PT_CODE: "01012"
        DESTINATION_PT_CODE: "83139"
        TOTAL_TRIPS: 145
        
    Interpretation: In January 2026, during weekday 8AM hours, 
    145 passenger trips went from bus stop 01012 to bus stop 83139.
    """
    return [
        bigquery.SchemaField(
            "YEAR_MONTH", 
            "STRING",  # Could also be INTEGER, but STRING is safer for leading zeros
            mode="REQUIRED",
            description="Year and month in YYYYMM format (e.g., 202601 for January 2026)"
        ),
        bigquery.SchemaField(
            "DAY_TYPE", 
            "STRING", 
            mode="REQUIRED",
            description="Type of day: WEEKDAY or WEEKENDS/HOLIDAY"
        ),
        bigquery.SchemaField(
            "TIME_PER_HOUR", 
            "INTEGER",  # INTEGER = whole number
            mode="REQUIRED",
            description="Hour of day when journey started (0-23, where 0 = midnight, 23 = 11 PM)"
        ),
        bigquery.SchemaField(
            "PT_TYPE", 
            "STRING", 
            mode="REQUIRED",
            description="Public transport type (BUS for this table)"
        ),
        bigquery.SchemaField(
            "ORIGIN_PT_CODE", 
            "STRING", 
            mode="REQUIRED",
            description="Bus stop code where passenger journey originated"
        ),
        bigquery.SchemaField(
            "DESTINATION_PT_CODE", 
            "STRING", 
            mode="REQUIRED",
            description="Bus stop code where passenger journey ended"
        ),
        bigquery.SchemaField(
            "TOTAL_TRIPS", 
            "INTEGER", 
            mode="REQUIRED",
            description="Aggregate count of passenger trips for this origin-destination-hour combination"
        ),
    ]


def get_train_od_schema() -> list[bigquery.SchemaField]:
    """
    Schema for train_od (origin-destination) table - monthly passenger flow data.
    
    This is FACT data - records of aggregated passenger journeys.
    Data comes from: /PV/ODTrain?Date=YYYYMM API endpoint
    Updates: Monthly (by 10th of month for previous month's data)
    
    Same structure as bus_od, but for train (MRT/LRT) journeys.
    
    Fields: (same as bus_od_schema, but PT_TYPE = "TRAIN" and codes are station codes)
    - YEAR_MONTH: Period identifier (YYYYMM format)
    - DAY_TYPE: WEEKDAY or WEEKENDS/HOLIDAY
    - TIME_PER_HOUR: Hour of day (0-23)
    - PT_TYPE: Always "TRAIN" for this table
    - ORIGIN_PT_CODE: Station code where journey started (e.g., "NS1")
    - DESTINATION_PT_CODE: Station code where journey ended (e.g., "EW12")
    - TOTAL_TRIPS: Number of passenger trips
    
    Grain: One row per unique combination of month-day_type-hour-origin-destination
    
    Returns:
        list[SchemaField]: BigQuery schema definition
        
    Example row:
        YEAR_MONTH: "202601"
        DAY_TYPE: "WEEKDAY"
        TIME_PER_HOUR: 8
        PT_TYPE: "TRAIN"
        ORIGIN_PT_CODE: "NS1"
        DESTINATION_PT_CODE: "NS24"
        TOTAL_TRIPS: 1250
        
    Interpretation: In January 2026, during weekday 8AM hours,
    1,250 passenger trips went from Jurong East (NS1) to Yishun (NS13).
    """
    # Train OD has same schema as Bus OD
    # The only difference is PT_TYPE value and what codes represent
    return get_bus_od_schema()


# =============================================================================
# Schema Registry
# =============================================================================
# Dictionary mapping table names to their schema functions
# This makes it easy to look up schemas programmatically
# =============================================================================

SCHEMAS = {
    'bus_stops': get_bus_stops_schema,
    'train_stations': get_train_stations_schema,
    'bus_od': get_bus_od_schema,
    'train_od': get_train_od_schema,
}


def get_schema(table_name: str) -> list[bigquery.SchemaField]:
    """
    Get the BigQuery schema for a given table name.
    
    This is a convenience function that looks up and returns the schema
    for any table in our data model.
    
    Parameters:
        table_name (str): Name of the table (e.g., 'bus_stops', 'train_od')
        
    Returns:
        list[SchemaField]: BigQuery schema definition
        
    Raises:
        ValueError: If table_name is not recognized
        
    Example:
        schema = get_schema('bus_stops')
        # Returns the bus stops schema
    """
    if table_name not in SCHEMAS:
        available = ', '.join(SCHEMAS.keys())
        raise ValueError(
            f"Unknown table name: '{table_name}'\n"
            f"Available tables: {available}"
        )
    
    # Call the schema function and return the result
    schema_function = SCHEMAS[table_name]
    return schema_function()
