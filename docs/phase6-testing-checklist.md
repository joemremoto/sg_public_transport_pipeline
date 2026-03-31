# Phase 6 Testing Checklist

**Objective:** Verify Airflow pipeline runs successfully end-to-end

**Test Date:** 2026-03-31  
**Test Data:** January 2026 (already extracted and loaded)

---

## Pre-Test Setup

### ✅ Prerequisites Check

- [ ] Docker and Docker Compose installed and running
- [ ] GCP service account credentials exist: `credentials/gcp-service-account.json`
- [ ] Environment variables configured in `.env` and `.env.airflow`
- [ ] LTA API key is valid and configured
- [ ] Existing data in BigQuery (from Phase 5)
- [ ] Port 8080 is available (not used by other services)

### ✅ File Verification

```bash
# Check all required files exist
ls docker-compose.yml
ls Dockerfile
ls airflow/requirements.txt
ls airflow/dags/sg_transport_monthly_pipeline.py
ls airflow/config/profiles.yml
ls credentials/gcp-service-account.json
```

---

## Test Steps

### Step 1: Build Custom Airflow Image

**Command:**
```bash
docker-compose build
```

**Expected Output:**
- Successfully builds custom image
- Installs all requirements (apache-airflow-providers-google, dbt-bigquery, etc.)
- Copies source code to `/opt/airflow/src`
- No build errors

**Status:** [ ] Pass / [ ] Fail

**Notes:**
```
[Record build time and any warnings]
```

---

### Step 2: Initialize Airflow Database

**Command:**
```bash
docker-compose up airflow-init
```

**Expected Output:**
- Creates Airflow metadata database
- Runs migrations
- Creates admin user
- Exits with code 0

**Status:** [ ] Pass / [ ] Fail

**Notes:**
```
[Record initialization output]
```

---

### Step 3: Start Airflow Services

**Command:**
```bash
docker-compose up -d
```

**Expected Output:**
- 3 containers start: postgres, airflow-webserver, airflow-scheduler
- All containers show "healthy" status after ~30 seconds

**Verification:**
```bash
docker-compose ps
```

**Expected:**
```
NAME                    STATUS
postgres               Up (healthy)
airflow-webserver      Up (healthy)
airflow-scheduler      Up (healthy)
```

**Status:** [ ] Pass / [ ] Fail

**Notes:**
```
[Record any container issues]
```

---

### Step 4: Access Airflow UI

**URL:** http://localhost:8080

**Credentials:**
- Username: `admin`
- Password: `admin`

**Expected:**
- Login page loads successfully
- Can authenticate with credentials
- Dashboard displays without errors

**Status:** [ ] Pass / [ ] Fail

**Screenshot:** [Take screenshot of dashboard]

---

### Step 5: Verify DAG Loaded

**In Airflow UI:**
1. Navigate to "DAGs" page
2. Search for: `sg_public_transport_monthly_pipeline`

**Expected:**
- DAG appears in list
- No import errors
- Shows as "Paused" initially
- 13 tasks visible in graph view

**Status:** [ ] Pass / [ ] Fail

**Notes:**
```
[Record DAG details: tasks, schedule, owner]
```

---

### Step 6: Enable DAG

**In Airflow UI:**
1. Toggle the DAG switch to "On"

**Expected:**
- DAG is now active
- No errors appear

**Status:** [ ] Pass / [ ] Fail

---

### Step 7: Trigger Manual DAG Run

**In Airflow UI:**
1. Click on DAG name: `sg_public_transport_monthly_pipeline`
2. Click "Trigger DAG" (play button icon)
3. Confirm trigger

**Expected:**
- DAG run starts immediately
- Status shows "running"
- Tasks begin executing

**Status:** [ ] Pass / [ ] Fail

**Start Time:** `____:____`

---

### Step 8: Monitor Task Execution

**Watch the following task groups:**

#### 8.1 Calculate Data Month
- [ ] Task: `calculate_data_month` - Success
- Expected: Calculates previous month from execution date

#### 8.2 Extract from LTA (4 tasks)
- [ ] Task: `extract_bus_stops` - Success
- [ ] Task: `extract_train_stations` - Success
- [ ] Task: `extract_bus_od` - Success (may take 5-10 min)
- [ ] Task: `extract_train_od` - Success (may take 3-5 min)

**Notes:**
```
[Record any API errors, timeouts, or warnings]
```

#### 8.3 Upload to GCS (2 tasks)
- [ ] Task: `upload_reference_data` - Success
- [ ] Task: `upload_journey_data` - Success (may take 5-8 min)

**Verify in GCS Console:**
- Check bucket: `sg-public-transport-data-raw`
- Verify files uploaded with correct timestamps

#### 8.4 Load to BigQuery (2 tasks)
- [ ] Task: `load_reference_tables` - Success
- [ ] Task: `load_od_tables` - Success (may take 3-5 min)

**Verify in BigQuery Console:**
- Check dataset: `sg_public_transport_analytics`
- Verify row counts updated

#### 8.5 dbt Transform (3 tasks)
- [ ] Task: `dbt_deps` - Success
- [ ] Task: `dbt_run` - Success (builds 10 models)
- [ ] Task: `dbt_test` - Success (runs 36 tests)

**Check dbt logs:**
- Click on `dbt_run` task → View Log
- Verify all 10 models built successfully
- No compilation errors

#### 8.6 Data Quality Validation
- [ ] Task: `validate_data_quality` - Success
- Verifies fact tables have rows > 0

**Status:** [ ] All Tasks Pass / [ ] Some Failed

**End Time:** `____:____`

**Total Duration:** `____ minutes`

---

### Step 9: Review Task Logs

**For each task group, spot-check logs:**

```bash
# View scheduler logs
docker-compose logs -f airflow-scheduler

# View webserver logs
docker-compose logs -f airflow-webserver
```

**Check for:**
- [ ] No ERROR level messages (except expected retries)
- [ ] No authentication failures
- [ ] No timeout errors
- [ ] GCP credentials loaded correctly
- [ ] dbt compiled successfully

**Status:** [ ] Pass / [ ] Fail

**Critical Errors:**
```
[List any critical errors found]
```

---

### Step 10: Verify Data in BigQuery

**Run these queries in BigQuery Console:**

```sql
-- Check fact_bus_journeys
SELECT 
  COUNT(*) as row_count,
  MIN(date_key) as earliest_date,
  MAX(date_key) as latest_date
FROM `sg_public_transport_analytics.fact_bus_journeys`;
```

**Expected:**
- Row count: ~17.6M rows
- Date range: January 2026 dates

```sql
-- Check fact_train_journeys
SELECT 
  COUNT(*) as row_count,
  MIN(date_key) as earliest_date,
  MAX(date_key) as latest_date
FROM `sg_public_transport_analytics.fact_train_journeys`;
```

**Expected:**
- Row count: ~1.7M rows
- Date range: January 2026 dates

**Status:** [ ] Pass / [ ] Fail

**Actual Row Counts:**
- Bus journeys: `____________`
- Train journeys: `____________`

---

### Step 11: Test DAG Re-run

**In Airflow UI:**
1. Mark the DAG run as "failed" or "success"
2. Clear task states
3. Re-trigger the DAG

**Expected:**
- DAG can be re-run without errors
- Idempotent behavior (doesn't duplicate data)

**Status:** [ ] Pass / [ ] Fail

---

### Step 12: Test Individual Task

**In Airflow UI:**
1. Click on a task (e.g., `dbt_test`)
2. Click "Clear"
3. Task should re-run independently

**Expected:**
- Single task re-executes
- Downstream tasks not affected

**Status:** [ ] Pass / [ ] Fail

---

### Step 13: Check Scheduler Health

```bash
# Check scheduler is processing DAGs
docker-compose exec airflow-scheduler airflow dags list-runs

# Check for any stuck tasks
docker-compose exec airflow-scheduler airflow tasks states-for-dag-run \
  sg_public_transport_monthly_pipeline \
  <execution_date>
```

**Expected:**
- Scheduler is active
- No tasks stuck in "running" state
- No zombie processes

**Status:** [ ] Pass / [ ] Fail

---

### Step 14: Test Failure Scenario (Optional)

**Simulate a task failure:**
1. Edit DAG to force a failure (e.g., wrong GCS path)
2. Trigger DAG
3. Observe retry behavior

**Expected:**
- Task retries 2 times with 5-minute delay
- Downstream tasks don't run
- Task marked as "failed" after retries exhausted

**Status:** [ ] Pass / [ ] Fail / [ ] Skipped

---

## Post-Test Cleanup

```bash
# Stop Airflow services
docker-compose down

# Optional: Remove volumes (WARNING: deletes all data)
# docker-compose down -v
```

---

## Test Results Summary

### Overall Status: [ ] PASS / [ ] FAIL

### Metrics

| Metric | Value |
|--------|-------|
| Total pipeline runtime | ___ minutes |
| Tasks succeeded | ___ / 13 |
| Tasks failed | ___ |
| Tasks retried | ___ |
| Docker build time | ___ minutes |
| Airflow init time | ___ seconds |

### Issues Found

| Issue | Severity | Resolution |
|-------|----------|------------|
| | | |
| | | |

### Recommendations

1. 
2. 
3. 

---

## Sign-off

**Tester:** ____________________  
**Date:** 2026-03-31  
**Airflow Version:** 2.10.4  
**Python Version:** 3.10  

**Notes:**
```
[Final thoughts, observations, next steps]
```

---

## Next Steps

If all tests pass:
- [ ] Update `docs/current-status.md` with test results
- [ ] Create Phase 6 success document
- [ ] Plan Phase 7: Streamlit dashboard
- [ ] Consider backfilling December 2025 and February 2026 data

If tests fail:
- [ ] Document failures in this checklist
- [ ] Review error logs
- [ ] Fix issues and re-test
- [ ] Update documentation with known issues
