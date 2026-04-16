FROM apache/airflow:2.10.4-python3.10

USER root

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER airflow

# Use Airflow's constraint file to avoid dependency resolution issues
ENV AIRFLOW_VERSION=2.10.4
ENV PYTHON_VERSION=3.10
ENV CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"

# Copy and install Python requirements with constraints
COPY airflow/requirements.txt /requirements.txt
RUN pip install --no-cache-dir --disable-pip-version-check -r /requirements.txt --constraint "${CONSTRAINT_URL}"

# Install the project source as a package
COPY --chown=airflow:root src /opt/airflow/src
ENV PYTHONPATH="${PYTHONPATH}:/opt/airflow/src:/opt/airflow"
