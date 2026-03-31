# Airflow Quick Reference

Quick commands and operations for the Singapore LTA Pipeline Airflow setup.

---

## Start/Stop

```bash
# Build image
docker-compose build

# Initialize (first time only)
docker-compose up airflow-init

# Start services
docker-compose up -d

# Stop services
docker-compose down

# Stop and remove all data
docker-compose down -v
```

---

## Access

- **Web UI:** http://localhost:8080
- **Username:** admin
- **Password:** admin

---

## Monitoring

```bash
# Check service status
docker-compose ps

# View scheduler logs
docker-compose logs -f airflow-scheduler

# View webserver logs
docker-compose logs -f airflow-webserver

# View all logs
docker-compose logs -f
```

---

## DAG Operations

```bash
# Access Airflow CLI
docker-compose exec airflow-webserver bash

# List DAGs
airflow dags list

# Show DAG details
airflow dags show sg_public_transport_monthly_pipeline

# Test DAG (dry run)
airflow dags test sg_public_transport_monthly_pipeline 2026-01-01

# Trigger DAG manually
airflow dags trigger sg_public_transport_monthly_pipeline

# List DAG runs
airflow dags list-runs -d sg_public_transport_monthly_pipeline
```

---

## Task Operations

```bash
# List tasks in DAG
airflow tasks list sg_public_transport_monthly_pipeline

# Show task details
airflow tasks show sg_public_transport_monthly_pipeline extract_from_lta.extract_bus_od

# Test single task
airflow tasks test sg_public_transport_monthly_pipeline \
  extract_from_lta.extract_bus_od 2026-01-01

# View task logs
airflow tasks logs sg_public_transport_monthly_pipeline \
  extract_from_lta.extract_bus_od 2026-01-01
```

---

## Backfilling

```bash
# Backfill December 2025
airflow dags backfill sg_public_transport_monthly_pipeline \
  --start-date 2025-12-01 \
  --end-date 2025-12-31

# Backfill with specific task
airflow dags backfill sg_public_transport_monthly_pipeline \
  --start-date 2026-01-01 \
  --end-date 2026-01-31 \
  --task-regex "dbt.*"
```

---

## Troubleshooting

```bash
# Check database connection
docker-compose exec airflow-webserver airflow db check

# Reset database (DANGER!)
docker-compose exec airflow-webserver airflow db reset

# Clear task instance state
airflow tasks clear sg_public_transport_monthly_pipeline

# Check configuration
airflow config list
```

---

## Development

```bash
# Rebuild after code changes
docker-compose build --no-cache

# Restart services
docker-compose restart

# Access Python shell with Airflow context
docker-compose exec airflow-webserver python
```

---

## File Locations in Container

| Path | Purpose |
|------|---------|
| /opt/airflow/dags | DAG definitions |
| /opt/airflow/logs | Task execution logs |
| /opt/airflow/src | Python source code |
| /opt/airflow/dbt | dbt project |
| /opt/airflow/credentials | GCP service account |
| /opt/airflow/data | Local data storage |

---

## Common Issues

**Issue:** DAG not appearing
```bash
# Check for syntax errors
docker-compose logs airflow-scheduler | grep ERROR
```

**Issue:** Task stuck in running
```bash
# View task logs in UI or:
airflow tasks logs sg_public_transport_monthly_pipeline <task_id> <execution_date>
```

**Issue:** Permission denied
```bash
# Check AIRFLOW_UID in .env.airflow matches host user
echo $AIRFLOW_UID
```

**Issue:** Can't connect to GCP
```bash
# Verify credentials are mounted
docker-compose exec airflow-webserver ls /opt/airflow/credentials
```

---

## Documentation

- Full Setup: `docs/phase6-airflow-setup.md`
- Testing: `docs/phase6-testing-checklist.md`
- Quick Start: `airflow/README.md`
- Alerting: `airflow/config/ALERTING.md`
