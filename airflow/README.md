# Airflow Setup - Singapore LTA Pipeline

This directory contains the Apache Airflow orchestration for the Singapore Public Transport Analytics Pipeline.

## Quick Start

### 1. Build and Initialize

```bash
# Build custom Airflow image
docker-compose build

# Initialize Airflow database and create admin user
docker-compose up airflow-init
```

### 2. Start Airflow

```bash
# Start all services (webserver, scheduler, postgres)
docker-compose up -d

# Check service status
docker-compose ps
```

### 3. Access Airflow UI

Open http://localhost:8080

**Login:**
- Username: `admin`
- Password: `admin`

### 4. Run the Pipeline

In the Airflow UI:
1. Find `sg_public_transport_monthly_pipeline`
2. Toggle the DAG to "On"
3. Click "Trigger DAG" to test

## Stopping Airflow

```bash
# Stop services
docker-compose down

# Stop and remove volumes (WARNING: deletes all data)
docker-compose down -v
```

## Directory Structure

```
airflow/
├── dags/                      # DAG definitions
│   └── sg_transport_monthly_pipeline.py
├── logs/                      # Task execution logs (auto-generated)
├── plugins/                   # Custom operators (future)
├── config/
│   ├── profiles.yml          # dbt configuration
│   └── ALERTING.md           # Alerting setup guide
└── requirements.txt          # Python dependencies
```

## Viewing Logs

```bash
# Scheduler logs
docker-compose logs -f airflow-scheduler

# Webserver logs
docker-compose logs -f airflow-webserver

# All services
docker-compose logs -f
```

## Common Commands

```bash
# Rebuild image (after code changes)
docker-compose build --no-cache

# Restart services
docker-compose restart

# Access Airflow CLI
docker-compose exec airflow-webserver bash

# List DAGs
docker-compose exec airflow-webserver airflow dags list

# Test DAG
docker-compose exec airflow-webserver airflow dags test sg_public_transport_monthly_pipeline 2026-01-01
```

## Troubleshooting

**DAG not showing:**
- Check for syntax errors in `dags/sg_transport_monthly_pipeline.py`
- View scheduler logs: `docker-compose logs airflow-scheduler`

**Tasks failing:**
- Check task logs in Airflow UI
- Verify GCP credentials are mounted correctly
- Check environment variables in docker-compose.yml

**Permission errors:**
- Ensure `AIRFLOW_UID` is set correctly in `.env.airflow`
- Check volume mount permissions

## Documentation

Full documentation: `docs/phase6-airflow-setup.md`
