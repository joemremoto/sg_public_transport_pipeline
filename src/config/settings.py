"""
Module: settings.py
Purpose: Centralized configuration management for the LTA Data Pipeline.
         This module loads environment variables from .env file and validates them.

Why this exists:
- Keeps all configuration in one place (single source of truth)
- Validates that required environment variables are set before the app runs
- Provides helpful error messages if configuration is missing
- Makes code cleaner (import Config instead of calling os.getenv everywhere)

This is part of the Singapore Public Transport Analytics Pipeline.
Reference: See .env.example for all available configuration options
"""

# Import statements - These are libraries we need to work with environment variables
import os  # os = operating system, provides access to environment variables
from pathlib import Path  # Path = modern way to work with file paths in Python
from typing import Optional  # Optional = type hint that means "this can be None"
from dotenv import load_dotenv # dotenv library - loads variables from .env file into environment


# Find and load the .env file
# __file__ = path to this current Python file (settings.py)
# .parent = go up one directory level (from src/config/ to src/)
# .parent again = go up another level (from src/ to project root)
# This works no matter where the script is run from
project_root = Path(__file__).parent.parent.parent
env_file_path = project_root / '.env'

# load_dotenv() reads the .env file and makes variables available via os.getenv()
# If .env doesn't exist, it fails silently (doesn't crash)
load_dotenv(dotenv_path=env_file_path)


class Config:
    """
    Configuration class that holds all application settings.
    
    This class loads environment variables and provides them as class attributes.
    Instead of calling os.getenv() throughout your code, you import and use Config.
    
    Usage:
        from src.config.settings import Config
        
        # Access configuration values
        api_key = Config.LTA_ACCOUNT_KEY
        project_id = Config.GCP_PROJECT_ID
    
    All values are loaded when the module is first imported.
    The validate() method checks that required values exist.
    """
    
    # =========================================================================
    # LTA API Configuration
    # =========================================================================
    
    # Your LTA DataMall API key for authentication
    # This is REQUIRED - the pipeline cannot run without it
    # Get your key from: https://datamall.lta.gov.sg
    LTA_ACCOUNT_KEY: Optional[str] = os.getenv('LTA_ACCOUNT_KEY')
    
    # Base URL for LTA DataMall API
    # This is the main endpoint that all API calls start with
    # We hardcode this because it never changes
    LTA_BASE_URL: str = 'http://datamall2.mytransport.sg/ltaodataservice'
    
    # API request timeout in seconds
    # How long to wait for API response before giving up
    # 30 seconds is reasonable for data downloads
    LTA_API_TIMEOUT: int = 30
    
    # =========================================================================
    # Google Cloud Platform Configuration
    # =========================================================================
    
    # Path to GCP service account credentials JSON file
    # This file contains the private key for authenticating to GCP
    # Example: ./credentials/gcp-service-account.json
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    
    # Your Google Cloud Project ID
    # This identifies which GCP project to use
    # Example: my-project-12345
    GCP_PROJECT_ID: Optional[str] = os.getenv('GCP_PROJECT_ID')
    
    # GCP region for resources (buckets, BigQuery datasets)
    # Default: asia-southeast1 (Singapore region - closest to data source)
    GCP_REGION: str = os.getenv('GCP_REGION', 'asia-southeast1')
    
    # =========================================================================
    # Google Cloud Storage Configuration
    # =========================================================================
    
    # GCS bucket name for storing raw data files
    # This is where we upload CSV files from LTA API
    # Must be globally unique across all of GCP
    GCS_BUCKET_RAW: Optional[str] = os.getenv('GCS_BUCKET')
    
    # GCS bucket for processed/transformed data (optional - can use same bucket)
    # If not set, we'll use the same bucket as raw data
    GCS_BUCKET_PROCESSED: Optional[str] = os.getenv('GCS_BUCKET_PROCESSED', 
                                                     os.getenv('GCS_BUCKET'))
    
    # =========================================================================
    # BigQuery Configuration
    # =========================================================================
    
    # BigQuery dataset name where tables will be created
    # A dataset is like a database schema - groups related tables together
    # Example: lta_analytics, public_transport, etc.
    BQ_DATASET: Optional[str] = os.getenv('BQ_DATASET')
    
    # BigQuery table location (should match GCP_REGION for best performance)
    BQ_LOCATION: str = os.getenv('BQ_LOCATION', os.getenv('GCP_REGION', 'asia-southeast1'))
    
    # =========================================================================
    # Local Storage Paths
    # =========================================================================
    
    # Base directory for local data storage (for development/testing)
    # In production, data will go to GCS instead
    # Path is relative to project root
    DATA_DIR: Path = project_root / 'data'
    
    # Directory for raw data files (as downloaded from API)
    RAW_DATA_DIR: Path = DATA_DIR / 'raw'
    
    # Directory for processed/cleaned data
    PROCESSED_DATA_DIR: Path = DATA_DIR / 'processed'
    
    # =========================================================================
    # Pipeline Configuration
    # =========================================================================
    
    # Modes of transport to process
    # List of transport types the pipeline should handle
    TRANSPORT_MODES: list[str] = ['bus', 'train']
    
    # Whether to save data locally (useful for development)
    # Set to False in production to save only to GCS
    SAVE_LOCAL: bool = os.getenv('SAVE_LOCAL', 'true').lower() == 'true'
    
    # =========================================================================
    # Validation Methods
    # =========================================================================
    
    @classmethod
    def validate(cls) -> None:
        """
        Validate that all required configuration variables are set.
        
        This method checks that essential environment variables exist and
        provides helpful error messages if anything is missing.
        
        Call this at application startup to fail fast if config is incomplete.
        
        Raises:
            ValueError: If any required configuration is missing
            
        Example:
            from src.config.settings import Config
            
            # Validate configuration at startup
            Config.validate()
            # If this doesn't raise an error, config is good!
        """
        errors = []  # List to collect all error messages
        
        # Check LTA API Key (REQUIRED for pipeline to work)
        if not cls.LTA_ACCOUNT_KEY:
            errors.append(
                "❌ LTA_ACCOUNT_KEY is not set!\n"
                "   Get your API key from: https://datamall.lta.gov.sg\n"
                "   Then add it to your .env file: LTA_ACCOUNT_KEY=your_key_here"
            )
        
        # Check GCP Project ID (REQUIRED for cloud operations)
        if not cls.GCP_PROJECT_ID:
            errors.append(
                "❌ GCP_PROJECT_ID is not set!\n"
                "   This is your Google Cloud project identifier.\n"
                "   Add it to your .env file: GCP_PROJECT_ID=your-project-id"
            )
        
        # Check GCP Credentials Path (REQUIRED for authenticating to GCP)
        if not cls.GOOGLE_APPLICATION_CREDENTIALS:
            errors.append(
                "❌ GOOGLE_APPLICATION_CREDENTIALS is not set!\n"
                "   This should point to your service account JSON key file.\n"
                "   Add it to your .env file: GOOGLE_APPLICATION_CREDENTIALS=./credentials/gcp-service-account.json"
            )
        elif not Path(cls.GOOGLE_APPLICATION_CREDENTIALS).exists():
            # Path is set, but file doesn't exist
            errors.append(
                f"❌ GCP credentials file not found!\n"
                f"   Looking for: {cls.GOOGLE_APPLICATION_CREDENTIALS}\n"
                f"   Make sure you've downloaded your service account key and placed it at this path."
            )
        
        # Check GCS Bucket (REQUIRED for storing data in cloud)
        if not cls.GCS_BUCKET_RAW:
            errors.append(
                "❌ GCS_BUCKET is not set!\n"
                "   This is the Google Cloud Storage bucket for storing raw data.\n"
                "   Add it to your .env file: GCS_BUCKET=your-bucket-name"
            )
        
        # Check BigQuery Dataset (REQUIRED for data warehouse)
        if not cls.BQ_DATASET:
            errors.append(
                "❌ BQ_DATASET is not set!\n"
                "   This is the BigQuery dataset where tables will be created.\n"
                "   Add it to your .env file: BQ_DATASET=your_dataset_name"
            )
        
        # If we found any errors, raise exception with all messages combined
        if errors:
            error_message = "\n\n".join(errors)
            raise ValueError(
                f"\n\n{'='*70}\n"
                f"⚠️  CONFIGURATION ERROR ⚠️\n"
                f"{'='*70}\n\n"
                f"{error_message}\n\n"
                f"{'='*70}\n"
                f"Fix these issues in your .env file and try again.\n"
                f"See .env.example for reference.\n"
                f"{'='*70}\n"
            )
    
    @classmethod
    def create_local_directories(cls) -> None:
        """
        Create local data directories if they don't exist.
        
        This is useful for development when testing locally before
        uploading to GCS.
        
        Creates:
        - data/
        - data/raw/
        - data/processed/
        - data/raw/bus/
        - data/raw/train/
        - data/processed/bus/
        - data/processed/train/
        
        Example:
            Config.create_local_directories()
            # Directories are now created and ready to use
        """
        # Create main directories
        cls.RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for each transport mode
        for mode in cls.TRANSPORT_MODES:
            (cls.RAW_DATA_DIR / mode).mkdir(exist_ok=True)
            (cls.PROCESSED_DATA_DIR / mode).mkdir(exist_ok=True)
    
    @classmethod
    def print_config(cls) -> None:
        """
        Print current configuration (with secrets masked).
        
        Useful for debugging - shows what configuration is loaded
        without exposing sensitive values like API keys.
        
        Example:
            Config.print_config()
            # Prints all config with masked secrets
        """
        print("\n" + "="*70)
        print("📋 CURRENT CONFIGURATION")
        print("="*70)
        
        # Helper function to mask sensitive values
        def mask_value(value: Optional[str]) -> str:
            if value is None:
                return "❌ NOT SET"
            if len(value) > 8:
                # Show first 4 and last 4 characters, mask the middle
                return f"{value[:4]}...{value[-4:]}"
            return "***"
        
        print(f"\n🔑 LTA API:")
        print(f"   Account Key: {mask_value(cls.LTA_ACCOUNT_KEY)}")
        print(f"   Base URL: {cls.LTA_BASE_URL}")
        
        print(f"\n☁️  Google Cloud Platform:")
        print(f"   Project ID: {cls.GCP_PROJECT_ID or '❌ NOT SET'}")
        print(f"   Region: {cls.GCP_REGION}")
        print(f"   Credentials: {cls.GOOGLE_APPLICATION_CREDENTIALS or '❌ NOT SET'}")
        
        print(f"\n🗄️  Cloud Storage:")
        print(f"   Raw Data Bucket: {cls.GCS_BUCKET_RAW or '❌ NOT SET'}")
        print(f"   Processed Data Bucket: {cls.GCS_BUCKET_PROCESSED or '❌ NOT SET'}")
        
        print(f"\n📊 BigQuery:")
        print(f"   Dataset: {cls.BQ_DATASET or '❌ NOT SET'}")
        print(f"   Location: {cls.BQ_LOCATION}")
        
        print(f"\n💾 Local Storage:")
        print(f"   Data Directory: {cls.DATA_DIR}")
        print(f"   Save Locally: {cls.SAVE_LOCAL}")
        
        print(f"\n🚆 Pipeline:")
        print(f"   Transport Modes: {', '.join(cls.TRANSPORT_MODES)}")
        
        print("="*70 + "\n")


# Automatically validate configuration when this module is imported
# This ensures the app fails fast with helpful error messages if config is wrong
# Comment this out during development if you want to import without validating
# Config.validate()  # Uncommented for now - will validate when needed


# Module-level function for easy access
def get_config() -> type[Config]:
    """
    Get the Config class.
    
    This is a convenience function for importing config in other modules.
    
    Returns:
        Config class with all configuration loaded
        
    Example:
        from src.config.settings import get_config
        
        config = get_config()
        api_key = config.LTA_ACCOUNT_KEY
    """
    return Config


# If this file is run directly (not imported), print the configuration
if __name__ == "__main__":
    # This block only runs if you execute: python src/config/settings.py
    # Useful for testing and debugging configuration
    
    print("Testing configuration module...\n")
    
    try:
        # Try to validate configuration
        Config.validate()
        print("✅ Configuration is valid!\n")
        
        # Print configuration summary
        Config.print_config()
        
        # Create local directories if needed
        if Config.SAVE_LOCAL:
            Config.create_local_directories()
            print("✅ Local directories created!")
        
    except ValueError as e:
        # Configuration validation failed
        print(e)
        print("\n❌ Configuration validation failed!")
        print("Fix the issues above and try again.")
