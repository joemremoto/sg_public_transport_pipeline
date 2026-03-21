# sg_public_transport_pipeline
This E2E pipeline extracts train and bus demand data from Singapore's Land Transport Authority and loads them into GCS, transforms the data using dbt, then ingests the data into BigQuery. After which, the marts tables will be used to create visualizations.

This serves as my capstone project for the Data Engineering Zoomcamp 2026 Cohort.
