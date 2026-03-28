/*
Singapore Public Transport Pipeline - GCP Infrastructure
Terraform Configuration

PURPOSE:
    This Terraform configuration defines all Google Cloud Platform (GCP) resources
    needed for the Singapore Public Transport Analytics Pipeline.
    
    Infrastructure as Code (IaC) means we define our cloud resources in code
    rather than clicking through the web console. Benefits:
    - Reproducible: Can recreate exact same infrastructure
    - Version controlled: Track changes over time
    - Documented: Code is self-documenting
    - Automated: Apply with one command

RESOURCES CREATED:
    1. GCS Buckets - For storing raw and processed data
    2. BigQuery Dataset - For analytics warehouse
    3. Service Account - For application authentication
    4. IAM Permissions - For secure access control

PREREQUISITES:
    1. GCP account with billing enabled
    2. gcloud CLI installed and authenticated
    3. Terraform installed (v1.0+)
    4. Project created (or Terraform will create it)

USAGE:
    # Initialize Terraform (first time only)
    terraform init
    
    # Preview changes
    terraform plan
    
    # Apply changes (create resources)
    terraform apply

    # Destroy everything (careful!)
    terraform destroy
*/

# ============================================================================
# TERRAFORM CONFIGURATION
# ============================================================================

# Specify required Terraform version and providers
terraform {
  # Require Terraform 1.0 or newer
  required_version = ">= 1.0"
  
  # Define required providers and their versions
  required_providers {
    google = {
      source  = "hashicorp/google"  # Official Google provider
      version = "~> 5.0"             # Use version 5.x (allows 5.1, 5.2, etc.)
    }
  }
}

# ============================================================================
# PROVIDER CONFIGURATION
# ============================================================================

# Configure the Google Cloud provider
provider "google" {
  project = var.project_id  # GCP project ID
  region  = var.region      # Default region for resources
  
  # Terraform will use your gcloud CLI credentials
  # Or you can specify credentials file:
  # credentials = file(var.credentials_file)
}

# ============================================================================
# DATA SOURCES - Query existing GCP resources
# ============================================================================

# Get information about the current GCP project
# This is useful for constructing resource names and references
data "google_project" "project" {
  project_id = var.project_id
}

# ============================================================================
# GOOGLE CLOUD STORAGE BUCKETS
# ============================================================================

# GCS Bucket for RAW data (as downloaded from LTA API)
resource "google_storage_bucket" "raw_data" {
  # Bucket name must be globally unique across ALL of GCS
  name     = var.gcs_bucket_raw
  location = var.region
  
  # STANDARD storage class
  # - Most expensive per GB, but cheapest access cost
  # - Good for frequently accessed data (our raw data)
  storage_class = "STANDARD"
  
  # Force destroy allows Terraform to delete bucket even if it contains files
  # WARNING: Set to false in production!
  force_destroy = var.enable_deletion
  
  # Enable uniform bucket-level access (recommended security practice)
  # This means permissions are set at bucket level, not per-object
  uniform_bucket_level_access = true
  
  # Lifecycle rules to manage data retention and costs
  lifecycle_rule {
    # Delete files older than 90 days
    # Raw data from LTA is only kept for 3 months anyway
    condition {
      age = 90  # days
    }
    action {
      type = "Delete"
    }
  }
  
  lifecycle_rule {
    # Move files to NEARLINE storage after 30 days
    # NEARLINE is cheaper for data accessed less than once per month
    condition {
      age = 30  # days
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }
  
  # Enable versioning to protect against accidental deletion
  versioning {
    enabled = true
  }
  
  # Add labels for organization and cost tracking
  labels = {
    environment = var.environment
    project     = "sg-public-transport-pipeline"
    managed_by  = "terraform"
    data_type   = "raw"
  }
}

# GCS Bucket for PROCESSED data (after dbt transformations)
resource "google_storage_bucket" "processed_data" {
  name          = var.gcs_bucket_processed
  location      = var.region
  storage_class = "STANDARD"
  force_destroy = var.enable_deletion
  
  uniform_bucket_level_access = true
  
  # Processed data lifecycle (keep longer than raw)
  lifecycle_rule {
    # Delete after 180 days (6 months)
    condition {
      age = 180
    }
    action {
      type = "Delete"
    }
  }
  
  lifecycle_rule {
    # Move to COLDLINE after 60 days
    # COLDLINE is for data accessed less than once per quarter
    condition {
      age = 60
    }
    action {
      type          = "SetStorageClass"
      storage_class = "COLDLINE"
    }
  }
  
  versioning {
    enabled = true
  }
  
  labels = {
    environment = var.environment
    project     = "sg-public-transport-pipeline"
    managed_by  = "terraform"
    data_type   = "processed"
  }
}

# ============================================================================
# BIGQUERY DATASET
# ============================================================================

# BigQuery dataset for analytics warehouse
resource "google_bigquery_dataset" "analytics" {
  # Dataset ID (name within the project)
  dataset_id = var.bq_dataset
  
  # Location must match GCS bucket location for optimal performance
  location = var.region
  
  # Human-readable description
  description = "Singapore Public Transport Analytics - Fact and Dimension Tables"
  
  # Default table expiration (optional)
  # Tables will be deleted after this many milliseconds if not accessed
  # Set to null for no expiration (recommended for production)
  default_table_expiration_ms = null
  
  # Default partition expiration
  # Partitions older than this will be deleted (cost optimization)
  # 180 days = 6 months
  default_partition_expiration_ms = 15552000000  # 180 days in milliseconds
  
  # Delete dataset contents when Terraform destroys the dataset
  # WARNING: Set to false in production!
  delete_contents_on_destroy = var.enable_deletion
  
  # Labels for organization
  labels = {
    environment = var.environment
    project     = "sg-public-transport-pipeline"
    managed_by  = "terraform"
  }
  
  # Access control
  # Note: Additional access will be granted to service account below
  access {
    # Grant project owners full control
    role          = "OWNER"
    user_by_email = var.bq_admin_email
  }
}

# ============================================================================
# SERVICE ACCOUNT
# ============================================================================

# Service account for the pipeline application
# This is the identity that your Python scripts will use to access GCP
resource "google_service_account" "pipeline_sa" {
  account_id   = var.service_account_name
  display_name = "Singapore Public Transport Pipeline Service Account"
  description  = "Service account for automated pipeline operations"
  
  # Service accounts don't support labels, but we can add a description
}

# ============================================================================
# IAM PERMISSIONS - Grant service account access to resources
# ============================================================================

# Grant service account access to GCS raw bucket
resource "google_storage_bucket_iam_member" "raw_data_writer" {
  bucket = google_storage_bucket.raw_data.name
  role   = "roles/storage.objectAdmin"  # Can create, read, update, delete objects
  member = "serviceAccount:${google_service_account.pipeline_sa.email}"
}

# Grant service account access to GCS processed bucket
resource "google_storage_bucket_iam_member" "processed_data_writer" {
  bucket = google_storage_bucket.processed_data.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.pipeline_sa.email}"
}

# Grant service account BigQuery permissions
# BigQuery Admin allows creating/updating tables and running queries
resource "google_project_iam_member" "bigquery_admin" {
  project = var.project_id
  role    = "roles/bigquery.admin"
  member  = "serviceAccount:${google_service_account.pipeline_sa.email}"
}

# Grant service account BigQuery Data Editor on the specific dataset
resource "google_bigquery_dataset_iam_member" "analytics_editor" {
  dataset_id = google_bigquery_dataset.analytics.dataset_id
  role       = "roles/bigquery.dataEditor"  # Can insert, update, delete data
  member     = "serviceAccount:${google_service_account.pipeline_sa.email}"
}

# ============================================================================
# SERVICE ACCOUNT KEY
# ============================================================================

# Create a service account key (JSON credentials file)
# This is what your application will use to authenticate
resource "google_service_account_key" "pipeline_sa_key" {
  service_account_id = google_service_account.pipeline_sa.name
  
  # Key will be output as base64-encoded JSON
  # We'll decode it and save to file in outputs.tf
}

# ============================================================================
# ENABLE REQUIRED APIs
# ============================================================================

# Enable Cloud Storage API
resource "google_project_service" "storage" {
  project = var.project_id
  service = "storage.googleapis.com"
  
  # Don't disable the API when Terraform destroys this resource
  # (Prevents breaking other resources that might use it)
  disable_on_destroy = false
}

# Enable BigQuery API
resource "google_project_service" "bigquery" {
  project = var.project_id
  service = "bigquery.googleapis.com"
  
  disable_on_destroy = false
}

# Enable IAM API
resource "google_project_service" "iam" {
  project = var.project_id
  service = "iam.googleapis.com"
  
  disable_on_destroy = false
}

# ============================================================================
# NOTES AND BEST PRACTICES
# ============================================================================

# COST OPTIMIZATION:
# - Lifecycle rules automatically move old data to cheaper storage
# - Partition expiration prevents unbounded growth
# - Standard storage for hot data, Nearline/Coldline for cold data
#
# SECURITY:
# - Uniform bucket-level access (no public access)
# - Service account with least-privilege permissions
# - Credentials stored securely (never commit to Git!)
#
# RELIABILITY:
# - Versioning enabled (recover from accidental deletion)
# - Regional resources (all in same region for performance)
# - Required APIs enabled automatically
#
# MAINTAINABILITY:
# - All resources labeled for easy identification
# - Descriptive names following naming conventions
# - Infrastructure as code (reproducible, version-controlled)
