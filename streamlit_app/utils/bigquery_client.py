"""
BigQuery Connection Module for Streamlit Dashboard

Handles connection to BigQuery and provides query functions for the dashboard.
"""

import os
from typing import Optional
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
import streamlit as st


@st.cache_resource
def get_bigquery_client() -> bigquery.Client:
    """
    Initialize and cache BigQuery client.
    
    Uses service account credentials from environment variable or
    falls back to default credentials.
    
    Returns:
        bigquery.Client: Authenticated BigQuery client
    """
    credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    project_id = os.getenv('GCP_PROJECT_ID', 'sg-public-transport-pipeline')
    
    if credentials_path:
        # Handle relative paths - resolve from project root
        if not os.path.isabs(credentials_path):
            # Get project root (parent of streamlit_app directory)
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            credentials_path = os.path.join(current_dir, credentials_path)
        
        if os.path.exists(credentials_path):
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path,
                scopes=["https://www.googleapis.com/auth/bigquery"]
            )
            client = bigquery.Client(credentials=credentials, project=project_id)
        else:
            raise FileNotFoundError(
                f"Credentials file not found: {credentials_path}\n"
                f"Please ensure GOOGLE_APPLICATION_CREDENTIALS points to a valid file."
            )
    else:
        # Fall back to default credentials (e.g., gcloud auth)
        client = bigquery.Client(project=project_id)
    
    return client


@st.cache_data(ttl=3600)
def query_bigquery(_client: bigquery.Client, query: str) -> pd.DataFrame:
    """
    Execute a BigQuery query and return results as DataFrame.
    
    Args:
        _client: BigQuery client (prefixed with _ to exclude from hashing)
        query: SQL query string
        
    Returns:
        pd.DataFrame: Query results
    """
    try:
        df = _client.query(query).to_dataframe()
        return df
    except Exception as e:
        st.error(f"Error executing query: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def get_available_months(_client: bigquery.Client, mode: str) -> list:
    """
    Get list of available year_month values for a mode.
    
    Args:
        _client: BigQuery client
        mode: 'Bus' or 'Train'
        
    Returns:
        list: Sorted list of year_month strings (e.g., ['202601', '202602'])
    """
    dataset = os.getenv('BQ_DATASET', 'sg_public_transport_analytics')
    table = 'fact_bus_journeys' if mode == 'Bus' else 'fact_train_journeys'
    
    query = f"""
    SELECT DISTINCT year_month
    FROM `{dataset}.{table}`
    ORDER BY year_month DESC
    """
    
    df = query_bigquery(_client, query)
    return df['year_month'].tolist() if not df.empty else []


@st.cache_data(ttl=3600)
def get_origins(_client: bigquery.Client, mode: str, year_month: str, day_type: str) -> pd.DataFrame:
    """
    Get list of origin locations (stops or stations) with their names.
    
    Args:
        _client: BigQuery client
        mode: 'Bus' or 'Train'
        year_month: Filter by year_month (e.g., '202601')
        day_type: Filter by day_type ('WEEKDAY' or 'WEEKENDS/HOLIDAY')
        
    Returns:
        pd.DataFrame: DataFrame with origin keys and names
    """
    dataset = os.getenv('BQ_DATASET', 'sg_public_transport_analytics')
    
    if mode == 'Bus':
        query = f"""
        SELECT DISTINCT
            f.origin_bus_stop_key,
            CONCAT(d.bus_stop_code, ' - ', d.description) AS origin_name
        FROM `{dataset}.fact_bus_journeys` f
        JOIN `{dataset}.dim_bus_stops` d 
            ON f.origin_bus_stop_key = d.bus_stop_key
        WHERE f.year_month = '{year_month}'
            AND f.day_type = '{day_type}'
        ORDER BY origin_name
        LIMIT 1000
        """
    else:
        query = f"""
        SELECT DISTINCT
            f.origin_station_key,
            CONCAT(d.station_code, ' - ', d.station_name) AS origin_name
        FROM `{dataset}.fact_train_journeys` f
        JOIN `{dataset}.dim_train_stations` d 
            ON f.origin_station_key = d.station_key
        WHERE f.year_month = '{year_month}'
            AND f.day_type = '{day_type}'
        ORDER BY origin_name
        """
    
    return query_bigquery(_client, query)


@st.cache_data(ttl=3600)
def get_trip_count_by_origin(
    _client: bigquery.Client,
    mode: str,
    year_month: str,
    day_type: str,
    origin_filter: Optional[list] = None,
    top_n: int = 20
) -> pd.DataFrame:
    """
    Get trip counts aggregated by origin location.
    
    Args:
        _client: BigQuery client
        mode: 'Bus' or 'Train'
        year_month: Filter by year_month
        day_type: Filter by day_type
        origin_filter: Optional list of origin keys to filter
        top_n: Return top N origins by trip count
        
    Returns:
        pd.DataFrame: Origin location, name, and total trip count
    """
    dataset = os.getenv('BQ_DATASET', 'sg_public_transport_analytics')
    
    if mode == 'Bus':
        origin_key = 'origin_bus_stop_key'
        dim_table = 'dim_bus_stops'
        dim_key = 'bus_stop_key'
        name_col = "CONCAT(d.bus_stop_code, ' - ', d.description)"
        fact_table = 'fact_bus_journeys'
    else:
        origin_key = 'origin_station_key'
        dim_table = 'dim_train_stations'
        dim_key = 'station_key'
        name_col = "CONCAT(d.station_code, ' - ', d.station_name)"
        fact_table = 'fact_train_journeys'
    
    where_clause = f"f.year_month = '{year_month}' AND f.day_type = '{day_type}'"
    
    if origin_filter and len(origin_filter) > 0:
        origins_str = "','".join(origin_filter)
        where_clause += f" AND f.{origin_key} IN ('{origins_str}')"
    
    query = f"""
    SELECT
        f.{origin_key} AS origin_key,
        {name_col} AS origin_name,
        SUM(f.trip_count) AS total_trips
    FROM `{dataset}.{fact_table}` f
    JOIN `{dataset}.{dim_table}` d 
        ON f.{origin_key} = d.{dim_key}
    WHERE {where_clause}
    GROUP BY f.{origin_key}, origin_name
    ORDER BY total_trips DESC
    LIMIT {top_n}
    """
    
    return query_bigquery(_client, query)


@st.cache_data(ttl=3600)
def get_trip_count_by_time_period(
    _client: bigquery.Client,
    mode: str,
    year_month: str,
    day_type: str,
    origin_filter: Optional[list] = None
) -> pd.DataFrame:
    """
    Get trip counts aggregated by time period (hour).
    
    Args:
        _client: BigQuery client
        mode: 'Bus' or 'Train'
        year_month: Filter by year_month
        day_type: Filter by day_type
        origin_filter: Optional list of origin keys to filter
        
    Returns:
        pd.DataFrame: Time period details and trip counts
    """
    dataset = os.getenv('BQ_DATASET', 'sg_public_transport_analytics')
    
    if mode == 'Bus':
        origin_key = 'origin_bus_stop_key'
        fact_table = 'fact_bus_journeys'
    else:
        origin_key = 'origin_station_key'
        fact_table = 'fact_train_journeys'
    
    where_clause = f"f.year_month = '{year_month}' AND f.day_type = '{day_type}'"
    
    if origin_filter and len(origin_filter) > 0:
        origins_str = "','".join(origin_filter)
        where_clause += f" AND f.{origin_key} IN ('{origins_str}')"
    
    query = f"""
    SELECT
        t.time_period_key,
        t.hour,
        t.time_period_name,
        t.is_peak_hour,
        SUM(f.trip_count) AS total_trips
    FROM `{dataset}.{fact_table}` f
    JOIN `{dataset}.dim_time_period` t 
        ON f.time_period_key = t.time_period_key
    WHERE {where_clause}
    GROUP BY t.time_period_key, t.hour, t.time_period_name, t.is_peak_hour
    ORDER BY t.time_period_key
    """
    
    return query_bigquery(_client, query)
