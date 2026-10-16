from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
REJECTED_DIR = ROOT / "data" / "rejected"
REPORT_DIR = ROOT / "reports"

COLUMN_MAP = {
    "orderid": "order_id", "transactionid": "order_id",
    "storename": "store", "branch": "store",
    "item": "product", "productname": "product",
    "qty": "quantity", "units": "quantity",
    "date": "order_date", "saledate": "order_date",
    "priceeach": "unit_price", "price": "unit_price",
    "salesamount": "revenue", "total": "revenue",
}

def standardize_columns(df):
    renamed = {}
    for col in df.columns:
        key = col.strip().replace(" ", "").replace("_", "").lower()
        # Canonical names are also normalized here.
        canonical = {
            "orderid": "order_id", "store": "store", "product": "product",
            "quantity": "quantity", "orderdate": "order_date",
            "unitprice": "unit_price", "revenue": "revenue",
        }
        renamed[col] = canonical.get(key, COLUMN_MAP.get(key, col.strip().lower()))
    return df.rename(columns=renamed)

def load_raw_files():
    frames = []
    for path in sorted(RAW_DIR.glob("*.csv")):
        df = pd.read_csv(path)
        df = standardize_columns(df)
        df["source_file"] = path.name
        frames.append(df)
    if not frames:
        raise FileNotFoundError(f"No CSV files found in {RAW_DIR}")
    return pd.concat(frames, ignore_index=True)

def run_pipeline():
    for folder in [PROCESSED_DIR, REJECTED_DIR, REPORT_DIR]:
        folder.mkdir(parents=True, exist_ok=True)

    raw = load_raw_files()
    raw_rows = len(raw)

    # Parse dates, coercing unparseable values to missing.
    raw["order_date"] = pd.to_datetime(raw["order_date"], errors="coerce", format="mixed", dayfirst=True)
    for col in ["quantity", "unit_price", "revenue"]:
        raw[col] = pd.to_numeric(raw[col], errors="coerce")
    raw["store"] = raw["store"].astype("string").str.strip()
    raw["product"] = raw["product"].astype("string").str.strip()
    raw["order_id"] = raw["order_id"].astype("string").str.strip()

    # Define validity rules; keep rejected records for audit rather than silently dropping them.
    invalid_mask = (
        raw["order_id"].isna() | (raw["order_id"] == "") |
        raw["store"].isna() | (raw["store"] == "") |
        raw["product"].isna() | (raw["product"] == "") |
        raw["order_date"].isna() |
        raw["quantity"].isna() | (raw["quantity"] <= 0) |
        raw["unit_price"].isna() | (raw["unit_price"] < 0) |
        raw["revenue"].isna() | (raw["revenue"] < 0)
    )
    rejected = raw[invalid_mask].copy()
    valid = raw[~invalid_mask].copy()

    # Duplicate key is order_id in this synthetic exercise. In a real project,
    # use the source system's true transaction/line-item key.
    before_dedupe = len(valid)
    valid = valid.drop_duplicates(subset=["order_id"], keep="first")
    duplicates_removed = before_dedupe - len(valid)

    valid["order_date"] = valid["order_date"].dt.strftime("%Y-%m-%d")
    valid["revenue"] = (valid["quantity"] * valid["unit_price"]).round(2)

    # Persist analytics-ready output in CSV and Parquet.
    valid.to_csv(PROCESSED_DIR / "retail_sales_clean.csv", index=False)
    try:
        valid.to_parquet(PROCESSED_DIR / "retail_sales_clean.parquet", index=False)
        parquet_status = "created"
    except ImportError:
        parquet_status = "not created (install pyarrow)"

    rejected.to_csv(REJECTED_DIR / "rejected_records.csv", index=False)

    report = {
        "raw_rows": int(raw_rows),
        "invalid_rows_quarantined": int(len(rejected)),
        "valid_rows_before_deduplication": int(before_dedupe),
        "duplicate_rows_removed": int(duplicates_removed),
        "clean_rows": int(len(valid)),
        "parquet_status": parquet_status,
        "source_files": [p.name for p in sorted(RAW_DIR.glob("*.csv"))],
    }
    (REPORT_DIR / "quality_report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    print(f"\nCleaned output: {PROCESSED_DIR / 'retail_sales_clean.csv'}")
    print(f"Rejected output: {REJECTED_DIR / 'rejected_records.csv'}")

if __name__ == "__main__":
    run_pipeline()
