
from pathlib import Path
import pandas as pd
import json

ROOT = Path(__file__).resolve().parents[1]

RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
REJECTED_DIR = ROOT / "data" / "rejected"
REPORT_DIR = ROOT / "reports"

for folder in [PROCESSED_DIR, REJECTED_DIR, REPORT_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

files = list(RAW_DIR.glob("*.xlsx"))

if not files:
    raise FileNotFoundError(f"No Excel file found in {RAW_DIR}")

print(f"Reading: {files[0].name}")
df = pd.read_excel(files[0])

# Standardize column names
df.columns = df.columns.str.strip()

required = [
    "InvoiceNo", "StockCode", "Description",
    "Quantity", "InvoiceDate", "UnitPrice",
    "CustomerID", "Country"
]

missing_columns = [c for c in required if c not in df.columns]
if missing_columns:
    raise ValueError(f"Missing expected columns: {missing_columns}")

# Preserve original row number for audit
df["source_row"] = range(2, len(df) + 2)

# Convert columns to suitable types
df["InvoiceNo"] = df["InvoiceNo"].astype("string").str.strip()
df["StockCode"] = df["StockCode"].astype("string").str.strip()
df["Description"] = df["Description"].astype("string").str.strip()
df["Country"] = df["Country"].astype("string").str.strip()

df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
df["UnitPrice"] = pd.to_numeric(df["UnitPrice"], errors="coerce")
df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")
df["CustomerID"] = pd.to_numeric(df["CustomerID"], errors="coerce")

# Mark cancellations instead of silently deleting them
df["is_cancellation"] = (
    df["InvoiceNo"].str.startswith("C", na=False)
)

# Revenue is the signed transaction amount
df["revenue"] = df["Quantity"] * df["UnitPrice"]

# Define basic validity rules
invalid = (
    df["InvoiceNo"].isna()
    | df["InvoiceNo"].eq("")
    | df["StockCode"].isna()
    | df["StockCode"].eq("")
    | df["Quantity"].isna()
    | df["UnitPrice"].isna()
    | df["InvoiceDate"].isna()
    | df["Quantity"].eq(0)
    | df["UnitPrice"].lt(0)
)

rejected = df[invalid].copy()
clean = df[~invalid].copy()

# Remove exact duplicates from clean output only
duplicate_mask = clean.duplicated(subset=required, keep="first")
duplicate_count = int(duplicate_mask.sum())
clean = clean[~duplicate_mask].copy()

# Save output files
clean.to_csv(
    PROCESSED_DIR / "online_retail_clean.csv",
    index=False
)

clean.to_parquet(
    PROCESSED_DIR / "online_retail_clean.parquet",
    index=False
)

rejected.to_csv(
    REJECTED_DIR / "online_retail_rejected.csv",
    index=False
)

report = {
    "source_file": files[0].name,
    "input_rows": int(len(df)),
    "clean_rows": int(len(clean)),
    "rejected_rows": int(len(rejected)),
    "exact_duplicates_removed": duplicate_count,
    "cancellation_rows_in_clean_data": int(clean["is_cancellation"].sum()),
    "missing_customer_ids_in_clean_data": int(clean["CustomerID"].isna().sum()),
    "revenue_sum_in_clean_data": round(float(clean["revenue"].sum()), 2)
}

with open(REPORT_DIR / "online_retail_quality_report.json", "w") as f:
    json.dump(report, f, indent=2)

print("\n--- ETL SUMMARY ---")
for key, value in report.items():
    print(f"{key}: {value}")

print("\nETL completed successfully!")
