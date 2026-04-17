# Streamlit Credentials Path Fix

**Date:** March 28, 2026  
**Issue:** Streamlit fails to load GCP credentials with path resolution error

## Problem

When running Streamlit from `streamlit_app/` directory:
```
Failed to connect to BigQuery: Credentials file not found: 
C:\Users\Joseph\sg_public_transport_pipeline\streamlit_app./credentials/gcp-service-account.json
```

### Root Cause

The `.env` file specifies a relative path:
```
GOOGLE_APPLICATION_CREDENTIALS=./credentials/gcp-service-account.json
```

When Streamlit loads this from `streamlit_app/app.py`, the path resolution in `utils/bigquery_client.py` was incorrect:
- **Original code:** `os.path.dirname(os.path.dirname(os.path.abspath(__file__)))`
- **This resolved to:** `streamlit_app/` (only went up 1 level from `utils/`)
- **Should resolve to:** Project root (2 levels up from `utils/`)

## Solution

Updated `streamlit_app/utils/bigquery_client.py` (lines 32-36):

```python
# Get project root (two levels up: utils -> streamlit_app -> project_root)
utils_dir = os.path.dirname(os.path.abspath(__file__))
streamlit_dir = os.path.dirname(utils_dir)
project_root = os.path.dirname(streamlit_dir)
credentials_path = os.path.join(project_root, credentials_path)
```

### Path Resolution Flow

1. `__file__` = `c:\...\streamlit_app\utils\bigquery_client.py`
2. `utils_dir` = `c:\...\streamlit_app\utils`
3. `streamlit_dir` = `c:\...\streamlit_app`
4. `project_root` = `c:\...\sg_public_transport_pipeline`
5. Final path = `c:\...\sg_public_transport_pipeline\credentials\gcp-service-account.json` ✅

## Testing

To verify the fix:
```bash
cd streamlit_app
streamlit run app.py
```

Should now load credentials successfully from the project root's `credentials/` directory.

## Related Files

- `streamlit_app/utils/bigquery_client.py` (fixed)
- `.env` (contains `GOOGLE_APPLICATION_CREDENTIALS=./credentials/gcp-service-account.json`)
- `docs/env-consolidation.md` (updated with note about path resolution)
