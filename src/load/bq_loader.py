"""
Module: bq_loader.py
Purpose: Load data from Google Cloud Storage into BigQuery tables.
         Handles table creation, schema management, and data loading.

Why this exists:
- Automates the process of getting data from GCS into BigQuery for analysis
- Creates tables if they don't exist (with proper schemas)
- Loads data files from GCS buckets into BigQuery tables (JSON for reference, CSV for OD)
- Handles partitioning and clustering for performance

This is part of Phase 4: BigQuery Schema & Load
After loading, dbt (Phase 5) will transform this raw data into dimensional models.

Author: Joseph Emmanuel Remoto
Date: 2026-03-30
Dependencies: google-cloud-bigquery, google-cloud-storage
"""

# Import statements
import logging  # For logging progress and errors
from pathlib import Path  # For working with file paths
from typing import Optional  # Type hints for optional parameters

# Google Cloud libraries
from google.cloud import bigquery  # BigQuery client
from google.cloud import storage  # GCS client (for listing files)
from google.cloud.exceptions import NotFound  # Exception when resource doesn't exist

# Our custom modules
from src.config.settings import Config  # Configuration
from src.load.bq_schemas import get_schema  # Schema definitions


# Set up logging
# This lets us see what the script is doing in real-time
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BigQueryLoader:
    """
    Class for loading data from GCS into BigQuery.
    
    This class handles:
    1. Creating BigQuery tables if they don't exist
    2. Loading data files (JSON for reference, CSV for OD) from GCS into BigQuery
    3. Managing table schemas and configurations
    
    The loader assumes data files are already in GCS (uploaded in Phase 3).
    
    Attributes:
        project_id (str): Google Cloud project ID
        dataset_id (str): BigQuery dataset name
        location (str): Geographic location for BigQuery (e.g., 'asia-southeast1')
        bq_client (bigquery.Client): Authenticated BigQuery client
        gcs_client (storage.Client): Authenticated GCS client
        
    Example:
        # Create loader instance
        loader = BigQueryLoader()
        
        # Load bus stops data (JSON)
        loader.load_reference_data('bus_stops')
        
        # Load bus OD data for January 2026 (CSV)
        loader.load_od_data('bus', '202601')
    """
    
    def __init__(
        self,
        project_id: Optional[str] = None,
        dataset_id: Optional[str] = None,
        location: Optional[str] = None
    ):
        """
        Initialize BigQuery loader with GCP credentials and configuration.
        
        Parameters:
            project_id (str, optional): GCP project ID. Uses Config.GCP_PROJECT_ID if not provided.
            dataset_id (str, optional): BigQuery dataset. Uses Config.BQ_DATASET if not provided.
            location (str, optional): BigQuery location. Uses Config.BQ_LOCATION if not provided.
            
        The constructor creates authenticated clients for BigQuery and GCS.
        It uses GOOGLE_APPLICATION_CREDENTIALS environment variable for authentication.
        """
        # Load configuration from environment variables (via Config class)
        self.project_id = project_id or Config.GCP_PROJECT_ID
        self.dataset_id = dataset_id or Config.BQ_DATASET
        self.location = location or Config.BQ_LOCATION
        
        # Validate that we have required configuration
        if not self.project_id:
            raise ValueError("GCP_PROJECT_ID must be set in environment or passed as parameter")
        if not self.dataset_id:
            raise ValueError("BQ_DATASET must be set in environment or passed as parameter")
        
        # Create authenticated clients
        # These clients use GOOGLE_APPLICATION_CREDENTIALS automatically
        logger.info(f"Initializing BigQuery client for project: {self.project_id}")
        self.bq_client = bigquery.Client(project=self.project_id, location=self.location)
        self.gcs_client = storage.Client(project=self.project_id)
        
        logger.info(f"BigQuery Loader initialized - Dataset: {self.dataset_id}, Location: {self.location}")
    
    
    def ensure_dataset_exists(self) -> None:
        """
        Create BigQuery dataset if it doesn't already exist.
        
        A dataset in BigQuery is like a database schema - it groups related tables.
        This method checks if the dataset exists, and creates it if needed.
        
        The dataset is created with:
        - Location matching the configured region
        - Default table expiration: None (tables don't auto-delete)
        - Description explaining the dataset purpose
        
        This is idempotent - safe to call multiple times.
        """
        # Construct full dataset ID (format: project.dataset)
        dataset_ref = f"{self.project_id}.{self.dataset_id}"
        
        try:
            # Try to get the dataset (will raise NotFound if doesn't exist)
            self.bq_client.get_dataset(dataset_ref)
            logger.info(f"✓ Dataset already exists: {dataset_ref}")
            
        except NotFound:
            # Dataset doesn't exist, so create it
            logger.info(f"Creating dataset: {dataset_ref}")
            
            # Configure the dataset
            dataset = bigquery.Dataset(dataset_ref)
            dataset.location = self.location  # Must match data location for best performance
            dataset.description = (
                "Data for Singapore LTA Public Transport Pipeline. "
                "Data sourced from LTA DataMall API. "
            )
            
            # Create the dataset
            dataset = self.bq_client.create_dataset(dataset, exists_ok=True)
            logger.info(f"✓ Created dataset: {dataset.dataset_id}")
    
    
    def create_table_if_not_exists(
        self,
        table_name: str,
        partition_field: Optional[str] = None
    ) -> None:
        """
        Create a BigQuery table if it doesn't already exist.
        
        This method:
        1. Gets the schema definition for the table
        2. Checks if table exists (creates if not)
        3. Optionally sets up partitioning for performance
        
        Parameters:
            table_name (str): Name of table to create (e.g., 'bus_stops', 'train_od')
            partition_field (str, optional): Field name to partition by (for large tables)
                                            Partitioning improves query performance and reduces costs
                                            
        Partitioning explanation:
            - Partitioning divides a table into segments based on a field value
            - Queries only scan relevant partitions (faster & cheaper)
            - Best for tables with time-series data or tables that grow large
            - Example: Partitioning by YEAR_MONTH means January data is separate from February
            
        Example:
            # Create reference table (no partitioning needed - small & static)
            loader.create_table_if_not_exists('bus_stops')
            
            # Create OD table with partitioning (large & grows monthly)
            loader.create_table_if_not_exists('bus_od', partition_field='YEAR_MONTH')
        """
        # Construct full table ID (format: project.dataset.table)
        table_ref = f"{self.project_id}.{self.dataset_id}.{table_name}"
        
        try:
            # Check if table already exists
            self.bq_client.get_table(table_ref)
            logger.info(f"✓ Table already exists: {table_ref}")
            return
            
        except NotFound:
            # Table doesn't exist, so create it
            logger.info(f"Creating table: {table_ref}")
            
            # Get schema definition for this table
            schema = get_schema(table_name)
            
            # Configure the table
            table = bigquery.Table(table_ref, schema=schema)
            table.description = f"Raw data for {table_name} from LTA DataMall API"
            
            # Set up partitioning if requested
            if partition_field:
                # Partitioning on a STRING field (like YEAR_MONTH)
                # This is called "RANGE partitioning" in BigQuery
                # However, for simplicity, we'll use clustering instead for STRING fields
                # Clustering is similar to partitioning but more flexible for non-date fields
                table.clustering_fields = [partition_field]
                logger.info(f"  - Clustering enabled on field: {partition_field}")
            
            # Create the table
            table = self.bq_client.create_table(table)
            logger.info(f"✓ Created table: {table.table_id}")
    
    
    def load_reference_data(
        self,
        table_name: str,
        gcs_uri: Optional[str] = None
    ) -> None:
        """
        Load reference/dimension data from GCS (NDJSON format) into BigQuery.
        
        Reference data = static data that doesn't change often
        Examples: bus_stops, train_stations
        
        This method loads from GCS NDJSON files (newline-delimited JSON).
        NDJSON format is optimized for BigQuery loading - each line is a JSON object.
        
        This method:
        1. Ensures dataset exists
        2. Creates table if needed
        3. Loads NDJSON file from GCS into BigQuery
        4. Uses WRITE_TRUNCATE mode (replaces all existing data)
        
        Parameters:
            table_name (str): Name of table ('bus_stops' or 'train_stations')
            gcs_uri (str, optional): Full GCS URI to NDJSON file
                                    Format: gs://bucket-name/path/to/file.ndjson
                                    If not provided, uses standard naming convention
                                    
        Example:
            # Load bus stops (auto-detects GCS path)
            loader.load_reference_data('bus_stops')
            
            # Load with explicit GCS path
            loader.load_reference_data(
                'train_stations',
                gcs_uri='gs://my-bucket/reference/train_stations.ndjson'
            )
        """
        logger.info(f"Loading reference data for table: {table_name}")
        
        # Step 1: Ensure dataset exists
        self.ensure_dataset_exists()
        
        # Step 2: Create table if it doesn't exist
        self.create_table_if_not_exists(table_name)
        
        # Step 3: Determine source file location in GCS
        if not gcs_uri:
            # Use standard naming convention
            # Reference files are stored at: gs://bucket/reference/{table_name}.ndjson
            bucket_name = Config.GCS_BUCKET_RAW
            gcs_uri = f"gs://{bucket_name}/reference/{table_name}.ndjson"
        
        logger.info(f"  Source: {gcs_uri}")
        
        # Step 4: Configure load job
        table_ref = f"{self.project_id}.{self.dataset_id}.{table_name}"
        
        job_config = bigquery.LoadJobConfig(
            # Schema configuration
            schema=get_schema(table_name),  # Use our defined schema
            autodetect=False,  # Don't auto-detect schema (we specify it explicitly)
            
            # Source format - NDJSON (newline-delimited JSON)
            source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
            
            # Write mode
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
            # WRITE_TRUNCATE = delete all existing rows and load new data
            # This is appropriate for reference data that is fully replaced each time
        )
        
        # Step 5: Start load job
        logger.info(f"  Starting load job for {table_name}...")
        load_job = self.bq_client.load_table_from_uri(
            gcs_uri,
            table_ref,
            job_config=job_config
        )
        
        # Wait for job to complete
        # This blocks until the load finishes (or fails)
        load_job.result()  # Raises exception if job failed
        
        # Step 6: Report success
        destination_table = self.bq_client.get_table(table_ref)
        logger.info(
            f"✓ Successfully loaded {destination_table.num_rows:,} rows into "
            f"{self.dataset_id}.{table_name}"
        )
    
    
    def load_od_data(
        self,
        mode: str,
        year_month: str,
        gcs_uri: Optional[str] = None
    ) -> None:
        """
        Load origin-destination (OD) data from GCS into BigQuery.
        
        OD data = passenger journey data (facts)
        Examples: bus_od, train_od
        This data grows each month as new data is added.
        
        This method:
        1. Ensures dataset exists
        2. Creates table if needed (with clustering on YEAR_MONTH)
        3. Loads CSV file from GCS into table
        4. Uses WRITE_APPEND mode (adds to existing data without deleting)
        
        Parameters:
            mode (str): Transport mode ('bus' or 'train')
            year_month (str): Period in YYYYMM format (e.g., '202601' for January 2026)
            gcs_uri (str, optional): Full GCS URI to CSV file
                                    If not provided, uses standard naming convention
                                    
        Example:
            # Load bus OD data for January 2026
            loader.load_od_data('bus', '202601')
            
            # Load train OD data with explicit path
            loader.load_od_data(
                'train',
                '202601',
                gcs_uri='gs://my-bucket/journeys/train/2026/01/train_od_202601.csv'
            )
        """
        # Validate mode
        if mode not in ['bus', 'train']:
            raise ValueError(f"Invalid mode: {mode}. Must be 'bus' or 'train'")
        
        table_name = f"{mode}_od"
        logger.info(f"Loading OD data for {mode} - {year_month}")
        
        # Step 1: Ensure dataset exists
        self.ensure_dataset_exists()
        
        # Step 2: Create table if it doesn't exist
        # Use clustering on YEAR_MONTH for query performance
        self.create_table_if_not_exists(table_name, partition_field='YEAR_MONTH')
        
        # Step 3: Determine source file location
        if not gcs_uri:
            # Use standard naming convention
            # OD files are stored at: gs://bucket/journeys/{mode}/{year}/{month}/{mode}_od_{year_month}.csv
            # Example: gs://bucket/journeys/bus/2026/01/bus_od_202601.csv
            bucket_name = Config.GCS_BUCKET_RAW
            year = year_month[:4]  # Extract year (e.g., '2026' from '202601')
            month = year_month[4:6]  # Extract month (e.g., '01' from '202601')
            gcs_uri = f"gs://{bucket_name}/journeys/{mode}/{year}/{month}/{mode}_od_{year_month}.csv"
        
        logger.info(f"  Source: {gcs_uri}")
        
        # Step 4: Configure load job
        table_ref = f"{self.project_id}.{self.dataset_id}.{table_name}"
        
        job_config = bigquery.LoadJobConfig(
            # Schema configuration
            schema=get_schema(table_name),
            autodetect=False,
            
            # Source format
            source_format=bigquery.SourceFormat.CSV,
            skip_leading_rows=1,  # Skip CSV header
            field_delimiter=',',
            
            # Write mode
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND,  # Add to existing data
            # WRITE_APPEND = keep existing rows and add new rows
            # This allows us to load multiple months incrementally
            
            # Prevent duplicate loads (optional but recommended)
            # If you try to load the same data twice, this will make the job fail
            # instead of creating duplicates
            # Note: This requires a truly unique combination of fields
        )
        
        # Step 5: Start load job
        logger.info(f"  Starting load job for {table_name} ({year_month})...")
        load_job = self.bq_client.load_table_from_uri(
            gcs_uri,
            table_ref,
            job_config=job_config
        )
        
        # Wait for job to complete
        load_job.result()
        
        # Step 6: Report success
        destination_table = self.bq_client.get_table(table_ref)
        logger.info(
            f"✓ Loaded data into {self.dataset_id}.{table_name} "
            f"(total rows now: {destination_table.num_rows:,})"
        )
    
    
    def load_all_od_data(self, mode: str, start_year_month: str, end_year_month: str) -> None:
        """
        Load multiple months of OD data in sequence.
        
        This is a convenience method for bulk loading historical data.
        It iterates through a range of year-months and loads each one.
        
        Parameters:
            mode (str): Transport mode ('bus' or 'train')
            start_year_month (str): First month to load (YYYYMM)
            end_year_month (str): Last month to load (YYYYMM)
            
        Example:
            # Load bus data from December 2025 through February 2026
            loader.load_all_od_data('bus', '202512', '202602')
            # This will load: 202512, 202601, 202602
        """
        logger.info(f"Loading {mode} OD data from {start_year_month} to {end_year_month}")
        
        # Generate list of year-months in range
        # For simplicity, we'll assume consecutive months
        # In production, you'd use a proper date library to handle this
        year_months = generate_year_month_range(start_year_month, end_year_month)
        
        for year_month in year_months:
            try:
                self.load_od_data(mode, year_month)
            except Exception as e:
                logger.error(f"Failed to load {mode} data for {year_month}: {e}")
                # Continue with next month instead of failing completely
                continue
        
        logger.info(f"✓ Completed loading {mode} OD data")


# =============================================================================
# Utility Functions
# =============================================================================

def generate_year_month_range(start: str, end: str) -> list[str]:
    """
    Generate a list of year-month strings between start and end (inclusive).
    
    Parameters:
        start (str): Start year-month in YYYYMM format
        end (str): End year-month in YYYYMM format
        
    Returns:
        list[str]: List of year-month strings in YYYYMM format
        
    Example:
        generate_year_month_range('202512', '202602')
        # Returns: ['202512', '202601', '202602']
        
    Note: This is a simplified implementation that assumes consecutive months.
    For production, consider using dateutil or pandas for more robust date handling.
    """
    from datetime import datetime
    from dateutil.relativedelta import relativedelta
    
    # Parse start and end dates
    start_date = datetime.strptime(start, '%Y%m')
    end_date = datetime.strptime(end, '%Y%m')
    
    # Generate list of dates
    year_months = []
    current_date = start_date
    
    while current_date <= end_date:
        year_months.append(current_date.strftime('%Y%m'))
        current_date += relativedelta(months=1)  # Add one month
    
    return year_months
