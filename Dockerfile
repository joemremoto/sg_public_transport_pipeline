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

# Copy and install Python requirements
COPY airflow/requirements.txt /requirements.txt
RUN pip install --no-cache-dir --disable-pip-version-check -r /requirements.txt

# Install the project source as a package
COPY --chown=airflow:root src /opt/airflow/src
ENV PYTHONPATH="${PYTHONPATH}:/opt/airflow/src:/opt/airflow"
