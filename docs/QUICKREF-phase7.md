# Streamlit Dashboard Quick Reference

Quick guide for running and using the Singapore Public Transport Analytics Dashboard.

---

## Quick Start

```bash
# Install dependencies
cd streamlit_app
pip install -r requirements.txt

# Run dashboard
streamlit run app.py
```

Dashboard opens at: http://localhost:8501

---

## Dashboard Controls

### Sidebar Filters

| Control | Type | Options | Default |
|---------|------|---------|---------|
| Transport Mode | Radio | Train, Bus | Train |
| Year-Month | Dropdown | Available months | Latest |
| Day Type | Dropdown | WEEKDAY, WEEKENDS/HOLIDAY | WEEKDAY |
| Filter by Origins | Checkbox | Enable/disable | Disabled |
| Select Origins | Multi-select | Stations/stops list | All |
| Top N Origins | Slider | 10-50 | 20 |

### Main View

**Metrics Row:**
- Total Trips
- Avg Trips per Origin
- Busiest Origin

**Visualizations:**
1. Trip Count by Origin (horizontal bar chart)
2. Trip Count by Time Period (24-hour bar chart)

---

## Common Tasks

### View Train Weekday Patterns
1. Select "Train" mode
2. Choose year-month
3. Select "WEEKDAY"
4. View charts

### Compare Specific Stops
1. Enable "Filter by specific origins"
2. Select stops from multi-select
3. Charts update automatically

### Analyze Peak Hours
1. Select any mode
2. Choose WEEKDAY
3. Look at time period chart
4. Red bars = peak hours (7-8am, 5-7pm)

### Export Data
1. Click expander under each chart
2. "View Data Table" shows raw data
3. Copy/paste or screenshot

---

## Troubleshooting

**Dashboard won't start:**
```bash
# Check dependencies installed
pip list | grep streamlit

# Reinstall if needed
pip install -r requirements.txt
```

**No data showing:**
- Verify `.env` file has correct credentials
- Check BigQuery dataset exists
- Test credentials: `gcloud auth application-default login`

**Slow loading:**
- Wait for cache (first load takes 3-5s)
- Subsequent loads < 1s
- Reduce Top N slider value

**Clear cache:**
- Press `C` key in dashboard
- Or restart: Ctrl+C, then re-run

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| C | Clear cache |
| R | Rerun app |
| ? | Show keyboard shortcuts |

---

## File Locations

| Path | Purpose |
|------|---------|
| `streamlit_app/app.py` | Main app |
| `streamlit_app/utils/bigquery_client.py` | Queries |
| `.env` | Credentials |
| `.streamlit/config.toml` | Theme |

---

## Documentation

- Full Setup: `docs/phase7-streamlit-setup.md`
- User Guide: `streamlit_app/README.md`
- Architecture: `docs/architecture.md`
