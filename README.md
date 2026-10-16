# RetailAI — Retail Data Engineering & Analytics Pipeline

RetailAI is an end-to-end retail data engineering project that transforms raw retail transactions into clean, validated data for analytics. It combines Python-based ETL, data quality checks, SQLite, Amazon S3, and Amazon Athena to demonstrate a practical data pipeline.

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
- SQLite query benchmarking and index performance testing.
- Pipeline execution monitoring and validation reports.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | ETL, validation, automation, and benchmarking |
| Pandas | Data cleaning and transformation |
| Parquet | Columnar data storage |
| SQLite | Local analytical database |
| SQL | Data analysis and aggregation |
| Amazon S3 | Cloud object storage |
| Amazon Athena | Serverless SQL queries on S3 data |
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
          +--------------------+
          |                    |
          v                    v
   Cleaned CSV/Parquet    Rejected Records
          |
          v
   Data Quality Tests
          |
          v
   SQLite Database
          |
          v
   SQL Analytics & Benchmarking

   Cleaned Parquet Dataset
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

### 2. Data Quality Validation

The validation script checks:

- Whether the expected output files exist.
- Whether required columns are present.
- Whether duplicate records remain.
- Whether quantity and unit price satisfy the defined rules.
- Whether revenue calculations are correct.
- Whether accepted and rejected records reconcile with the input.

**Main script:** `src/test_retail_quality.py`

### 3. SQLite Database

The cleaned data is loaded into a local SQLite database for analytical queries.

- Database: `data/online_retail.db`
- Table: `retail_transactions`
- Records loaded: 536,639

The current full-load script rebuilds the table contents during each run.

**Main script:** `src/load_retail_database.py`

An additional incremental-loading script is available at `src/incremental_retail_load.py`. It is not currently integrated into the main pipeline orchestrator.

### 4. SQL Analytics

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

Note: This query includes all rows in the table, including cancellation records. For sales-only analysis, apply the appropriate cancellation filter.

### 5. Amazon S3

The cleaned Parquet dataset is stored in Amazon S3 for cloud-based analytics.

Configured dataset location:

`s3://retailai-data-847291/processed/online_retail_clean.parquet`

S3 stores the processed data as an object, allowing analytical tools to access it without maintaining a traditional database server.

### 6. Amazon Athena

Athena is configured to query the Parquet dataset stored in S3.

Database: `retailai`

Table: `online_retail`

Example: count the records available through Athena.

```sql
SELECT COUNT(*) AS total_rows
FROM retailai.online_retail;
```

Example: calculate revenue by country.

```sql
SELECT
    country,
    ROUND(SUM(revenue), 2) AS total_revenue
FROM retailai.online_retail
GROUP BY country
ORDER BY total_revenue DESC
LIMIT 10;
```

The Athena table is an external table. The underlying data remains stored in S3.

## Pipeline Orchestration

The main orchestration script runs the local workflow in sequence and stops when a step fails.

**Main script:** `src/run_pipeline.py`

Current sequence:

1. `retail_etl.py`
2. `test_retail_quality.py`
3. `load_retail_database.py`
4. `verify_retail_database.py`
5. `pipeline_monitor.py`

Run the pipeline with:

```powershell
py src/run_pipeline.py
```

The current orchestrator performs a full database reload rather than incremental loading.

## Validation Results

Observed results from the local environment:

| Metric | Result |
|---|---:|
| Cleaned records loaded into SQLite | 536,639 |
| Unique transaction IDs | 536,639 |
| Null transaction IDs | 0 |
| Data quality test script | Passed |
| Pipeline execution | Successful |
| Latest previously recorded pipeline duration | 53.21 seconds |

Pipeline duration varies with the local machine, filesystem, and execution conditions.

## Query Performance Benchmark

### SQLite Index Benchmark

The country-wise revenue query was benchmarked over five runs.

| Metric | Observed Result |
|---|---:|
| Average runtime before country index | 160.02 ms |
| Average runtime after country index | 176.54 ms |
| Number of benchmark runs | 5 |

The index did not improve performance in this observed test. The measured difference may reflect execution variability, and index effectiveness depends on the query and data distribution.

**Benchmark script:** `src/benchmark_queries.py`

### SQLite and Athena Observations

One Athena country-wise revenue query completed with the following observed measurements:

| Metric | Observed Result |
|---|---:|
| Query status | Completed |
| Run time | 896 ms |
| Time in queue | 74 ms |
| Data scanned | 861.74 KB |

The local SQLite comparison script reported an average runtime of 171.5 ms.

These figures are observations, not a controlled performance comparison. SQLite's average runtime and Athena's single execution have different measurement conditions. Athena's runtime can include cloud execution overhead, and data scanned depends on the query and dataset layout.

**Comparison script:** `src/compare_performance.py`

## Project Structure

```text
RetailAI_Pro/
├── data/
│   ├── raw/
│   │   └── Online Retail.xlsx
│   ├── processed/
│   │   ├── online_retail_clean.csv
│   │   └── online_retail_clean.parquet
│   ├── rejected/
│   │   └── online_retail_rejected.csv
│   └── online_retail.db
├── reports/
│   └── online_retail_quality_report.json
├── src/
│   ├── inspect_dataset.py
│   ├── retail_etl.py
│   ├── test_retail_quality.py
│   ├── load_retail_database.py
│   ├── verify_retail_database.py
│   ├── incremental_retail_load.py
│   ├── pipeline_monitor.py
│   ├── benchmark_queries.py
│   ├── compare_performance.py
│   └── run_pipeline.py
└── README.md
```

The file tree shows the main files used in the workflow; additional starter files may also exist in the repository.

## Setup and Execution

### Prerequisites

- Python 3.10 or later
- pip
- Windows PowerShell or another terminal
- AWS account only for the S3 and Athena portions

### Install dependencies

From the project root:

```powershell
py -m pip install pandas openpyxl pyarrow
```

### Run the ETL pipeline

```powershell
py src/retail_etl.py
```

### Run data quality checks

```powershell
py src/test_retail_quality.py
```

### Load and verify SQLite

```powershell
py src/load_retail_database.py
py src/verify_retail_database.py
```

### Run pipeline monitoring

```powershell
py src/pipeline_monitor.py
```

### Run the complete local pipeline

```powershell
py src/run_pipeline.py
```

### Run performance benchmarks

```powershell
py src/benchmark_queries.py
py src/compare_performance.py
```

Run the complete pipeline only after checking that the input file and dependencies are available.

## AWS Cost and Data Management

- Athena queries scan data stored in S3 and may incur charges.
- Use Parquet and limit query scans where possible.
- Keep Athena query results in a dedicated S3 prefix.
- Review AWS billing and usage regularly.
- Do not upload AWS credentials, access keys, or secrets to GitHub.
- Check the repository's `.gitignore` before publishing local datasets or database files.

## Current Limitations

- The main orchestrator uses a full database reload, not an incremental load.
- The incremental-loading script is separate from the main orchestrator.
- The transaction ID is derived from source-row information and is not a universal business key.
- The current performance measurements are environment-specific.
- The S3 and Athena setup is configured separately from the local Python pipeline.
- Automated CI tests, a dimensional star schema, workflow scheduling, and partitioned Parquet benchmarking are potential future enhancements.

## Future Improvements

1. Add a proper automated test suite using `pytest`.
2. Add GitHub Actions for continuous integration.
3. Design a dimensional star schema for analytical reporting.
4. Integrate a workflow orchestration tool such as Prefect or Airflow.
5. Partition Parquet data by year and month and compare Athena scan sizes and costs.

## Learning Outcomes

This project demonstrates practical experience with:

- ETL development using Python.
- Data cleaning and validation.
- CSV and Parquet data formats.
- Local database loading and SQL analytics.
- Cloud object storage using Amazon S3.
- Serverless analytics using Amazon Athena.
- Query benchmarking and execution-plan inspection.
- Pipeline monitoring and orchestration.

## Acknowledgements

The project uses the Online Retail dataset provided by the UCI Machine Learning Repository.

Dataset page: https://archive.ics.uci.edu/dataset/352/online+retail
