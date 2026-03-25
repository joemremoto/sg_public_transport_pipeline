# Data Extraction Scripts - Checkpoint

> **Date:** March 25, 2026  
> **Phase:** Data Ingestion  
> **Status:** ✅ Complete

---

## Overview

This document summarizes the four data extraction scripts created for the Singapore Public Transport Analytics Pipeline. These scripts fetch raw data from LTA DataMall and save it locally for further processing.

---

## 📊 Data Extraction Architecture

### Data Types

We extract two categories of data:

**1. Dimension Data (Static/Reference)**
- Bus stops - WHERE bus journeys happen
- Train stations - WHERE train journeys happen
- Rarely changes, small size, foundational

**2. Fact Data (Transactional/Dynamic)**
- Bus OD (Origin-Destination) - HOW MANY journeys per route
- Train OD - HOW MANY journeys per route
- Monthly updates, large size, analytical focus

---

## 🚌 Script 1: Extract Bus Stops

**File:** `src/ingestion/extract_bus_stops.py`

### Purpose
Fetches all bus stop information from LTA DataMall API, including location coordinates, names, and codes.

### Data Source
- **Method:** REST API endpoint
- **Endpoint:** `/BusStops`
- **Authentication:** API key required
- **Format:** JSON response

### Key Features
- **Pagination handling** - Fetches 500 stops per request
- **Automatic retry logic** - Inherits from `LTAClient`
- **Context manager support** - Clean HTTP session management
- **Detailed logging** - Progress tracking for each page

### Output
- **File:** `data/raw/bus_stops.json`
- **Size:** ~921 KB
- **Records:** 5,202 bus stops
- **Format:** JSON array

### Data Structure
```json
{
  "BusStopCode": "01012",
  "RoadName": "Victoria St",
  "Description": "Hotel Grand Pacific",
  "Latitude": 1.29684825487647,
  "Longitude": 103.85253591654006
}
```

### Usage
```bash
uv run python src/ingestion/extract_bus_stops.py
```

### Technical Highlights
- Demonstrates API pagination pattern
- Pure API-based extraction
- No external file downloads
- Fast execution (~2-3 seconds)

---

## 🚂 Script 2: Extract Train Stations

**File:** `src/ingestion/extract_train_stations.py`

### Purpose
Downloads train station codes and names (English + Chinese) from LTA DataMall's website.

### Data Source
- **Method:** Direct file download
- **URL:** https://datamall.lta.gov.sg/.../Train%20Station%20Codes%20and%20Chinese%20Names.zip
- **Authentication:** None required
- **Format:** ZIP containing Excel (.xls)

### Key Features
- **In-memory processing** - No temp files created
- **Excel parsing** - Uses pandas with xlrd engine
- **ZIP extraction** - Handles compressed downloads
- **Multilingual support** - Preserves Chinese characters

### Output
- **File:** `data/raw/train_stations.json`
- **Size:** ~20 KB
- **Records:** 166 train stations
- **Format:** JSON array

### Data Structure
```json
{
  "station_code": "NS1",
  "station_name": "Jurong East",
  "station_name_chinese": "裕廊东"
}
```

### Usage
```bash
uv run python src/ingestion/extract_train_stations.py
```

### Technical Highlights
- Demonstrates file download + extraction pattern
- Excel file parsing with pandas
- In-memory ZIP handling (efficient)
- Cross-format conversion (Excel → JSON)

### Dependencies Added
- `xlrd` - For reading .xls files

---

## 🚌 Script 3: Extract Bus OD Data

**File:** `src/ingestion/extract_bus_od.py`

### Purpose
Downloads monthly aggregated bus journey data showing trip counts between origin-destination pairs.

### Data Source
- **Method:** REST API endpoint (returns S3 download link)
- **Endpoint:** `/PV/ODBus`
- **Authentication:** API key required
- **Format:** ZIP containing CSV

### Key Features
- **Command line interface** - Accepts year/month parameters
- **Smart defaults** - Uses previous month if no args provided
- **Date validation** - Prevents invalid/future dates
- **Large file handling** - Efficiently processes multi-MB files
- **Link expiration aware** - Downloads immediately (5-min expiry)

### Output
- **File:** `data/raw/bus_od_YYYYMM.csv`
- **Example:** `data/raw/bus_od_202601.csv`
- **Size:** ~150 MB (compressed), ~500 MB (uncompressed)
- **Records:** ~6 million rows (Jan 2026)
- **Format:** CSV

### Data Structure
```csv
YEAR_MONTH,DAY_TYPE,TIME_PER_HOUR,PT_TYPE,ORIGIN_PT_CODE,DESTINATION_PT_CODE,TOTAL_TRIPS
2026-01,WEEKDAY,9,BUS,16069,14169,11
```

**Columns Explained:**
- `YEAR_MONTH` - Data period (e.g., 2026-01)
- `DAY_TYPE` - WEEKDAY or WEEKENDS/HOLIDAY
- `TIME_PER_HOUR` - Hour bucket (0-23, where 9 = 9 AM)
- `PT_TYPE` - Public transport type (always BUS for this file)
- `ORIGIN_PT_CODE` - Starting bus stop code
- `DESTINATION_PT_CODE` - Ending bus stop code
- `TOTAL_TRIPS` - Number of journeys for this OD pair

### Usage
```bash
# Specific month
uv run python src/ingestion/extract_bus_od.py --year 2026 --month 1

# Default (previous month)
uv run python src/ingestion/extract_bus_od.py
```

### Technical Highlights
- Demonstrates command-line argument parsing
- Handles large CSV files efficiently
- API returns S3 pre-signed URL
- Pre-aggregated data (already summarized by LTA)

### Important Constraints
- ⚠️ Only last **3 months** of data available
- ⚠️ Data published ~10th of following month
- ⚠️ Download links expire after **5 minutes**
- ℹ️ One file per month (cannot get daily/weekly)

---

## 🚂 Script 4: Extract Train OD Data

**File:** `src/ingestion/extract_train_od.py`

### Purpose
Downloads monthly aggregated train journey data showing trip counts between station pairs.

### Data Source
- **Method:** REST API endpoint (returns S3 download link)
- **Endpoint:** `/PV/ODTrain`
- **Authentication:** API key required
- **Format:** ZIP containing CSV

### Key Features
- **Identical to bus OD** - Same CLI interface and workflow
- **Smaller dataset** - Fewer stations = fewer OD pairs
- **Same constraints** - 3-month history, monthly updates

### Output
- **File:** `data/raw/train_od_YYYYMM.csv`
- **Example:** `data/raw/train_od_202601.csv`
- **Size:** ~25 MB (compressed), ~100 MB (uncompressed)
- **Records:** ~884k rows (Jan 2026) - 7× smaller than bus
- **Format:** CSV

### Data Structure
```csv
YEAR_MONTH,DAY_TYPE,TIME_PER_HOUR,PT_TYPE,ORIGIN_PT_CODE,DESTINATION_PT_CODE,TOTAL_TRIPS
2026-01,WEEKDAY,12,TRAIN,CC27,NE16/STC,77
```

**Notable Differences from Bus:**
- `PT_TYPE` is always TRAIN
- Station codes include line prefixes (NS, EW, CC, etc.)
- **Interchange stations** use slash notation (e.g., `NE16/STC`)
- Higher trip volumes per OD pair (fewer alternatives)

### Usage
```bash
# Specific month
uv run python src/ingestion/extract_train_od.py --year 2026 --month 1

# Default (previous month)
uv run python src/ingestion/extract_train_od.py
```

### Technical Highlights
- Nearly identical code to bus OD (reusable pattern)
- Handles interchange station codes
- Smaller data volume = faster processing

---

## 📊 Data Summary

### Files Extracted (January 2026)

| File | Type | Size | Records | Source |
|------|------|------|---------|--------|
| `bus_stops.json` | Dimension | 921 KB | 5,202 | API |
| `train_stations.json` | Dimension | 20 KB | 166 | ZIP (Excel) |
| `bus_od_202601.csv` | Fact | ~150 MB | 5.9M | API → ZIP (CSV) |
| `train_od_202601.csv` | Fact | ~25 MB | 884k | API → ZIP (CSV) |

### Scale Comparison

**Bus vs Train Network:**
- Bus stops: **31×** more than train stations
- Bus OD records: **7×** more than train OD records
- Bus has more routes, alternatives, and coverage

**Storage Implications:**
- Dimension data: Small, easily cached
- Fact data: Large, requires partitioning strategy
- Monthly OD data grows by ~175 MB/month

---

## 🎓 Technical Patterns Demonstrated

### 1. API Pagination
**File:** `extract_bus_stops.py`

```python
skip = 0
page_size = 500
while True:
    response = client.get_bus_stops(skip=skip)
    stops = response.get('value', [])
    all_stops.extend(stops)
    
    if len(stops) < page_size:
        break
    skip += page_size
```

### 2. In-Memory File Processing
**Files:** All extraction scripts

```python
# No temp files created!
zip_buffer = io.BytesIO(zip_content)
with zipfile.ZipFile(zip_buffer, 'r') as zip_ref:
    content = zip_ref.read('file.csv')
```

### 3. Command Line Arguments
**Files:** `extract_bus_od.py`, `extract_train_od.py`

```python
parser = argparse.ArgumentParser()
parser.add_argument('--year', type=int)
parser.add_argument('--month', type=int)
args = parser.parse_args()
```

### 4. Date Validation
**Files:** OD extraction scripts

```python
def validate_year_month(year: int, month: int):
    if not 1 <= month <= 12:
        raise ValueError("Invalid month")
    if datetime(year, month, 1) > datetime.now():
        raise ValueError("Cannot request future data")
```

### 5. Error Handling
**All scripts:**

```python
try:
    # Operation
except SpecificError as e:
    logger.error(f"Specific problem: {e}")
    raise
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    traceback.print_exc()
    exit(1)
```

---

## 🔄 Running the Complete Extraction

### Extract All Data for January 2026

```bash
# 1. Dimension data (run once, rarely changes)
uv run python src/ingestion/extract_bus_stops.py
uv run python src/ingestion/extract_train_stations.py

# 2. Fact data (run monthly for new data)
uv run python src/ingestion/extract_bus_od.py --year 2026 --month 1
uv run python src/ingestion/extract_train_od.py --year 2026 --month 1
```

### Expected Runtime
- Bus stops: ~3 seconds
- Train stations: ~2 seconds
- Bus OD: ~10-20 seconds (depends on download speed)
- Train OD: ~5-10 seconds

**Total:** < 1 minute for complete extraction

---

## ⚠️ Important Considerations

### Data Freshness
- **OD data lag:** Published ~10th of following month
- **Current limitation:** Can only get last 3 months
- **Planning:** Must run monthly to avoid data loss

### API Constraints
- **Rate limiting:** Not documented, but be respectful
- **Download links:** Expire after 5 minutes
- **Timeouts:** Set to 30 seconds (configurable)

### Data Quality
- **Pre-aggregated:** Already summarized by LTA
  - ✅ Pro: Ready for analysis
  - ⚠️ Con: Cannot get individual transaction details
- **Time granularity:** Hourly buckets only
  - Cannot analyze minute-level patterns
- **Interchange stations:** Need special handling (slash notation)

### Storage Requirements
- **Per month:** ~175 MB raw data
- **12 months:** ~2.1 GB
- **+ Dimension data:** ~1 MB (negligible)
- **Recommendation:** Implement data lifecycle policy

---

## 🚀 Next Steps

With extraction complete, the next phases are:

### 1. Data Upload to GCS
- Create scripts to upload raw data to Google Cloud Storage
- Organize by date partitions
- Set up folder structure

### 2. BigQuery Schema Design
- Define dimension tables (bus stops, train stations, dates, time periods)
- Define fact tables (bus journeys, train journeys)
- Implement surrogate keys and relationships

### 3. Data Transformation (dbt)
- Clean and validate raw data
- Apply business logic
- Create aggregated views
- Implement data quality tests

### 4. Orchestration (Airflow)
- Schedule monthly extraction
- Chain extraction → upload → transformation
- Add monitoring and alerts

### 5. Visualization (Streamlit)
- Build interactive dashboard
- Show journey patterns by time/route
- Compare bus vs train usage

---

## 📝 Lessons Learned

### What Went Well
1. **Modular design** - Each script has single responsibility
2. **Consistent patterns** - Easy to understand and maintain
3. **Thorough documentation** - Beginner-friendly comments
4. **Robust error handling** - Clear messages when things fail
5. **Efficient processing** - In-memory operations, no temp files

### Challenges Overcome
1. **Excel file format** - Initially expected CSV, got .xls
   - **Solution:** Added pandas + xlrd for Excel parsing
2. **Attribute naming** - Used `RAW_DATA_PATH` instead of `RAW_DATA_DIR`
   - **Solution:** Fixed script to match config
3. **Date constraints** - LTA's 3-month window not obvious
   - **Solution:** Added validation and helpful warnings

### Key Insights
1. **Bus network is massive** - 5,202 stops vs 166 train stations
2. **Data is pre-aggregated** - Already in analytical format
3. **Interchange complexity** - Train stations serve multiple lines
4. **File sizes matter** - Bus OD is 7× larger than train OD

---

## 📚 File Reference

### Created Files

**Scripts:**
- `src/ingestion/extract_bus_stops.py` (309 lines)
- `src/ingestion/extract_train_stations.py` (433 lines)
- `src/ingestion/extract_bus_od.py` (407 lines)
- `src/ingestion/extract_train_od.py` (380 lines)

**Data Files (for Jan 2026):**
- `data/raw/bus_stops.json`
- `data/raw/train_stations.json`
- `data/raw/bus_od_202601.csv`
- `data/raw/train_od_202601.csv`

**Documentation:**
- `docs/setup-log.md` - Initial setup and foundation
- `docs/data-extraction-checkpoint.md` - This document

### Supporting Files
- `src/config/settings.py` - Configuration management
- `src/ingestion/lta_client.py` - API client
- `tests/test_api_connection.py` - API validation
- `.env` - Environment variables (git-ignored)
- `pyproject.toml` - Dependencies

---

## ✅ Checkpoint Status

**Phase:** Data Extraction  
**Status:** ✅ Complete  
**Date:** March 25, 2026

**Achievements:**
- ✅ Created 4 extraction scripts
- ✅ Successfully extracted dimension data
- ✅ Successfully extracted fact data (Jan 2026)
- ✅ All scripts tested and working
- ✅ Documentation complete

**Ready for next phase:** Data Upload to GCS

---

**Last updated:** March 25, 2026  
**Session:** 2 of pipeline development  
**Next session:** GCS upload scripts + Terraform infrastructure
