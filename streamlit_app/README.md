# Singapore Public Transport Analytics Dashboard

Interactive Streamlit dashboard for visualizing LTA public transport journey data.

## Features

### Current Visualizations

1. **Trip Count by Origin**
   - Bar chart showing top N busiest stations/stops
   - Horizontal layout for easy reading
   - Color-coded by trip volume

2. **Trip Count by Time Period**
   - 24-hour trip distribution
   - Peak hour highlighting (red for peak, blue for off-peak)
   - Hourly breakdown

### Filters

- **Mode:** Switch between Train and Bus data
- **Year-Month:** Select which month to analyze
- **Day Type:** Filter by WEEKDAY or WEEKENDS/HOLIDAY
- **Origin Filter:** Optionally filter by specific stations/stops
- **Top N:** Adjust number of origins displayed (10-50)

### Key Metrics

- Total trips for selected filters
- Average trips per origin
- Busiest origin location

## Setup

### Prerequisites

- Python 3.10+
- GCP service account credentials with BigQuery access
- Environment variables configured

### Installation

```bash
# Navigate to streamlit_app directory
cd streamlit_app

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create or link `.env` file in the project root:

```bash
GOOGLE_APPLICATION_CREDENTIALS=./credentials/gcp-service-account.json
GCP_PROJECT_ID=sg-public-transport-pipeline
BQ_DATASET=sg_public_transport_analytics
```

## Running the Dashboard

### Local Development

```bash
# From project root
streamlit run streamlit_app/app.py

# Or from streamlit_app directory
streamlit run app.py
```

The dashboard will open automatically at http://localhost:8501

### Command Line Options

```bash
# Custom port
streamlit run app.py --server.port 8502

# Disable browser auto-open
streamlit run app.py --server.headless true
```

## Project Structure

```
streamlit_app/
├── app.py                  # Main Streamlit application
├── requirements.txt        # Python dependencies
├── .streamlit/
│   └── config.toml        # Streamlit configuration
├── utils/
│   └── bigquery_client.py # BigQuery connection and queries
└── README.md              # This file
```

## Data Model

The dashboard queries the following BigQuery tables:

**Fact Tables:**
- `fact_bus_journeys` (17.6M rows)
- `fact_train_journeys` (1.7M rows)

**Dimension Tables:**
- `dim_bus_stops` (5.2k rows)
- `dim_train_stations` (213 rows)
- `dim_time_period` (24 rows)

## Performance

- **Caching:** BigQuery queries are cached for 1 hour (`@st.cache_data(ttl=3600)`)
- **Query Optimization:** Uses clustered columns (origin_key, time_period_key)
- **Data Limits:** Origin visualization limited to top 50 to maintain performance

## Troubleshooting

### "Failed to connect to BigQuery"

Ensure `GOOGLE_APPLICATION_CREDENTIALS` points to a valid service account JSON file with BigQuery access.

**Fix Option 1 (Recommended):** Use the local `.env` file in `streamlit_app` directory (already created).

**Fix Option 2:** Set absolute path in environment variable:
```powershell
# In PowerShell (from project root)
$env:GOOGLE_APPLICATION_CREDENTIALS="C:\Users\JosephEmmanuelRemoto\hellofresh_gh\sg_public_transport_pipeline\credentials\gcp-service-account.json"

# Then run Streamlit
cd streamlit_app
streamlit run app.py
```

**Fix Option 3:** Use gcloud default credentials:
```powershell
gcloud auth application-default login
```
Then remove `GOOGLE_APPLICATION_CREDENTIALS` from `.env` to use default auth.

### "No data available"

Check that:
1. BigQuery dataset exists and contains data
2. Dataset name matches `BQ_DATASET` in `.env`
3. Service account has `BigQuery Data Viewer` role

### Slow loading

- Reduce `top_n` value in sidebar
- Check BigQuery query costs in GCP Console
- Verify data is partitioned and clustered correctly

## Future Enhancements

Potential additions (not yet implemented):

- Geospatial map visualization
- Destination analysis
- Time series trends
- Mode comparison side-by-side
- Export functionality
- Custom date range selection

## Documentation

- **Architecture:** `docs/architecture.md`
- **Phase 7 Setup:** `docs/phase7-streamlit-setup.md` (coming soon)
- **Project Status:** `docs/current-status.md`

## Tech Stack

- **Frontend:** Streamlit 1.41.1
- **Visualization:** Plotly 5.24.1, Altair 5.5.0
- **Data:** Google BigQuery via google-cloud-bigquery
- **Processing:** Pandas 2.2.3

---

Built as part of the Singapore Public Transport Analytics Pipeline - Phase 7
