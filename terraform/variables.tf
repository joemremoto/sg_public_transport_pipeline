/*
Terraform Variables Configuration

PURPOSE:
    This file defines all input variables that can be customized when
    running Terraform. Variables make your infrastructure code reusable
    across different environments (dev, staging, production).
    
    Variables can be set via:
    1. terraform.tfvars file (recommended)
    2. -var command line flag
    3. Environment variables (TF_VAR_name)
    4. Default values (defined here)

USAGE:
    # Create terraform.tfvars file with your values:
    echo 'project_id = "your-project-id"' > terraform.tfvars
    
    # Or pass variables on command line:
    terraform apply -var="project_id=your-project-id"
*/

# ============================================================================
# REQUIRED VARIABLES - Must be provided
# ============================================================================

variable "project_id" {
  description = "GCP Project ID where resources will be created"
  type        = string
  
  # No default - must be provided by user
  # This ensures you explicitly choose which project to use
}

# ============================================================================
# REGIONAL CONFIGURATION
# ============================================================================

variable "region" {
  description = <<-EOT
    GCP region for resources.
    Choose a region close to your users for lower latency.
    Singapore users should use asia-southeast1 or asia-east1.
  EOT
  type        = string
  default     = "asia-east1"
  
  # Other options:
  # - asia-southeast1: Singapore (most expensive but lowest latency)
  # - asia-east1: Taiwan (good balance of cost and latency)
  # - asia-east2: Hong Kong
}

# ============================================================================
# STORAGE CONFIGURATION
# ============================================================================

variable "gcs_bucket_raw" {
  description = <<-EOT
    Name for GCS bucket storing raw data from LTA API.
    Must be globally unique across ALL of Google Cloud Storage.
    Use project-specific prefix to avoid conflicts.
  EOT
  type        = string
  default     = "sg-public-transport-data-raw"
  
  # Naming convention: <project>-<purpose>-<data-type>
  # Must be lowercase, no underscores
  
  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9-]*[a-z0-9]$", var.gcs_bucket_raw))
    error_message = "Bucket name must be lowercase, alphanumeric, and hyphens only."
  }
}

variable "gcs_bucket_processed" {
  description = "Name for GCS bucket storing processed/transformed data"
  type        = string
  default     = "sg-public-transport-data-processed"
  
  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9-]*[a-z0-9]$", var.gcs_bucket_processed))
    error_message = "Bucket name must be lowercase, alphanumeric, and hyphens only."
  }
}

# ============================================================================
# BIGQUERY CONFIGURATION
# ============================================================================

variable "bq_dataset" {
  description = <<-EOT
    BigQuery dataset name for analytics tables.
    This will contain your dimension and fact tables.
  EOT
  type        = string
  
  # Note: BigQuery dataset names can use underscores
  # Unlike GCS buckets which must use hyphens
  
  validation {
    condition     = can(regex("^[a-zA-Z0-9_]+$", var.bq_dataset))
    error_message = "Dataset name must be alphanumeric and underscores only."
  }
}

variable "bq_admin_email" {
  description = <<-EOT
    Email address of the user who should have admin access to BigQuery dataset.
    This is typically your own email address.
  EOT
  type        = string
  
  # No default - must be provided
  # Use your own email address (the one you use for GCP)
}

# ============================================================================
# SERVICE ACCOUNT CONFIGURATION
# ============================================================================

variable "service_account_name" {
  description = <<-EOT
    Name for the service account that will run the pipeline.
    This should be short, descriptive, and follow naming conventions.
  EOT
  type        = string
  
  # Service account names must be 6-30 characters
  # Only lowercase letters, numbers, and hyphens
  
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{4,28}[a-z0-9]$", var.service_account_name))
    error_message = "Service account name must be 6-30 chars, lowercase, alphanumeric, and hyphens."
  }
}

# ============================================================================
# ENVIRONMENT CONFIGURATION
# ============================================================================

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
  
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

# ============================================================================
# SAFETY CONFIGURATION
# ============================================================================

variable "enable_deletion" {
  description = <<-EOT
    Allow Terraform to delete buckets and datasets even if they contain data.
    
    WARNING: Set to false in production!
    Setting to true is convenient for development, but dangerous in production.
    
    When false:
    - Terraform will refuse to delete non-empty buckets
    - You must manually delete data before destroying infrastructure
    
    When true:
    - Terraform can delete everything (including data) with 'terraform destroy'
    - Convenient for dev/testing, risky for production
  EOT
  type        = bool
  default     = true  # Safe for development
  
  # In production terraform.tfvars, set this to false!
}

# ============================================================================
# DATA RETENTION CONFIGURATION
# ============================================================================

variable "raw_data_retention_days" {
  description = "Number of days to keep raw data before deletion"
  type        = number
  default     = 90  # 3 months (matches LTA's availability window)
  
  validation {
    condition     = var.raw_data_retention_days >= 30
    error_message = "Raw data retention must be at least 30 days."
  }
}

variable "processed_data_retention_days" {
  description = "Number of days to keep processed data before deletion"
  type        = number
  default     = 180  # 6 months
  
  validation {
    condition     = var.processed_data_retention_days >= 90
    error_message = "Processed data retention must be at least 90 days."
  }
}

variable "bq_partition_retention_days" {
  description = "Number of days to keep BigQuery partitions before deletion"
  type        = number
  default     = 180  # 6 months
  
  validation {
    condition     = var.bq_partition_retention_days >= 60
    error_message = "BigQuery partition retention must be at least 60 days."
  }
}

# ============================================================================
# COST OPTIMIZATION CONFIGURATION
# ============================================================================

variable "move_to_nearline_days" {
  description = "Move GCS objects to NEARLINE storage after this many days"
  type        = number
  default     = 30
  
  # NEARLINE is for data accessed less than once per month
  # 50% cheaper than STANDARD storage
}

variable "move_to_coldline_days" {
  description = "Move GCS objects to COLDLINE storage after this many days"
  type        = number
  default     = 60
  
  # COLDLINE is for data accessed less than once per quarter
  # 75% cheaper than STANDARD storage
}

# ============================================================================
# VARIABLE NOTES
# ============================================================================

# VALIDATION:
# - Terraform validates variables before applying changes
# - Prevents common mistakes (e.g., invalid names, wrong formats)
# - Provides clear error messages
#
# DEFAULTS:
# - Sensible defaults for development
# - Should be overridden in terraform.tfvars for production
# - Required variables (no default) must be provided
#
# DESCRIPTIONS:
# - Multi-line descriptions use <<-EOT syntax (heredoc)
# - Explains what each variable controls
# - Provides guidance on choosing values
#
# BEST PRACTICES:
# - Use descriptive names
# - Provide clear descriptions
# - Set sensible defaults
# - Add validation rules where appropriate
# - Document special considerations
