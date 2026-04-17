# Pipeline Glossary - Key Terms Explained

A beginner-friendly reference for understanding all the technical terms used in the Singapore LTA Public Transport Analytics Pipeline.

---

## Table of Contents

- [Tech Stack Tools](#tech-stack-tools)
- [Python Packages](#python-packages)
- [Data Engineering Concepts](#data-engineering-concepts)
- [Data Modeling Concepts](#data-modeling-concepts)
- [API & Web Concepts](#api--web-concepts)
- [Cloud & Infrastructure](#cloud--infrastructure)
- [General Computer Science](#general-computer-science)

---

## Tech Stack Tools

### Apache Airflow

**What it is:** A workflow orchestration platform that schedules and monitors data pipelines.

**Analogy:** Think of it as a project manager that knows when to run each task, in what order, and what to do if something fails.

**In our project:** Runs our pipeline monthly on the 10th, downloading data → uploading to GCS → triggering dbt transformations.

**Key concepts:**

- **DAG (Directed Acyclic Graph):** A workflow definition showing tasks and their dependencies
- **Task:** A single unit of work (e.g., "download bus data")
- **Operator:** The type of task (e.g., PythonOperator, BashOperator)

---

### dbt (data build tool)

**What it is:** A transformation tool that helps you write modular SQL queries to transform raw data into analytics-ready tables.

**Analogy:** Like a recipe book for data - it takes raw ingredients (CSV data) and transforms them into finished dishes (fact/dimension tables).

**In our project:** Transforms raw LTA CSV files into our star schema (dimensions and facts) in BigQuery.

**Key concepts:**

- **Model:** A SQL file that creates a table or view
- **Staging:** First layer - cleans and standardizes raw data
- **Marts:** Final layer - business-ready fact and dimension tables

---

### Docker

**What it is:** A platform that packages applications and their dependencies into isolated containers.

**Analogy:** Like shipping containers - your code runs the same way whether on your laptop, a server, or the cloud.

**In our project:** Each component (Airflow, Python scripts, Streamlit) runs in its own container for consistency.

**Key concepts:**

- **Container:** A running instance of an image
- **Image:** A blueprint/template for a container
- **Dockerfile:** Instructions for building an image
- **docker-compose:** Tool for running multiple containers together

---

### Terraform

**What it is:** Infrastructure as Code (IaC) tool that provisions cloud resources using configuration files.

**Analogy:** Like LEGO instructions - you write what infrastructure you want (in code), and Terraform builds it for you.

**In our project:** Creates our GCS buckets, BigQuery datasets, and other Google Cloud resources.

**Key concepts:**

- **Resource:** A piece of infrastructure (e.g., a GCS bucket)
- **Provider:** Plugin for a cloud platform (e.g., Google Cloud)
- **State:** Terraform's record of what infrastructure exists
- **Plan:** Preview of what changes Terraform will make

---

### BigQuery

**What it is:** Google's fully-managed, serverless data warehouse optimized for analytics.

**Analogy:** Like a super-fast library specifically designed for looking up information in huge datasets.

**In our project:** Stores our final fact and dimension tables for querying and analysis.

**Key features:**

- Columnar storage (very fast for analytics)
- Scales automatically to handle large datasets
- SQL-based querying
- Pay only for queries you run

---

### Google Cloud Storage (GCS)

**What it is:** Google's object storage service, similar to Amazon S3.

**Analogy:** Like a massive hard drive in the cloud where you can store any type of file.

**In our project:** Stores raw CSV files from LTA API in a data lake structure (organized by year/month/mode).

**Key concepts:**

- **Bucket:** A container for storing objects (like a top-level folder)
- **Object:** A file stored in GCS
- **Path:** Where an object is located (e.g., `raw/bus/2024/01/data.csv`)

---

### Streamlit

**What it is:** Python framework for building interactive web dashboards without HTML/CSS/JavaScript.

**Analogy:** Like PowerPoint but interactive and powered by live data from your database.

**In our project:** Creates the visualization layer showing charts, maps, and insights from BigQuery data.

**Key features:**

- Pure Python (no web development needed)
- Automatic updates when data changes
- Interactive widgets (sliders, dropdowns, etc.)

---

### uv

**What it is:** Modern Python package manager, faster alternative to pip.

**Analogy:** Like an app store manager for Python libraries - installs, updates, and tracks what your project needs.

**In our project:** Manages all Python dependencies (requests, pandas, etc.) via `pyproject.toml`.

**Key commands:**

- `uv add package-name` - Install a package
- `uv sync` - Install all dependencies from pyproject.toml
- `uv run python script.py` - Run Python in the correct environment

---

## Python Packages

### requests

**What it is:** Library for making HTTP requests in Python.

**Purpose:** Talking to APIs - sending requests and receiving responses.

**In our project:** Used to call LTA DataMall API endpoints to download data.

**Example:**

```python
import requests
response = requests.get('https://api.example.com/data')
```

---

### pandas

**What it is:** Powerful library for data manipulation and analysis.

**Analogy:** Like Excel but in code - work with tables (DataFrames) of data.

**In our project:** Reading CSV files, cleaning data, transforming before uploading to BigQuery.

**Key concepts:**

- **DataFrame:** 2D table with rows and columns
- **Series:** Single column of data
- **read_csv():** Load CSV into DataFrame

---

### zipfile

**What it is:** Built-in Python library for working with ZIP archives.

**Purpose:** Extracting files from ZIP archives without manual unzipping.

**In our project:** LTA API returns ZIP files - we use zipfile to extract CSVs programmatically.

---

### dotenv (python-dotenv)

**What it is:** Library that loads environment variables from a `.env` file.

**Purpose:** Keep secrets (API keys, passwords) out of your code.

**In our project:** Loads `LTA_ACCOUNT_KEY` and other sensitive config from `.env` file.

---

### google-cloud-storage

**What it is:** Official Python client for Google Cloud Storage.

**Purpose:** Upload/download files to/from GCS buckets using Python.

**In our project:** Uploads extracted CSV files to our GCS data lake.

---

### logging

**What it is:** Built-in Python library for recording program events.

**Purpose:** Better than print statements - logs can have levels (INFO, ERROR) and go to files.

**In our project:** Tracks pipeline progress, logs errors for debugging.

---

## Data Engineering Concepts

### ETL (Extract, Transform, Load)

**What it is:** The process of moving data from source systems to analytics destinations.

**Breakdown:**

- **Extract:** Get data from sources (LTA API)
- **Transform:** Clean, reshape, aggregate data (dbt models)
- **Load:** Put data into destination (BigQuery)

**In our project:** We follow ELT (Extract, Load, Transform) - load raw data first, then transform in warehouse.

---

### Data Pipeline

**What it is:** Automated workflow that moves and transforms data from source to destination.

**Analogy:** Like an assembly line in a factory - data flows through stages, getting processed at each step.

**In our project:** LTA API → GCS → dbt → BigQuery → Streamlit

---

### Data Lake

**What it is:** Storage repository that holds raw data in its native format.

**vs Data Warehouse:** Lake = raw/unstructured (like a pond with everything), Warehouse = cleaned/structured (like organized shelves)

**In our project:** GCS stores raw CSV files in a data lake structure (partitioned by date/mode).

---

### Data Warehouse

**What it is:** Central repository optimized for analytics, stores structured data.

**Analogy:** Like a well-organized library where data is indexed for fast lookups.

**In our project:** BigQuery is our warehouse holding transformed fact/dimension tables.

---

### Orchestration

**What it is:** Coordinating and scheduling multiple tasks/systems to work together.

**Analogy:** Like a conductor directing an orchestra - ensures each instrument plays at the right time.

**In our project:** Airflow orchestrates our entire pipeline execution.

---

### Partitioning

**What it is:** Dividing large datasets into smaller, manageable pieces based on a key (usually date).

**Benefits:**

- Faster queries (only scan relevant partitions)
- Easier management (delete old partitions)
- Cost savings (don't process unnecessary data)

**In our project:** 

- Files partitioned by year/month: `raw/bus/2024/03/`
- BigQuery tables partitioned by date

---

### Batch Processing

**What it is:** Processing data in large chunks at scheduled intervals (vs real-time streaming).

**Example:** Processing all of March's data on April 10th.

**In our project:** Pipeline runs monthly when new data is published (batch, not real-time).

---

## Data Modeling Concepts

### Data Model

**What it is:** A blueprint showing how data is structured, stored, and related.

**Analogy:** Like an architect's floor plan for a building, but for data.

**Common types:**

- **Star Schema** (what we use)
- **Snowflake Schema**
- **3NF (Third Normal Form)**

---

### Star Schema

**What it is:** Data model with central fact table(s) connected to dimension tables.

**Visual:**

```
        dim_date
            |
dim_bus_stops -- fact_bus_journeys -- dim_time_period
            |
        dim_route
```

**Why "Star"?** Looks like a star with fact table in the center.

**Benefits:**

- Simple to understand
- Fast queries (fewer joins)
- Great for analytics

**In our project:** Our main data model structure.

---

### Fact Table

**What it is:** Table storing measurable events or transactions (the "facts" of the business).

**Characteristics:**

- Contains numeric measures (e.g., trip_count, revenue, quantity)
- Contains foreign keys to dimension tables
- Usually has many rows (one per event)

**In our project:**

- `fact_bus_journeys` - records of bus trips
- `fact_train_journeys` - records of train trips
- Measures: trip_count

---

### Dimension Table

**What it is:** Table storing descriptive attributes about business entities.

**Characteristics:**

- Contains text descriptions (e.g., bus stop names, station names)
- Fewer rows than fact tables
- Used for filtering and grouping in analysis

**In our project:**

- `dim_bus_stops` - information about each bus stop
- `dim_train_stations` - information about each train station
- `dim_date` - date attributes (year, month, day, is_weekend)
- `dim_time_period` - time of day classifications

---

### Surrogate Key

**What it is:** An artificial identifier (usually integer) used as primary key instead of natural key.

**vs Natural Key:** 

- Natural: Actual business identifier (e.g., bus_stop_code = "83139")
- Surrogate: Generated number (e.g., bus_stop_key = 1, 2, 3...)

**Benefits:**

- Smaller size (integers are compact)
- Stable (won't change if business key changes)
- Better join performance

**In our project:** All dimension tables use surrogate keys (e.g., `bus_stop_key`, `station_key`).

---

### Foreign Key

**What it is:** A field in one table that refers to the primary key of another table.

**Purpose:** Creates relationships between tables.

**Example:** `fact_bus_journeys.origin_bus_stop_key` → `dim_bus_stops.bus_stop_key`

**In our project:** Fact tables have multiple foreign keys linking to dimensions.

---

### Grain (of a fact table)

**What it is:** The level of detail stored in each row of a fact table.

**Question to ask:** "What does one row represent?"

**In our project:** 

- Grain = one origin-destination pair, for one hour, on one day type
- Example row: Bus stop A → Bus stop B, hour 8, weekday, 150 trips

---

### SCD (Slowly Changing Dimension)

**What it is:** Strategy for handling changes in dimension attributes over time.

**Types:**

- **Type 1:** Overwrite (don't track history)
- **Type 2:** Add new row (track full history)
- **Type 3:** Add new column (track limited history)

**In our project:** We use Type 1 (overwrite) for bus stops and stations.

---

## API & Web Concepts

### API (Application Programming Interface)

**What it is:** A way for programs to talk to each other - defines what requests you can make and what responses you get.

**Analogy:** Like a restaurant menu:

- Menu = API documentation
- Your order = API request
- Food delivered = API response

**In our project:** LTA DataMall API provides programmatic access to transport data.

---

### Endpoint

**What it is:** A specific URL where an API can be accessed for a particular resource.

**Format:** Base URL + path

**Examples from our project:**

- Bus OD data: `http://datamall2.mytransport.sg/ltaodataservice/PV/ODBus`
- Train OD data: `http://datamall2.mytransport.sg/ltaodataservice/PV/ODTrain`
- Bus stops: `http://datamall2.mytransport.sg/ltaodataservice/BusStops`

---

### HTTP Request

**What it is:** Message sent from client (your code) to server (API) asking for something.

**Common methods:**

- **GET:** Retrieve data (what we use)
- **POST:** Send data to create something
- **PUT:** Update existing data
- **DELETE:** Remove data

**In our project:** We make GET requests to download data from LTA.

---

### HTTP Response

**What it is:** Message sent back from server (API) to client (your code) with the result.

**Key parts:**

- **Status code:** 200 = success, 404 = not found, 500 = server error
- **Headers:** Metadata about the response
- **Body:** The actual data (JSON, XML, file, etc.)

---

### JSON (JavaScript Object Notation)

**What it is:** Lightweight text format for storing and exchanging data.

**Example:**

```json
{
  "bus_stop_code": "83139",
  "description": "Opp Blk 123",
  "latitude": 1.3521
}
```

**Why popular:** Easy for both humans and computers to read/write.

**In our project:** LTA API can return data in JSON format.

---

### REST API

**What it is:** API design style using HTTP methods and URLs to access resources.

**Principles:**

- Each resource has a unique URL
- Use standard HTTP methods (GET, POST, etc.)
- Stateless (each request is independent)

**In our project:** LTA DataMall follows REST principles.

---

### Query Parameters

**What it is:** Key-value pairs in a URL that filter or modify the request.

**Format:** `?key1=value1&key2=value2`

**Example:** `/ltaodataservice/PV/ODBus?Date=202403`

- Parameter: `Date`
- Value: `202403`

---

### Authentication

**What it is:** Process of verifying who you are (proving identity to access a service).

**Methods:**

- API Key (what LTA uses)
- OAuth tokens
- Username/password

**In our project:** We use `AccountKey` header with our LTA API key.

---

## Cloud & Infrastructure

### Cloud Computing

**What it is:** Using remote servers on the internet instead of local computer for storage/processing.

**Benefits:**

- No hardware to buy/maintain
- Scale up/down as needed
- Pay only for what you use
- Access from anywhere

**In our project:** Using Google Cloud Platform (GCP).

---

### Object Storage

**What it is:** Storage architecture that manages data as objects (files) rather than blocks or file systems.

**Characteristics:**

- Flat namespace (no real folder hierarchy)
- Each object has unique ID/path
- Highly scalable (store petabytes)
- Accessed via API

**Examples:** GCS, AWS S3, Azure Blob Storage

**In our project:** GCS for storing raw CSV files.

---

### Data Warehouse (Cloud)

**What it is:** Fully-managed analytics database in the cloud.

**vs Traditional:** No servers to manage, scales automatically, pay per query.

**Examples:** BigQuery, Snowflake, Redshift

**In our project:** BigQuery hosts our dimensional model.

---

### Infrastructure as Code (IaC)

**What it is:** Managing infrastructure through code files rather than manual configuration.

**Benefits:**

- Version controlled (track changes)
- Reproducible (rebuild identical infrastructure)
- Documented (code = documentation)
- Automated (no manual clicking)

**Tools:** Terraform, CloudFormation, Pulumi

**In our project:** Terraform defines all our GCP resources.

---

### Bucket (in GCS)

**What it is:** Container for storing objects in Google Cloud Storage.

**Analogy:** Like a top-level folder or drive.

**Naming rules:**

- Globally unique across all GCP
- Lowercase letters, numbers, hyphens only
- 3-63 characters

**In our project:** Separate buckets for raw data, processed data, etc.

---

### Blob

**What it is:** Binary Large Object - a file stored in object storage.

**Types:**

- Text files (CSV, JSON)
- Images (PNG, JPG)
- Videos (MP4)
- Archives (ZIP)

**In our project:** Our CSV files are blobs in GCS.

---

## General Computer Science

### Environment Variable

**What it is:** A value stored outside your code that your program can access.

**Purpose:** Store configuration and secrets without hardcoding.

**Access in Python:** `os.getenv('VARIABLE_NAME')`

**In our project:** Store API keys, GCP project ID, bucket names.

---

### Virtual Environment

**What it is:** Isolated Python environment with its own set of installed packages.

**Analogy:** Like separate toolboxes for different projects - changes in one don't affect others.

**Why needed:** Different projects need different package versions.

**Tools:** venv, virtualenv, uv (what we use)

---

### Dependency

**What it is:** External code/library that your project needs to function.

**Example:** Our project depends on `requests` library for making API calls.

**Management:** Tracked in `pyproject.toml`, installed with `uv sync`.

---

### CSV (Comma-Separated Values)

**What it is:** Simple text file format for tabular data, fields separated by commas.

**Example:**

```csv
bus_stop_code,description,latitude
83139,Opp Blk 123,1.3521
83131,Blk 123,1.3522
```

**In our project:** LTA provides data as CSV files inside ZIP archives.

---

### Schema (data)

**What it is:** The structure/blueprint defining what fields/columns exist and their data types.

**Example:**

```
bus_stop_code: STRING
latitude: FLOAT
longitude: FLOAT
```

**In our project:** dbt schema files define our table structures.

---

### SQL (Structured Query Language)

**What it is:** Programming language for managing and querying relational databases.

**Common operations:**

- SELECT: Read data
- INSERT: Add data
- UPDATE: Modify data
- JOIN: Combine tables

**In our project:** dbt models are written in SQL.

---

### Cron Expression

**What it is:** String that defines a schedule (when jobs should run).

**Format:** `minute hour day month day_of_week`

**Example:** `0 2 10 * `* = "Run at 2:00 AM on the 10th of every month"

**In our project:** Airflow uses cron to schedule our pipeline.

---

### Idempotent

**What it is:** Operation that produces the same result no matter how many times it's executed.

**Example:** 

- Idempotent: "Set temperature to 70°F" (same result if run 10 times)
- Not idempotent: "Increase temperature by 5°F" (different result each time)

**Why important:** Pipelines can be re-run safely without duplicating data.

---

### Timestamp

**What it is:** A moment in time represented as a number or string.

**Formats:**

- Unix timestamp: `1677654321` (seconds since 1970)
- ISO 8601: `2024-03-21T14:30:00Z`

**In our project:** Used to track when data was processed.

---

### YAML (YAML Ain't Markup Language)

**What it is:** Human-readable data serialization format, often used for configuration files.

**Example:**

```yaml
database:
  host: localhost
  port: 5432
  username: admin
```

**In our project:** `docker-compose.yml`, dbt project files use YAML.

---

## Quick Reference: Terms by Category

### Most Important for Beginners

Start with these concepts first:

1. API & Endpoint
2. CSV & JSON
3. Data Pipeline
4. Fact Table & Dimension Table
5. Docker & Container
6. Environment Variable

### Data Modeling Essentials

- Star Schema
- Fact Table
- Dimension Table
- Surrogate Key
- Foreign Key
- Grain

### Cloud & Infrastructure

- BigQuery (warehouse)
- GCS (object storage)
- Bucket
- Terraform (IaC)
- Partitioning

### Pipeline Tools

- Airflow (orchestration)
- dbt (transformation)
- Docker (containerization)
- uv (package management)
- Streamlit (visualization)

---

## Learning Tips

1. **Don't memorize everything** - Use this glossary as a reference when you encounter terms
2. **Focus on concepts, not tools** - Understanding "orchestration" is more important than Airflow specifics
3. **Connect to analogies** - Real-world comparisons help concepts stick
4. **Ask "why"** - Why do we need surrogate keys? Why use Docker? Understanding purpose helps
5. **Learn by doing** - Terms make more sense when you use them in code

---

## Python Programming Concepts

### Class
**What it is:** A blueprint or template for creating objects. Think of it as a cookie cutter.

**Analogy:** 
- **Class** = Cookie cutter (the template)
- **Object** = The actual cookie (created from the template)

**In our project:**
```python
class Config:
    LTA_ACCOUNT_KEY = "..."
    GCP_PROJECT_ID = "..."
```

This creates a `Config` class that holds all our settings. The class itself is just the template - we use it by accessing `Config.LTA_ACCOUNT_KEY`.

**Key concepts:**
- **Class definition** - Using `class ClassName:` to create the blueprint
- **Class attributes** - Variables that belong to the class (like `LTA_ACCOUNT_KEY`)
- **Class methods** - Functions that belong to the class (like `validate()`)
- **Instance** - A specific object created from the class

**Why use classes:**
- **Organization** - Group related data and functions together
- **Reusability** - Define once, use many times
- **Encapsulation** - Keep related things in one place

---

### Object
**What it is:** A specific instance created from a class. An actual "thing" with data.

**Analogy:**
- **Class** = Car blueprint (design)
- **Object** = Your actual Toyota Camry (specific car)

**Example:**
```python
# Class definition (the blueprint)
class Car:
    def __init__(self, color, model):
        self.color = color
        self.model = model

# Creating objects (instances) from the class
my_car = Car("red", "Camry")      # Object 1
your_car = Car("blue", "Accord")  # Object 2
```

Each object has its own data (`my_car` is red, `your_car` is blue).

**In our project:**
Our `Config` class is special - we don't create objects from it. We use it as a "namespace" to organize settings. But when you use libraries like `requests.Session()`, that creates an object.

---

### Function
**What it is:** A reusable block of code that performs a specific task.

**Analogy:** Like a recipe - you write it once, then follow it many times.

**Structure:**
```python
def function_name(parameter1, parameter2):
    """
    Docstring: Explains what the function does
    """
    # Code that does something
    result = parameter1 + parameter2
    return result  # Sends back the answer
```

**Key parts:**
- **def** - Keyword that means "define a function"
- **function_name** - What you call it (use descriptive names)
- **parameters** - Input values the function needs (in parentheses)
- **return** - Output value the function gives back
- **docstring** - Documentation (in triple quotes)

**Example from our project:**
```python
def get_config():
    """
    Get the Config class.
    
    Returns the Config class for use in other modules.
    """
    return Config
```

**When to use functions:**
- When you do the same task multiple times
- To break complex code into smaller pieces
- To make code more readable and maintainable

---

### Method
**What it is:** A function that belongs to a class. It's a function defined inside a class.

**Analogy:**
- **Function** = A standalone recipe (make cookies)
- **Method** = A recipe in a cookbook (the cookbook's cookie recipe)

**Difference from function:**
```python
# Function (standalone, not in a class)
def format_date(year, month):
    return f"{year}{month:02d}"

# Method (inside a class)
class Config:
    @classmethod
    def validate(cls):
        # This is a method because it's inside Config class
        if not cls.LTA_ACCOUNT_KEY:
            raise ValueError("Missing API key")
```

**Types of methods:**

1. **Instance method** - Works with a specific object
```python
class Car:
    def start_engine(self):  # 'self' = the specific car
        print("Engine started!")

my_car.start_engine()  # Method called ON an object
```

2. **Class method** - Works with the class itself (uses `@classmethod`)
```python
class Config:
    @classmethod
    def validate(cls):  # 'cls' = the Config class
        # Works with class, not a specific instance
        pass
```

3. **Static method** - Doesn't use class or instance data (uses `@staticmethod`)
```python
class MathUtils:
    @staticmethod
    def add(a, b):
        return a + b  # Just a utility function
```

**In our project:**
`Config.validate()` is a **class method** - it checks the Config class settings.

---

### Attribute
**What it is:** A variable that belongs to a class or object. Data stored in the class/object.

**Analogy:** Like properties of a car (color, model, year).

**Types:**

1. **Class attribute** - Shared by all instances
```python
class Config:
    LTA_BASE_URL = "http://..."  # Class attribute
    # Same for everyone who uses Config
```

2. **Instance attribute** - Unique to each object
```python
class Car:
    def __init__(self, color):
        self.color = color  # Instance attribute
        # Each car can have different color

car1 = Car("red")   # car1.color = "red"
car2 = Car("blue")  # car2.color = "blue"
```

**How to access:**
```python
# Accessing class attribute
print(Config.LTA_BASE_URL)

# Accessing instance attribute
print(my_car.color)
```

**In our project:**
All our Config settings are class attributes:
- `Config.LTA_ACCOUNT_KEY`
- `Config.GCP_PROJECT_ID`
- `Config.GCS_BUCKET_RAW`

---

### Module
**What it is:** A Python file (.py) that contains code you can import and reuse.

**Analogy:** Like a chapter in a book - each module focuses on one topic.

**Example:**
```python
# File: src/config/settings.py (this IS a module)
class Config:
    LTA_ACCOUNT_KEY = "..."

# In another file, you import the module:
from src.config.settings import Config
# Now you can use Config.LTA_ACCOUNT_KEY
```

**Why use modules:**
- **Organization** - Break large programs into smaller files
- **Reusability** - Import code from one file into another
- **Maintainability** - Easier to find and fix things

**Module vs Package:**
- **Module** = Single .py file
- **Package** = Folder with multiple modules (must have `__init__.py`)

**In our project:**
- `src/config/settings.py` is a module
- `src/config/` is a package (folder with modules)

---

### Import
**What it is:** A way to use code from other files/modules/libraries.

**Types of imports:**

1. **Import entire module:**
```python
import os
# Use: os.getenv()
```

2. **Import specific things:**
```python
from os import getenv
# Use: getenv() directly
```

3. **Import with alias (nickname):**
```python
import pandas as pd
# Use: pd.DataFrame()
```

4. **Import from your own modules:**
```python
from src.config.settings import Config
# Use: Config.LTA_ACCOUNT_KEY
```

**Best practices:**
- Put all imports at top of file
- Standard library first, then third-party, then your own
- Use absolute imports (`from src.config...`) not relative (`from ..config...`)

---

### Decorator
**What it is:** A function that modifies or enhances another function. Uses `@` symbol.

**Analogy:** Like gift wrapping - takes a function and adds something to it.

**Common decorators you'll see:**

1. **@classmethod** - Makes a method work with the class, not an instance
```python
class Config:
    @classmethod
    def validate(cls):  # cls = the class
        pass
```

2. **@staticmethod** - Makes a method that doesn't need class or instance
```python
class Utils:
    @staticmethod
    def add(a, b):  # No self or cls
        return a + b
```

3. **@property** - Makes a method look like an attribute
```python
class Person:
    @property
    def full_name(self):
        return f"{self.first} {self.last}"

p = Person()
print(p.full_name)  # No () needed - looks like attribute
```

**In our project:**
We use `@classmethod` for `Config.validate()` and other Config methods.

---

### Type Hints
**What it is:** Optional notation that indicates what type a variable should be.

**Format:**
```python
def function_name(param: type) -> return_type:
    pass
```

**Examples:**
```python
# Function with type hints
def add_numbers(a: int, b: int) -> int:
    return a + b

# Variable with type hint
name: str = "John"
age: int = 25
is_active: bool = True

# Optional type (can be None)
from typing import Optional
api_key: Optional[str] = None  # Can be str or None
```

**In our project:**
```python
class Config:
    LTA_ACCOUNT_KEY: Optional[str] = os.getenv('LTA_ACCOUNT_KEY')
    #                ^^^^^^^^^^^^^^
    #                Type hint: Can be string or None
```

**Benefits:**
- **Documentation** - Shows what types are expected
- **IDE help** - Your editor can autocomplete and catch errors
- **Clarity** - Makes code easier to understand

**Note:** Type hints don't enforce types (Python still runs without checking). They're hints for developers and tools.

---

### Docstring
**What it is:** Documentation string that explains what code does. Uses triple quotes `"""`.

**Where to use:**
1. At top of modules (files)
2. At top of classes
3. At top of functions/methods

**Format:**
```python
def download_data(year: int, month: int) -> str:
    """
    Download transport data from LTA API.
    
    This function calls the LTA DataMall API to download
    origin-destination data for the specified month.
    
    Parameters:
        year (int): The year (e.g., 2024)
        month (int): The month (1-12)
        
    Returns:
        str: Path to the downloaded file
        
    Raises:
        ValueError: If month is not 1-12
        ConnectionError: If API is unreachable
        
    Example:
        >>> path = download_data(2024, 3)
        >>> print(path)
        'data/raw/bus/2024/03/od_bus_202403.zip'
    """
    # Function code here
    pass
```

**Why important:**
- Documents your code for others (and future you)
- Tools can generate documentation from docstrings
- IDEs show docstrings as tooltips

**In our project:**
Every module, class, and function has detailed docstrings explaining what it does.

---

### self vs cls
**What they mean:**

**`self`** - Refers to the specific object (instance)
```python
class Car:
    def __init__(self, color):
        self.color = color  # self = this specific car
        
    def paint(self, new_color):
        self.color = new_color  # Change THIS car's color

my_car = Car("red")
my_car.paint("blue")  # Changes my_car's color only
```

**`cls`** - Refers to the class itself
```python
class Config:
    count = 0
    
    @classmethod
    def increment_count(cls):
        cls.count += 1  # cls = the Config class
        # Changes the class variable, not instance

Config.increment_count()  # Called on class, not object
```

**When to use:**
- **self** - Instance methods (working with specific objects)
- **cls** - Class methods (working with the class itself)
- **Neither** - Static methods (utility functions)

---

### None
**What it is:** Python's way of representing "nothing" or "no value".

**Like:** NULL in other languages, or "N/A" in Excel.

**When used:**
1. Default value when something isn't set
```python
api_key: Optional[str] = None  # Not set yet
```

2. Function returns nothing
```python
def print_message(msg):
    print(msg)
    return None  # Or just no return statement
```

3. Checking if something exists
```python
if Config.LTA_ACCOUNT_KEY is None:
    print("API key not set!")
```

**Important:**
- Use `is None` not `== None` (best practice)
- Use `is not None` to check if something exists

---

### List vs Tuple vs Dictionary
Three common ways to store collections of data:

**List** - Ordered, changeable, allows duplicates
```python
# Created with square brackets []
modes = ['bus', 'train', 'taxi']
modes.append('subway')  # Can modify
modes[0] = 'bus_rapid'  # Can change items
```

**Tuple** - Ordered, unchangeable, allows duplicates
```python
# Created with parentheses ()
coordinates = (1.3521, 103.8198)
# coordinates[0] = 2.0  # ERROR - cannot change!
```

**Dictionary** - Key-value pairs, unordered
```python
# Created with curly braces {}
config = {
    'api_key': 'abc123',
    'timeout': 30,
    'region': 'asia'
}
print(config['api_key'])  # Access by key
config['timeout'] = 60    # Can modify values
```

**When to use:**
- **List** - Collection of similar items that might change
- **Tuple** - Fixed collection that shouldn't change (coordinates, RGB colors)
- **Dictionary** - Named values, like configuration or JSON data

---

### Exception Handling (try/except)
**What it is:** Way to handle errors gracefully without crashing.

**Structure:**
```python
try:
    # Code that might fail
    result = dangerous_operation()
except SpecificError as e:
    # What to do if that error happens
    print(f"Error: {e}")
except AnotherError:
    # Handle different error
    print("Different error!")
else:
    # Runs if NO error occurred
    print("Success!")
finally:
    # ALWAYS runs, error or not
    cleanup()
```

**Example:**
```python
try:
    api_key = Config.LTA_ACCOUNT_KEY
    if api_key is None:
        raise ValueError("API key not set!")
except ValueError as e:
    print(f"Configuration error: {e}")
    # Handle the error gracefully
```

**Common exceptions:**
- `ValueError` - Wrong value (e.g., invalid format)
- `TypeError` - Wrong type (e.g., string instead of int)
- `FileNotFoundError` - File doesn't exist
- `KeyError` - Dictionary key doesn't exist
- `Exception` - Catch-all for any error

**Best practice:**
- Catch specific exceptions, not generic `Exception`
- Don't silently ignore errors (`except: pass`)
- Always log or handle errors meaningfully

---

### String Formatting
**Different ways to create strings with variables:**

**1. f-strings (Modern, Recommended)**
```python
name = "LTA"
year = 2024
message = f"Downloading {name} data for {year}"
# Result: "Downloading LTA data for 2024"
```

**2. .format() (Older style)**
```python
message = "Downloading {} data for {}".format(name, year)
```

**3. % formatting (Very old, avoid)**
```python
message = "Downloading %s data for %d" % (name, year)
```

**Our project uses f-strings** because they're:
- More readable
- Faster
- Can include expressions: `f"Total: {a + b}"`

---

### Pathlib vs os.path
**Two ways to work with file paths:**

**os.path (Old way)**
```python
import os
path = os.path.join('data', 'raw', 'bus', 'file.csv')
if os.path.exists(path):
    print("File exists")
```

**Path from pathlib (Modern way - What we use)**
```python
from pathlib import Path
path = Path('data') / 'raw' / 'bus' / 'file.csv'
if path.exists():
    print("File exists")
```

**Why Path is better:**
- More intuitive (`/` to join paths)
- Cross-platform (works on Windows and Linux)
- Object-oriented (methods like `.exists()`, `.mkdir()`)
- Cleaner code

**In our project:**
```python
DATA_DIR = Path(__file__).parent.parent.parent / 'data'
RAW_DATA_DIR = DATA_DIR / 'raw'
```

---

## Quick Reference: Python Concepts

**Object-Oriented:**
- Class - Blueprint/template
- Object - Instance of a class
- Method - Function inside a class
- Attribute - Variable inside a class
- self - Reference to instance
- cls - Reference to class

**Code Organization:**
- Module - A .py file
- Package - Folder with modules
- Import - Use code from other files
- Function - Reusable code block

**Type System:**
- Type Hints - Optional type annotations
- Optional - Can be value or None
- None - Represents "no value"

**Data Structures:**
- List - Changeable collection `[]`
- Tuple - Unchangeable collection `()`
- Dictionary - Key-value pairs `{}`

**Documentation:**
- Docstring - Triple-quoted documentation
- Comments - `#` for explanations
- Type hints - Show expected types

---

**Last Updated:** April 17, 2026  
**Project:** Singapore LTA Public Transport Analytics Pipeline