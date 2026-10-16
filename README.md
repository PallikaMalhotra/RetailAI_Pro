import pypandoc

readme = r"""# RetailAI — Retail Data Engineering & Analytics Pipeline

RetailAI is an end-to-end retail data engineering project that transforms raw retail transactions into clean, validated data for analytics. It combines Python ETL, automated data quality checks, SQLite, Amazon S3, Amazon Athena, GitHub Actions, a dimensional star schema, Prefect orchestration, and partitioned Parquet analytics.

## Project Overview

Retail businesses generate large volumes of transaction data. Before this data can be used for reporting and business decisions, it must be cleaned, validated, stored, and made accessible for analytical queries.

RetailAI demonstrates this workflow using the UCI Online Retail dataset.

### Key Features

- ETL pipeline for cleaning raw retail transaction data.
- Data quality validation and rejected-record reporting.
- CSV and Parquet output generation.
- Local analytical storage using SQLite.
- SQL-based retail revenue analysis.
- Cloud storage using Amazon S3.
- Serverless SQL analytics using Amazon Athena.
- Partitioned Parquet data by year and month.
- Athena scan-size comparison for partitioned and unpartitioned queries.
- Dimensional star schema with fact and dimension tables.
- Automated tests with pytest and GitHub Actions.
- Local workflow orchestration using Prefect.
- SQLite query benchmarking, pipeline monitoring, and validation reports.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | ETL, validation, automation, and benchmarking |
| Pandas | Data cleaning and transformation |
| Pytest | Automated data and schema tests |
| Parquet | Columnar data storage |
| SQLite | Local analytical database and star schema |
| SQL | Data analysis and aggregation |
| Amazon S3 | Cloud object storage |
| Amazon Athena | Serverless SQL queries on S3 data |
| GitHub Actions | Automated CI workflow |
| Prefect | Local workflow orchestration |
| PowerShell | Running scripts on Windows |
| Git | Version control |

## Architecture

```text
UCI Online Retail Dataset
          |
          v
     Raw Excel Dataset
          |
          v
     Python ETL Pipeline
          |
          +----------------------+
          |                      |
          v                      v
   Clean CSV/Parquet       Rejected Records
          |
          v
   Data Quality Tests
          |
          v
      SQLite Database
          |
          +----------------------+
          |                      |
          v                      v
   SQL Analytics          Dimensional Star Schema
          |
          v
   Partitioned Parquet
   (year/month folders)
          |
          v
       Amazon S3
          |
          v
      Amazon Athena
          |
          v
  Cloud SQL Analytics
```

## Dataset

**Source:** UCI Machine Learning Repository — Online Retail  
Dataset: https://archive.ics.uci.edu/dataset/352/online+retail

The dataset contains retail transactions from a UK-based online retailer between 2010 and 2011.

Important fields include:

- `InvoiceNo` — invoice identifier
- `StockCode` — product identifier
- `Description` — product description
- `Quantity` — quantity purchased
- `InvoiceDate` — transaction date and time
- `UnitPrice` — price per unit
- `CustomerID` — customer identifier
- `Country` — customer's country

## Data Engineering Workflow

### 1. ETL Pipeline

The ETL process reads the source Excel dataset and performs the following operations:

- Converts columns into appropriate data types.
- Handles missing required values.
- Identifies cancellation transactions.
- Calculates revenue using quantity multiplied by unit price.
- Rejects invalid records, including zero-quantity rows and negative unit prices.
- Removes exact duplicate business records.
- Preserves source-row information for traceability.
- Exports cleaned data into CSV and Parquet formats.
- Generates a data quality report in JSON format.

**Main script:** `src/retail_etl.py`

### 2. Data Quality Validation and CI

The data quality checks cover output-file availability, required columns, duplicate records, quantity and unit-price rules, revenue calculations, and reconciliation of accepted and rejected records.

- The local data quality tests are run with pytest.
- GitHub Actions runs the automated workflow on GitHub, including ETL, quality tests, database loading, star-schema creation, and star-schema tests.
- The latest workflow run reported by the project owner completed successfully.

**Main test files:** `src/test_retail_quality.py`, `src/test_star_schema.py`  
**Workflow:** `.github/workflows/tests.yml`

### 3. SQLite Database

The cleaned data is loaded into a local SQLite database for analytical queries.

- Database: `data/online_retail.db`
- Table: `retail_transactions`
- Records loaded: 536,639

The standard full-load script rebuilds the table contents during each run. An additional incremental-loading script is available at `src/incremental_retail_load.py`; it is not integrated into the main local orchestrator.

**Main script:** `src/load_retail_database.py`

### 4. Dimensional Star Schema

A dimensional model was created for analytical reporting. It contains:

- `FactSales` — transaction-level sales measures and dimension keys.
- `DimProduct` — product attributes.
- `DimCustomer` — customer and country attributes.
- `DimDate` — date, year, month, and day attributes.

Observed row counts from the local build:

| Table | Rows |
|---|---:|
| `DimProduct` | 5,749 |
| `DimCustomer` | 4,380 |
| `DimDate` | 305 |
| `FactSales` | 536,639 |

The fact table row count matched the 536,639 cleaned source records in the observed run. Five star-schema tests passed in the local test run reported by the project owner.

**Files:** `sql/star_schema.sql`, `src/build_star_schema.py`, `src/test_star_schema.py`

### 5. SQL Analytics

SQL queries can be used to explore revenue by country, product, and other business dimensions.

Example: top 10 countries by revenue.

```sql
SELECT
    country,
    ROUND(SUM(revenue), 2) AS total_revenue
FROM retail_transactions
GROUP BY country
ORDER BY total_revenue DESC
LIMIT 10;
```

This query includes all rows in the table, including cancellation records. For sales-only analysis, apply the appropriate cancellation filter.

Additional analytical queries are maintained in `sql/analytics.sql` where available.

### 6. Amazon S3

The cleaned Parquet dataset is stored in Amazon S3 for cloud-based analytics.

**Unpartitioned dataset:**

`s3://retailai-data-847291/processed/online_retail_clean.parquet`

**Partitioned dataset prefix:**

`s3://retailai-data-847291/partitioned/`

The partitioned output is organized by `year` and `month`, allowing queries with matching partition filters to read only relevant partitions.

### 7. Amazon Athena

Athena is configured to query Parquet datasets stored in S3.

- Database: `retailai`
- Original table: `online_retail`
- Partitioned table: `online_retail_partitioned`

The partitioned table uses `year` and `month` partition columns. Partition metadata was registered in Athena, and a December 2010 query was run against both tables.

#### Partitioning benchmark: December 2010

Both queries returned the same results, validating that the partitioned query preserved the result for this time range.

| Metric | Original table | Partitioned table |
|---|---:|---:|
| Transaction count | 41,981 | 41,981 |
| Total revenue | 746,723.61 | 746,723.61 |
| Data scanned | 1.27 MB | 87.20 KB |

This observed comparison represents approximately **93.3% less data scanned** for the partitioned query. The result applies to the tested December 2010 query and is not a guarantee for every query. To benefit from partition pruning, include partition filters such as `year = 2010 AND month = 12`.

Example partitioned query:

```sql
SELECT
    COUNT(*) AS transaction_count,
    ROUND(SUM(revenue), 2) AS total_revenue
FROM retailai.online_retail_partitioned
WHERE year = 2010
  AND month = 12
  AND invoicedate >= TIMESTAMP '2010-12-01 00:00:00'
  AND invoicedate < TIMESTAMP '2011-01-01 00:00:00';
```

Athena tables are external tables; the underlying data remains stored in S3.

## Pipeline Orchestration

### Standard local orchestrator

The main orchestration script runs the local workflow in sequence and stops when a step fails.

**Main script:** `src/run_pipeline.py`

Current sequence:

1. `retail_etl.py`
2. `test_retail_quality.py`
3. `load_retail_database.py`
4. `verify_retail_database.py`
5. `pipeline_monitor.py`

Run it with:

```powershell
py src/run_pipeline.py
```

### Prefect flow

A separate Prefect flow was also run successfully in the local environment. It invokes the ETL, quality-test, database-load, verification, and monitoring scripts as sequential tasks.

**Main script:** `src/prefect_pipeline.py`

Run it with:

```powershell
py src/prefect_pipeline.py
```

This demonstrates local orchestration; it is not described as a deployed or scheduled Prefect service.

Both orchestration paths currently use a full database reload rather than incremental loading. The Prefect flow does not currently include the star-schema build steps.

## Validation Results

Observed results from local runs:

| Metric | Result |
|---|---:|
| Cleaned records loaded into SQLite | 536,639 |
| Unique transaction IDs | 536,639 |
| Null transaction IDs | 0 |
| Data quality tests | 6 passed |
| Star-schema tests | 5 passed |
| GitHub Actions workflow | Successful |
| Prefect local flow | Completed successfully |

Pipeline duration can vary with the local machine, filesystem, and execution conditions.

## Query Performance Benchmark

### SQLite index benchmark

The country-wise revenue query was benchmarked over five runs.

| Metric | Observed result |
|---|---:|
| Average runtime before country index | 160.02 ms |
| Average runtime after country index | 176.54 ms |
| Number of benchmark runs | 5 |

The index did not improve performance in this observed test. The measured difference may reflect execution variability, and index effectiveness depends on the query and data distribution.

**Benchmark script:** `src/benchmark_queries.py`

### SQLite and Athena observations

One Athena country-wise revenue query previously completed with these measurements:

| Metric | Observed result |
|---|---:|
| Query status | Completed |
| Run time | 896 ms |
| Time in queue | 74 ms |
| Data scanned | 861.74 KB |

The local SQLite comparison script reported an average runtime of 171.5 ms. These are observations, not a controlled performance comparison: SQLite's average runtime and Athena's single execution have different measurement conditions.

**Comparison script:** `src/compare_performance.py`

## Project Structure

```text
RetailAI_Pro/
├── .github/
│   └── workflows/
│       └── tests.yml
├── data/
│   ├── raw/
│   ├── processed/
│   ├── partitioned/
│   ├── rejected/
│   └── online_retail.db
├── reports/
├── sql/
│   ├── analytics.sql
│   └── star_schema.sql
├── src/
│   ├── retail_etl.py
│   ├── test_retail_quality.py
│   ├── load_retail_database.py
│   ├── verify_retail_database.py
│   ├── incremental_retail_load.py
│   ├── pipeline_monitor.py
│   ├── benchmark_queries.py
│   ├── compare_performance.py
│   ├── run_pipeline.py
│   ├── prefect_pipeline.py
│   ├── partition_retail_data.py
│   ├── build_star_schema.py
│   └── test_star_schema.py
├── requirements.txt
└── README.md
```

The tree shows the principal project files. Actual local folders may contain additional generated data or helper scripts. Raw datasets, processed datasets, database files, and reports may be excluded from version control by `.gitignore`.

## Setup and Execution

### Prerequisites

- Python 3.10 or later
- pip
- Windows PowerShell or another terminal
- AWS account only for the S3 and Athena portions

### Install dependencies

From the project root, install the project's dependencies:

```powershell
py -m pip install -r requirements.txt
```

If you are setting up only the basic ETL components, the core packages include:

```powershell
py -m pip install pandas openpyxl pyarrow
```

### Run ETL and data quality checks

```powershell
py src/retail_etl.py
py -m pytest src/test_retail_quality.py -v
```

### Load and verify SQLite

```powershell
py src/load_retail_database.py
py src/verify_retail_database.py
```

### Build and test the star schema

```powershell
py src/build_star_schema.py
py -m pytest src/test_star_schema.py -v
```

### Run the local pipeline

```powershell
py src/run_pipeline.py
```

### Run the Prefect flow

```powershell
py src/prefect_pipeline.py
```

### Create partitioned Parquet data

```powershell
py src/partition_retail_data.py
```

Upload the generated `data/partitioned/` contents to the configured S3 partition prefix before querying the partitioned Athena table.

### Run performance benchmarks

```powershell
py src/benchmark_queries.py
py src/compare_performance.py
```

## AWS Cost and Data Management

- Athena queries scan data stored in S3 and may incur charges.
- Use Parquet and partition filters to limit scans where possible.
- Keep Athena query results in a dedicated S3 prefix.
- Review AWS billing and usage regularly.
- Do not upload AWS credentials, access keys, or secrets to GitHub.
- Check `.gitignore` before publishing local datasets or database files.

## Current Limitations

- The standard local orchestrator uses a full database reload, not an incremental load.
- The incremental-loading script is separate from the main orchestrators.
- The transaction ID is derived from source-row information and is not a universal business key.
- The current performance measurements are environment-specific.
- The S3 and Athena setup is configured separately from the local Python pipeline.
- The Prefect flow is a local run, not a deployed or scheduled service.
- The Prefect flow does not currently build the star schema.
- The 93.3% scan reduction was observed for the December 2010 query only.

## Future Improvements

1. Integrate incremental loading into the main orchestrator.
2. Add automated checks for partition registration and query-result parity.
3. Add partitioned Athena benchmarks for more date ranges and query patterns.
4. Deploy and schedule the Prefect flow if automated recurring execution is required.
5. Add more analytical queries and document their business interpretation.

## Learning Outcomes

This project demonstrates practical experience with:

- ETL development using Python.
- Data cleaning and validation.
- CSV and Parquet data formats.
- Local database loading and SQL analytics.
- Dimensional modeling with fact and dimension tables.
- Cloud object storage using Amazon S3.
- Serverless analytics using Amazon Athena.
- Automated testing and continuous integration.
- Local workflow orchestration with Prefect.
- Query benchmarking and partition-pruning analysis.
- Pipeline monitoring.

## Acknowledgements

The project uses the Online Retail dataset provided by the UCI Machine Learning Repository.

Dataset page: https://archive.ics.uci.edu/dataset/352/online+retail
"""

output_path = "/mnt/data/README_RetailAI_Updated.md"
pypandoc.convert_text(readme, "md", format="md", outputfile=output_path, extra_args=["--standalone"])
print(f"Created updated README: {output_path}")
