# Phase 6: Apache Airflow Orchestration

**Status:** Complete  
**Date Completed:** 2026-03-31

---

## Overview

Phase 6 implements Apache Airflow orchestration for the Singapore LTA Public Transport Analytics Pipeline. The DAG automates the entire monthly data pipeline from API extraction to BigQuery transformation.

---

## What Was Built

### 1. Airflow Infrastructure

**Docker-based Airflow Setup:**
- Apache Airflow 2.10.4 with Python 3.10
- PostgreSQL database for metadata storage
- LocalExecutor for task execution
- Webserver on port 8080

**Key Files:**
- `docker-compose.yml` - Docker orchestration
- `Dockerfile` - Custom Airflow image with dependencies
- `airflow/requirements.txt` - Python packages
- `.env.airflow` - Airflow-specific environment variables

### 2. Main Pipeline DAG

**DAG:** `sg_public_transport_monthly_pipeline`

**Schedule:** Monthly on the 15th (after LTA releases previous month's data)

**Task Groups:**

1. **Extract from LTA** (4 tasks)
   - Extract bus stops reference data
   - Extract train stations reference data
   - Extract bus OD journey data (previous month)
   - Extract train OD journey data (previous month)

2. **Upload to GCS** (2 tasks)
   - Upload reference data to `reference/*.ndjson`
   - Upload journey data to `journeys/{mode}/{year}/{month}/*.csv`

3. **Load to BigQuery** (2 tasks)
   - Load reference tables (bus_stops, train_stations)
   - Load OD tables (bus_od, train_od)

4. **dbt Transform** (3 tasks)
   - Install dbt dependencies
   - Run dbt models (10 models: staging, dimensions, facts)
   - Run dbt tests (36 data quality tests)

5. **Data Quality Validation** (1 task)
   - Validate fact table row counts
   - Check for empty tables
   - Ensure data was loaded successfully

**Total Tasks:** 13 (including start, end, and date calculation)

### 3. Configuration Files

**dbt Profile** (`airflow/config/profiles.yml`):
- BigQuery connection via service account
- Environment variable-based configuration
- Production target with 4 threads

**Alerting Guide** (`airflow/config/ALERTING.md`):
- Email configuration (optional)
- Slack webhook setup (recommended)
- Monitoring recommendations

### 4. Retry & Error Handling

**Default Task Settings:**
- Retries: 2 attempts
- Retry delay: 5 minutes
- Execution timeout: 2 hours
- Failure alerts: Configurable

---

## Architecture

### DAG Task Flow

```
start
  ↓
calculate_data_month
  ↓
┌─────────────────────────────────┐
│ Extract from LTA (4 tasks)      │
│ - Bus stops                     │
│ - Train stations                │
│ - Bus OD (prev month)           │
│ - Train OD (prev month)         │
└─────────────────────────────────┘
  ↓
┌─────────────────────────────────┐
│ Upload to GCS (2 tasks)         │
│ - Reference data                │
│ - Journey data                  │
└─────────────────────────────────┘
  ↓
┌─────────────────────────────────┐
│ Load to BigQuery (2 tasks)      │
│ - Reference tables              │
│ - OD tables                     │
└─────────────────────────────────┘
  ↓
┌─────────────────────────────────┐
│ dbt Transform (3 tasks)         │
│ - dbt deps                      │
│ - dbt run                       │
│ - dbt test                      │
└─────────────────────────────────┘
  ↓
validate_data_quality
  ↓
end
```

### Data Flow

```
LTA API
  ↓
[Airflow: Extract Tasks]
  ↓
Local Storage (/opt/airflow/data)
  ↓
[Airflow: Upload Tasks]
  ↓
GCS (sg-public-transport-data-raw)
  ↓
[Airflow: Load Tasks]
  ↓
BigQuery Raw Tables
  ↓
[Airflow: dbt Tasks]
  ↓
BigQuery Star Schema (19.3M rows)
  ↓
[Airflow: Validation Task]
  ↓
Complete ✓
```

---

## Setup Instructions

### Prerequisites

- Docker and Docker Compose installed
- GCP service account credentials in `credentials/gcp-service-account.json`
- LTA API key in `.env` file
- Existing GCP infrastructure (buckets, BigQuery dataset)

### Step 1: Build Custom Airflow Image

The custom image includes all required Python packages and the project source code.

```bash
docker-compose build
```

### Step 2: Initialize Airflow Database

Creates the Airflow metadata database and admin user.

```bash
docker-compose up airflow-init
```

### Step 3: Start Airflow Services

Starts webserver, scheduler, and PostgreSQL.

```bash
docker-compose up -d
```

### Step 4: Access Airflow UI

Open http://localhost:8080

**Default credentials:**
- Username: `admin`
- Password: `admin`

### Step 5: Enable the DAG

In the Airflow UI:
1. Navigate to DAGs page
2. Find `sg_public_transport_monthly_pipeline`
3. Toggle the DAG to "On"

---

## Running the Pipeline

### Manual Trigger (Testing)

1. Go to Airflow UI: http://localhost:8080
2. Click on `sg_public_transport_monthly_pipeline`
3. Click "Trigger DAG" (play button)
4. Monitor task execution in real-time

### Scheduled Runs

The DAG automatically runs monthly on the 15th at midnight (UTC).

**Why the 15th?**  
LTA typically releases the previous month's data around the 10th-12th of each month. The 15th provides a buffer.

### Backfilling Historical Data

To process previous months:

```bash
docker-compose exec airflow-webserver bash

# Backfill December 2025
airflow dags backfill \
  sg_public_transport_monthly_pipeline \
  --start-date 2025-12-01 \
  --end-date 2025-12-31

# Backfill February 2026
airflow dags backfill \
  sg_public_transport_monthly_pipeline \
  --start-date 2026-02-01 \
  --end-date 2026-02-28
```

---

## Monitoring & Debugging

### View Task Logs

In Airflow UI:
1. Click on the DAG run
2. Click on a task
3. Click "Log" to view execution details

### Common Issues

**Issue:** DAG not showing up
- **Fix:** Check for syntax errors in `airflow/dags/sg_transport_monthly_pipeline.py`
- **Command:** `docker-compose logs airflow-scheduler`

**Issue:** GCP authentication failed
- **Fix:** Ensure `credentials/gcp-service-account.json` is mounted correctly
- **Check:** `docker-compose exec airflow-webserver ls /opt/airflow/credentials`

**Issue:** dbt command not found
- **Fix:** Rebuild Docker image with requirements
- **Command:** `docker-compose build --no-cache`

**Issue:** Task stuck in "running" state
- **Fix:** Check task logs for timeouts or hanging processes
- **Action:** Mark task as failed and retry

### Health Checks

```bash
# Check service status
docker-compose ps

# Check scheduler logs
docker-compose logs -f airflow-scheduler

# Check webserver logs
docker-compose logs -f airflow-webserver

# Check PostgreSQL
docker-compose logs postgres
```

---

## Configuration Details

### Environment Variables (from docker-compose.yml)

| Variable | Value | Purpose |
|----------|-------|---------|
| AIRFLOW__CORE__EXECUTOR | LocalExecutor | Single-machine execution |
| AIRFLOW__CORE__LOAD_EXAMPLES | false | Disable example DAGs |
| GOOGLE_APPLICATION_CREDENTIALS | /opt/airflow/credentials/... | GCP auth |
| GCP_PROJECT_ID | sg-public-transport-pipeline | GCP project |
| GCS_BUCKET_RAW | sg-public-transport-data-raw | Raw data bucket |
| BQ_DATASET | sg_public_transport_analytics | BigQuery dataset |
| LTA_ACCOUNT_KEY | (from .env) | LTA API key |

### Volume Mounts

| Local Path | Container Path | Purpose |
|------------|----------------|---------|
| ./airflow/dags | /opt/airflow/dags | DAG definitions |
| ./airflow/logs | /opt/airflow/logs | Task execution logs |
| ./credentials | /opt/airflow/credentials | GCP service account |
| ./src | /opt/airflow/src | Python source code |
| ./sg_transport_dbt | /opt/airflow/dbt | dbt project |
| ./data | /opt/airflow/data | Local data storage |

---

## Performance Metrics

### Expected Execution Times (January 2026 data)

| Task Group | Duration | Notes |
|------------|----------|-------|
| Extract from LTA | ~10-15 min | Depends on API response time |
| Upload to GCS | ~5-8 min | Large CSV files (230MB bus, 18MB train) |
| Load to BigQuery | ~3-5 min | Bulk load from GCS |
| dbt Transform | ~15-20 sec | 10 models, 19.3M rows |
| Data Quality | ~5 sec | Row count validation |
| **Total Pipeline** | ~20-30 min | Full end-to-end |

### Resource Usage

- **Memory:** ~2GB (PostgreSQL + Airflow services)
- **CPU:** Low (LocalExecutor, 1 task at a time per group)
- **Disk:** ~500MB for logs and metadata

---

## Alerting & Notifications

### Current Setup

- Basic retry logic (2 retries, 5-minute delay)
- Execution timeout (2 hours)
- Manual monitoring via Airflow UI

### Recommended for Production

1. **Email Alerts:**
   - Configure SMTP in docker-compose.yml
   - Enable `email_on_failure: True` in DAG

2. **Slack Notifications:**
   - Set up Slack webhook
   - Add `on_failure_callback` to DAG

3. **External Monitoring:**
   - Datadog APM integration
   - Grafana dashboards
   - Cloud Logging integration

See `airflow/config/ALERTING.md` for detailed setup instructions.

---

## Next Steps

1. **Test the Pipeline**
   - Trigger manual DAG run with January 2026 data
   - Verify all tasks complete successfully
   - Check BigQuery for updated data

2. **Backfill Historical Data**
   - Extract December 2025, February 2026
   - Run backfill commands
   - Validate data consistency

3. **Enable Production Features**
   - Set up email/Slack alerts
   - Configure external monitoring
   - Implement SLA tracking

4. **Phase 7: Streamlit Dashboard**
   - Build interactive visualizations
   - Connect to BigQuery star schema
   - Deploy to Streamlit Cloud or GCP

---

## Lessons Learned

### What Worked Well

1. **Docker Compose:** Easy local development and testing
2. **Task Groups:** Clear organization of related tasks
3. **Environment Variables:** Flexible configuration without code changes
4. **Volume Mounts:** Direct access to source code and data
5. **dbt Integration:** Seamless transformation execution

### Challenges

1. **Windows PowerShell:** Different commands than bash (e.g., `mkdir` vs `mkdir -p`)
2. **Docker File Permissions:** Had to set `user: "0:0"` for init container
3. **dbt Profiles:** Required separate profiles.yml for Airflow environment

### Improvements for Production

1. **CeleryExecutor:** For parallel task execution across workers
2. **Cloud Composer:** Managed Airflow on GCP (removes Docker maintenance)
3. **KubernetesPodOperator:** For isolated task execution
4. **Secrets Backend:** Store credentials in GCP Secret Manager
5. **Custom Operators:** Reusable Python classes for common patterns

---

## Files Created

```
project_root/
├── docker-compose.yml                    # Airflow orchestration
├── Dockerfile                            # Custom Airflow image
├── .env.airflow                          # Airflow environment variables
└── airflow/
    ├── requirements.txt                  # Python dependencies
    ├── dags/
    │   └── sg_transport_monthly_pipeline.py  # Main DAG
    ├── config/
    │   ├── profiles.yml                  # dbt profile
    │   └── ALERTING.md                   # Alerting guide
    ├── logs/                             # Task execution logs (git-ignored)
    └── plugins/                          # Custom operators (future)
```

---

## Summary

Phase 6 successfully implements Apache Airflow orchestration for the Singapore LTA Public Transport Analytics Pipeline:

- ✅ Docker-based Airflow setup (2.10.4)
- ✅ Monthly pipeline DAG (13 tasks, 5 task groups)
- ✅ Automated extraction, upload, load, and transformation
- ✅ Data quality validation
- ✅ Retry logic and error handling
- ✅ Comprehensive documentation

**Pipeline Status:** Ready for testing and production deployment.

**Next Phase:** Phase 7 - Streamlit visualization dashboard.
