"""
Singapore LTA Public Transport Analytics Pipeline DAG

This DAG orchestrates the monthly data pipeline:
1. Extract data from LTA DataMall API
2. Upload to GCS
3. Load into BigQuery raw tables
4. Transform with dbt (star schema)
5. Run data quality tests

Schedule: Monthly on the 15th (after LTA releases previous month's data)
"""

from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator
from airflow.utils.task_group import TaskGroup
from airflow.utils.trigger_rule import TriggerRule

# Default arguments for all tasks
default_args = {
    'owner': 'data-engineering',
    'depends_on_past': False,
    'start_date': datetime(2026, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(hours=2),
}

# DAG definition
dag = DAG(
    'sg_public_transport_monthly_pipeline',
    default_args=default_args,
    description='Monthly pipeline for Singapore public transport analytics',
    schedule_interval='0 0 15 * *',  # Monthly on 15th at midnight
    catchup=False,
    max_active_runs=1,
    tags=['lta', 'singapore', 'transport', 'monthly'],
)

# Helper function to get data month
def get_data_month(**context):
    """Get the data month (previous month from execution date)"""
    execution_date = context['execution_date']
    data_month = execution_date - timedelta(days=execution_date.day)
    return {
        'year': data_month.year,
        'month': data_month.month,
        'year_month': data_month.strftime('%Y%m')
    }


# Start task
start = EmptyOperator(
    task_id='start',
    dag=dag,
)

# Calculate data month
calculate_data_month = PythonOperator(
    task_id='calculate_data_month',
    python_callable=get_data_month,
    dag=dag,
)

# Task Group: Data Extraction from LTA API
with TaskGroup('extract_from_lta', dag=dag) as extract_group:
    
    # Extract reference data
    extract_bus_stops = BashOperator(
        task_id='extract_bus_stops',
        bash_command="""
        cd /opt/airflow && \
        python -m src.ingestion.extract_bus_stops
        """,
        dag=dag,
    )
    
    extract_train_stations = BashOperator(
        task_id='extract_train_stations',
        bash_command="""
        cd /opt/airflow && \
        python -m src.ingestion.extract_train_stations
        """,
        dag=dag,
    )
    
    # Extract OD journey data
    extract_bus_od = BashOperator(
        task_id='extract_bus_od',
        bash_command="""
        cd /opt/airflow && \
        python -m src.ingestion.extract_bus_od \
            --year {{ ti.xcom_pull(task_ids='calculate_data_month')['year'] }} \
            --month {{ ti.xcom_pull(task_ids='calculate_data_month')['month'] }}
        """,
        dag=dag,
    )
    
    extract_train_od = BashOperator(
        task_id='extract_train_od',
        bash_command="""
        cd /opt/airflow && \
        python -m src.ingestion.extract_train_od \
            --year {{ ti.xcom_pull(task_ids='calculate_data_month')['year'] }} \
            --month {{ ti.xcom_pull(task_ids='calculate_data_month')['month'] }}
        """,
        dag=dag,
    )

# Task Group: Upload to GCS
with TaskGroup('upload_to_gcs', dag=dag) as upload_group:
    
    # Upload reference data
    upload_reference = BashOperator(
        task_id='upload_reference_data',
        bash_command="""
        cd /opt/airflow && \
        python scripts/upload_to_gcs.py --data-type reference
        """,
        dag=dag,
    )
    
    # Upload OD journey data
    upload_journeys = BashOperator(
        task_id='upload_journey_data',
        bash_command="""
        cd /opt/airflow && \
        python scripts/upload_to_gcs.py \
            --data-type journeys \
            --year {{ ti.xcom_pull(task_ids='calculate_data_month')['year'] }} \
            --month {{ ti.xcom_pull(task_ids='calculate_data_month')['month'] }}
        """,
        dag=dag,
    )

# Task Group: Load to BigQuery
with TaskGroup('load_to_bigquery', dag=dag) as load_group:
    
    # Load reference tables
    load_reference = BashOperator(
        task_id='load_reference_tables',
        bash_command="""
        cd /opt/airflow && \
        python scripts/load_to_bq.py --table-type reference
        """,
        dag=dag,
    )
    
    # Load OD tables
    load_od = BashOperator(
        task_id='load_od_tables',
        bash_command="""
        cd /opt/airflow && \
        python scripts/load_to_bq.py \
            --table-type od \
            --year {{ ti.xcom_pull(task_ids='calculate_data_month')['year'] }} \
            --month {{ ti.xcom_pull(task_ids='calculate_data_month')['month'] }}
        """,
        dag=dag,
    )

# Task Group: dbt Transformation
with TaskGroup('dbt_transform', dag=dag) as dbt_group:
    
    # Install dbt dependencies
    dbt_deps = BashOperator(
        task_id='dbt_deps',
        bash_command="""
        cd /opt/airflow/dbt && \
        dbt deps --profiles-dir /opt/airflow/config
        """,
        dag=dag,
    )
    
    # Run dbt models
    dbt_run = BashOperator(
        task_id='dbt_run',
        bash_command="""
        cd /opt/airflow/dbt && \
        dbt run --profiles-dir /opt/airflow/config
        """,
        dag=dag,
    )
    
    # Run dbt tests
    dbt_test = BashOperator(
        task_id='dbt_test',
        bash_command="""
        cd /opt/airflow/dbt && \
        dbt test --profiles-dir /opt/airflow/config
        """,
        dag=dag,
    )
    
    dbt_deps >> dbt_run >> dbt_test

# Data quality validation
validate_data_quality = BashOperator(
    task_id='validate_data_quality',
    bash_command="""
    cd /opt/airflow && \
    python -c "
import sys
from google.cloud import bigquery
import os

client = bigquery.Client(project=os.getenv('GCP_PROJECT_ID'))
dataset_id = os.getenv('BQ_DATASET')

# Check row counts
queries = {
    'fact_bus_journeys': f'SELECT COUNT(*) as cnt FROM \`{dataset_id}.fact_bus_journeys\`',
    'fact_train_journeys': f'SELECT COUNT(*) as cnt FROM \`{dataset_id}.fact_train_journeys\`',
}

for table, query in queries.items():
    result = list(client.query(query).result())[0]
    count = result.cnt
    print(f'{table}: {count:,} rows')
    if count == 0:
        print(f'ERROR: {table} is empty!')
        sys.exit(1)

print('✓ Data quality validation passed')
    "
    """,
    dag=dag,
)

# End task
end = EmptyOperator(
    task_id='end',
    trigger_rule=TriggerRule.ALL_SUCCESS,
    dag=dag,
)

# Define task dependencies
start >> calculate_data_month >> extract_group
extract_group >> upload_group
upload_group >> load_group
load_group >> dbt_group
dbt_group >> validate_data_quality
validate_data_quality >> end
