/*
Terraform Outputs Configuration

PURPOSE:
    Outputs display important information after Terraform creates resources.
    They're useful for:
    - Getting resource names/IDs to use in your application
    - Displaying connection strings and credentials
    - Passing values to other Terraform modules
    - Documenting what was created

USAGE:
    # View all outputs after applying
    terraform output
    
    # View specific output
    terraform output gcs_bucket_raw_name
    
    # Output in JSON format
    terraform output -json
*/

# ============================================================================
# GCS BUCKET OUTPUTS
# ============================================================================

output "gcs_bucket_raw_name" {
  description = "Name of the GCS bucket for raw data"
  value       = google_storage_bucket.raw_data.name
}

output "gcs_bucket_raw_url" {
  description = "URL of the GCS bucket for raw data"
  value       = google_storage_bucket.raw_data.url
}

output "gcs_bucket_processed_name" {
  description = "Name of the GCS bucket for processed data"
  value       = google_storage_bucket.processed_data.name
}

output "gcs_bucket_processed_url" {
  description = "URL of the GCS bucket for processed data"
  value       = google_storage_bucket.processed_data.url
}

# ============================================================================
# BIGQUERY OUTPUTS
# ============================================================================

output "bigquery_dataset_id" {
  description = "ID of the BigQuery dataset"
  value       = google_bigquery_dataset.analytics.dataset_id
}

output "bigquery_dataset_location" {
  description = "Location of the BigQuery dataset"
  value       = google_bigquery_dataset.analytics.location
}

output "bigquery_dataset_url" {
  description = "URL to view the BigQuery dataset in console"
  value       = "https://console.cloud.google.com/bigquery?project=${var.project_id}&ws=!1m4!1m3!3m2!1s${var.project_id}!2s${google_bigquery_dataset.analytics.dataset_id}"
}

# ============================================================================
# SERVICE ACCOUNT OUTPUTS
# ============================================================================

output "service_account_email" {
  description = "Email of the pipeline service account"
  value       = google_service_account.pipeline_sa.email
}

output "service_account_id" {
  description = "ID of the pipeline service account"
  value       = google_service_account.pipeline_sa.id
}

output "service_account_key_json" {
  description = "Service account key in JSON format (base64 encoded)"
  value       = google_service_account_key.pipeline_sa_key.private_key
  sensitive   = true  # Hide from console output (contains credentials!)
  
  # To save this to a file (after terraform apply):
  # terraform output -raw service_account_key_json | base64 -d > credentials/gcp-service-account.json
}

# ============================================================================
# PROJECT INFORMATION
# ============================================================================

output "project_id" {
  description = "GCP Project ID"
  value       = var.project_id
}

output "project_number" {
  description = "GCP Project Number"
  value       = data.google_project.project.number
}

output "region" {
  description = "GCP Region where resources are created"
  value       = var.region
}

# ============================================================================
# SUMMARY OUTPUT
# ============================================================================

output "infrastructure_summary" {
  description = "Summary of all created infrastructure"
  value = {
    project = {
      id     = var.project_id
      number = data.google_project.project.number
      region = var.region
    }
    storage = {
      raw_bucket       = google_storage_bucket.raw_data.name
      processed_bucket = google_storage_bucket.processed_data.name
    }
    bigquery = {
      dataset  = google_bigquery_dataset.analytics.dataset_id
      location = google_bigquery_dataset.analytics.location
    }
    service_account = {
      email = google_service_account.pipeline_sa.email
      name  = google_service_account.pipeline_sa.name
    }
    environment = var.environment
  }
}

# ============================================================================
# NEXT STEPS OUTPUT
# ============================================================================

output "next_steps" {
  description = "Instructions for what to do after Terraform completes"
  value = <<-EOT
  
  ✅ Infrastructure Created Successfully!
  
  📋 Next Steps:
  
  1. Save Service Account Credentials:
     terraform output -raw service_account_key_json | base64 -d > credentials/gcp-service-account.json
     
  2. Verify .env Configuration:
     - GCP_PROJECT_ID=${var.project_id}
     - GCS_BUCKET_RAW=${google_storage_bucket.raw_data.name}
     - GCS_BUCKET_PROCESSED=${google_storage_bucket.processed_data.name}
     - BQ_DATASET=${google_bigquery_dataset.analytics.dataset_id}
     - GOOGLE_APPLICATION_CREDENTIALS=./credentials/gcp-service-account.json
  
  3. Test GCS Access:
     gsutil ls gs://${google_storage_bucket.raw_data.name}
  
  4. Test BigQuery Access:
     bq ls --project_id=${var.project_id} ${google_bigquery_dataset.analytics.dataset_id}
  
  5. Create Upload Scripts:
     - src/upload/upload_to_gcs.py
     - src/load/load_to_bigquery.py
  
  📊 View Resources:
  - GCS Console: https://console.cloud.google.com/storage/browser?project=${var.project_id}
  - BigQuery Console: https://console.cloud.google.com/bigquery?project=${var.project_id}&ws=!1m4!1m3!3m2!1s${var.project_id}!2s${google_bigquery_dataset.analytics.dataset_id}
  - IAM Console: https://console.cloud.google.com/iam-admin/serviceaccounts?project=${var.project_id}
  
  EOT
}

# ============================================================================
# OUTPUT NOTES
# ============================================================================

# SENSITIVE OUTPUTS:
# - service_account_key_json is marked sensitive
# - Won't be displayed in console output
# - Must use `terraform output -raw service_account_key_json` to retrieve
# - NEVER commit credentials to Git!
#
# URL OUTPUTS:
# - Direct links to GCP console for easy access
# - Click to view resources in web interface
#
# SUMMARY OUTPUTS:
# - Structured output combining multiple values
# - Useful for passing to other tools/scripts
# - Can be consumed as JSON: terraform output -json infrastructure_summary
#
# NEXT STEPS:
# - Provides clear instructions for user
# - Copy-paste ready commands
# - Reduces confusion about what to do after infrastructure is created
