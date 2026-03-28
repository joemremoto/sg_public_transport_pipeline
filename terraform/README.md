# Terraform Infrastructure - GCP Setup

This folder contains Terraform configuration for provisioning Google Cloud Platform (GCP) infrastructure for the Singapore Public Transport Analytics Pipeline.

---

## 📋 What Gets Created

### Resources:
1. **2 GCS Buckets**
   - `sg-public-transport-data-raw` - For raw data from LTA API
   - `sg-public-transport-data-processed` - For transformed data

2. **1 BigQuery Dataset**
   - `sg_public_transport_analytics` - For fact and dimension tables

3. **1 Service Account**
   - `sg-transport-pipeline` - For application authentication

4. **IAM Permissions**
   - Service account access to GCS buckets
   - Service account access to BigQuery dataset

5. **Enabled APIs**
   - Cloud Storage API
   - BigQuery API
   - IAM API

---

## 🚀 Prerequisites

### 1. Install Terraform

**Windows (using Chocolatey):**
```bash
choco install terraform
```

**Or download from:** https://www.terraform.io/downloads

**Verify installation:**
```bash
terraform version
```

### 2. Install Google Cloud SDK

**Windows:**
Download from: https://cloud.google.com/sdk/docs/install

**Verify installation:**
```bash
gcloud version
```

### 3. Authenticate with GCP

```bash
# Login to your Google account
gcloud auth login

# Set application default credentials (for Terraform)
gcloud auth application-default login

# Verify
gcloud auth list
```

### 4. Create/Select GCP Project

**Option A: Use existing project**
```bash
gcloud config set project sg-public-transport-pipeline
```

**Option B: Create new project**
```bash
gcloud projects create sg-public-transport-pipeline --name="SG Public Transport Pipeline"
gcloud config set project sg-public-transport-pipeline
```

**Enable billing** (required for creating resources):
https://console.cloud.google.com/billing

---

## ⚙️ Configuration

### 1. Create `terraform.tfvars`

Copy the example file and fill in your values:

```bash
cp terraform.tfvars.example terraform.tfvars
```

**Edit `terraform.tfvars`:**
```hcl
project_id     = "sg-public-transport-pipeline"
bq_admin_email = "your.email@gmail.com"  # Your GCP email

# Optional: Customize bucket names if defaults are taken
# gcs_bucket_raw = "sg-public-transport-data-raw-xyz123"
```

### 2. Review Configuration

Check the variables match your `.env` file:

**In `.env`:**
```
GCP_PROJECT_ID=sg-public-transport-pipeline
GCS_BUCKET_RAW=sg-public-transport-data-raw
GCS_BUCKET_PROCESSED=sg-public-transport-data-processed
BQ_DATASET=sg_public_transport_analytics
```

**In `terraform.tfvars`:**
```hcl
project_id = "sg-public-transport-pipeline"
gcs_bucket_raw = "sg-public-transport-data-raw"
gcs_bucket_processed = "sg-public-transport-data-processed"
bq_dataset = "sg_public_transport_analytics"
```

---

## 🏗️ Usage

### Step 1: Initialize Terraform

```bash
cd terraform
terraform init
```

This downloads required providers (Google Cloud provider) and initializes the backend.

### Step 2: Review Plan

```bash
terraform plan
```

This shows what Terraform will create, modify, or destroy. Review carefully!

**Expected output:**
```
Plan: 10 to add, 0 to change, 0 to destroy.
```

### Step 3: Apply Configuration

```bash
terraform apply
```

Type `yes` when prompted to create resources.

**Expected duration:** 1-2 minutes

### Step 4: Save Service Account Credentials

After Terraform completes, save the service account key:

**Windows (PowerShell):**
```powershell
terraform output -raw service_account_key_json | Out-File -Encoding ascii temp.txt
certutil -decode temp.txt ..\credentials\gcp-service-account.json
del temp.txt
```

**macOS/Linux:**
```bash
terraform output -raw service_account_key_json | base64 -d > ../credentials/gcp-service-account.json
```

### Step 5: Verify Resources

**List GCS buckets:**
```bash
gsutil ls
```

**List BigQuery datasets:**
```bash
bq ls --project_id=sg-public-transport-pipeline
```

**Test service account:**
```bash
gcloud auth activate-service-account --key-file=../credentials/gcp-service-account.json
gsutil ls gs://sg-public-transport-data-raw
```

---

## 📊 View Resources

After applying, Terraform outputs direct links to view resources:

```bash
# View all outputs
terraform output

# View infrastructure summary
terraform output infrastructure_summary

# View next steps
terraform output next_steps
```

**Or visit GCP Console:**
- **Storage:** https://console.cloud.google.com/storage/browser
- **BigQuery:** https://console.cloud.google.com/bigquery
- **IAM:** https://console.cloud.google.com/iam-admin/serviceaccounts

---

## 🔄 Updating Infrastructure

If you modify Terraform files:

```bash
# Preview changes
terraform plan

# Apply changes
terraform apply
```

Terraform only modifies what changed (incremental updates).

---

## 🗑️ Destroying Resources

**⚠️ WARNING:** This deletes ALL resources and data!

```bash
terraform destroy
```

Type `yes` when prompted.

**Use cases:**
- Clean up dev/test environment
- Start fresh
- Avoid ongoing costs

**Not recommended for production!**

---

## 📝 Common Commands

```bash
# Initialize (first time setup)
terraform init

# Format code (fix indentation)
terraform fmt

# Validate configuration
terraform validate

# Show current state
terraform show

# List all resources
terraform state list

# View specific output
terraform output gcs_bucket_raw_name

# Refresh state (sync with actual GCP)
terraform refresh

# Plan with specific variables
terraform plan -var="project_id=my-project"

# Apply without confirmation (automation)
terraform apply -auto-approve

# Destroy specific resource
terraform destroy -target=google_storage_bucket.raw_data
```

---

## 🔒 Security Best Practices

### ✅ DO:
- ✅ Keep `terraform.tfvars` out of Git (in `.gitignore`)
- ✅ Use service accounts for applications
- ✅ Enable uniform bucket-level access
- ✅ Set data retention policies
- ✅ Review `terraform plan` before applying
- ✅ Store credentials securely (never commit!)

### ❌ DON'T:
- ❌ Commit `terraform.tfstate` to Git (contains sensitive data)
- ❌ Commit `terraform.tfvars` (may contain secrets)
- ❌ Use your personal GCP account in applications
- ❌ Set `enable_deletion = true` in production
- ❌ Share service account keys publicly

---

## 🐛 Troubleshooting

### Error: "Project not found"
**Solution:** Verify project exists and you have access:
```bash
gcloud projects list
gcloud config set project YOUR_PROJECT_ID
```

### Error: "API not enabled"
**Solution:** Enable required APIs:
```bash
gcloud services enable storage.googleapis.com
gcloud services enable bigquery.googleapis.com
gcloud services enable iam.googleapis.com
```

### Error: "Bucket name already exists"
**Solution:** Bucket names must be globally unique. Try adding a suffix:
```hcl
gcs_bucket_raw = "sg-public-transport-data-raw-xyz123"
```

### Error: "Insufficient permissions"
**Solution:** Ensure you have required IAM roles:
- Storage Admin
- BigQuery Admin
- Service Account Admin

Check your roles:
```bash
gcloud projects get-iam-policy YOUR_PROJECT_ID --flatten="bindings[].members" --filter="bindings.members:user:YOUR_EMAIL"
```

### Error: "Invalid credentials"
**Solution:** Re-authenticate:
```bash
gcloud auth application-default login
```

---

## 📚 File Structure

```
terraform/
├── main.tf                    # Main infrastructure definition
├── variables.tf               # Input variables
├── outputs.tf                 # Output values
├── terraform.tfvars.example   # Example configuration
├── terraform.tfvars           # Your actual configuration (git-ignored)
├── README.md                  # This file
├── .terraform/                # Terraform working directory (git-ignored)
└── *.tfstate                  # State files (git-ignored)
```

---

## 🎓 Learning Resources

### Terraform Basics:
- **Official Tutorial:** https://learn.hashicorp.com/terraform
- **GCP Provider Docs:** https://registry.terraform.io/providers/hashicorp/google/latest/docs

### GCP Concepts:
- **GCS Documentation:** https://cloud.google.com/storage/docs
- **BigQuery Documentation:** https://cloud.google.com/bigquery/docs
- **IAM Best Practices:** https://cloud.google.com/iam/docs/best-practices

---

## ✅ Next Steps

After Terraform completes:

1. ✅ Verify resources in GCP Console
2. ✅ Save service account credentials
3. ✅ Test GCS access with gsutil
4. ✅ Test BigQuery access with bq CLI
5. ➡️ Create upload scripts (`src/upload/upload_to_gcs.py`)
6. ➡️ Create BigQuery loader scripts
7. ➡️ Initialize dbt project

---

**Last updated:** March 25, 2026  
**Version:** 1.0
