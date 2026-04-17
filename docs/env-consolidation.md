# Environment Variables Consolidation

**Date:** March 28, 2026  
**Status:** ✅ Complete

## Summary

Consolidated all environment variables into a single root `.env` file for simplified configuration management across all services (Python scripts, Airflow, Streamlit).

## Changes Made

### 1. Consolidated `.env` File

**Location:** `c:\Users\JosephEmmanuelRemoto\hellofresh_gh\sg_public_transport_pipeline\.env`

**Contents:**
- GCP configuration (credentials, project ID, region)
- GCS bucket names (raw, processed)
- BigQuery configuration (dataset, location)
- LTA API key
- Airflow configuration (UID, web UI credentials)

### 2. Removed Separate Environment Files

- ❌ **Deleted:** `airflow/.env` (previously `.env.airflow` at root)
  - All Airflow variables now in root `.env`
  - Docker Compose already configured to read from root `.env`
  
- ❌ **Deleted:** `streamlit_app/.env`
  - Streamlit app has fallback logic to use root `.env`
  - Updated `streamlit_app/.env.example` with note about consolidation

### 3. Updated `.env.example`

**Changes:**
- Uncommented Airflow configuration section (lines 50-62)
- Updated notes section to reflect single `.env` usage
- Removed references to separate Streamlit `.env`

### 4. Updated `.gitignore`

**Changes:**
- Removed `.env.airflow` entries
- Kept single `.env` in gitignore (already present)

## File Loading Behavior

### Python Scripts (`src/`)
```python
from dotenv import load_dotenv
load_dotenv()  # Loads .env from project root
```

### Streamlit (`streamlit_app/app.py`)
```python
# Lines 24-30: Tries streamlit_app/.env first, then parent .env
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
else:
    parent_env = Path(__file__).parent.parent / '.env'
    load_dotenv(parent_env)  # ✅ Will use root .env
```

### Airflow (`docker-compose.yml`)
```yaml
# Lines 30, 41, 111-112: Reads from root .env via ${VAR_NAME}
LTA_ACCOUNT_KEY: ${LTA_ACCOUNT_KEY}
user: "${AIRFLOW_UID:-50000}:0"
_AIRFLOW_WWW_USER_USERNAME: ${_AIRFLOW_WWW_USER_USERNAME:-admin}
_AIRFLOW_WWW_USER_PASSWORD: ${_AIRFLOW_WWW_USER_PASSWORD:-admin}
```

## Benefits

1. **Simplicity:** One file to manage all environment variables
2. **Consistency:** Same values across all services
3. **Maintainability:** Single source of truth for configuration
4. **Developer Experience:** Less confusion, easier setup

## Verification

To verify the consolidation works:

### Test Python Scripts
```bash
python scripts/upload_to_gcs.py --help
# Should load .env successfully
```

### Test Airflow
```bash
docker-compose up airflow-init
# Should use AIRFLOW_UID and credentials from .env
```

### Test Streamlit
```bash
cd streamlit_app
streamlit run app.py
# Should load credentials from parent .env
```

## Future Considerations

For production deployments:
- Use cloud secret management (GCP Secret Manager, AWS Secrets Manager)
- Use Kubernetes secrets/ConfigMaps
- Never commit `.env` to version control (already in `.gitignore`)

## Related Files

- `.env` (root, contains all variables)
- `.env.example` (root, template for setup)
- `streamlit_app/.env.example` (note about consolidation)
- `.gitignore` (updated to remove `.env.airflow`)
- `docker-compose.yml` (reads from root `.env`)
- `streamlit_app/app.py` (fallback to parent `.env`)
