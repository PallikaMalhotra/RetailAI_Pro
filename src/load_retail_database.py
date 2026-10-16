
import sqlite3
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

CLEAN_FILE = ROOT / "data" / "processed" / "online_retail_clean.csv"
DB_PATH = ROOT / "data" / "online_retail.db"

if not CLEAN_FILE.exists():
    raise FileNotFoundError(
        f"Clean dataset not found: {CLEAN_FILE}. Run retail_etl.py first."
    )

df = pd.read_csv(CLEAN_FILE)

# Keep source row identity from the ETL output.
# It must be present to load this version of the cleaned dataset.
if "source_row" not in df.columns:
    raise ValueError("source_row column is missing. Run retail_etl.py first.")

df["transaction_id"] = df["source_row"].astype(str)

columns = [
    "transaction_id", "InvoiceNo", "StockCode", "Description",
    "Quantity", "InvoiceDate", "UnitPrice", "CustomerID",
    "Country", "revenue", "is_cancellation"
]

df["CustomerID"] = df["CustomerID"].astype("Int64").astype("string")

DB_PATH.parent.mkdir(parents=True, exist_ok=True)
con = sqlite3.connect(DB_PATH)

try:
    con.execute("""
        CREATE TABLE IF NOT EXISTS retail_transactions (
            transaction_id TEXT PRIMARY KEY,
            invoice_no TEXT NOT NULL,
            stock_code TEXT NOT NULL,
            description TEXT,
            quantity INTEGER NOT NULL CHECK (quantity <> 0),
            invoice_date TEXT NOT NULL,
            unit_price REAL NOT NULL CHECK (unit_price >= 0),
            customer_id TEXT,
            country TEXT,
            revenue REAL NOT NULL,
            is_cancellation INTEGER NOT NULL
                CHECK (is_cancellation IN (0, 1))
        )
    """)

    records = []
    for row in df[columns].itertuples(index=False, name=None):
        records.append((
            str(row[0]), str(row[1]), str(row[2]),
            None if pd.isna(row[3]) else str(row[3]),
            int(row[4]), str(row[5]), float(row[6]),
            None if pd.isna(row[7]) else str(row[7]),
            None if pd.isna(row[8]) else str(row[8]),
            float(row[9]), int(bool(row[10]))
        ))

    # Explicit transaction; rollback if the load fails
    con.execute("BEGIN")
    con.execute("DELETE FROM retail_transactions")

    con.executemany("""
        INSERT INTO retail_transactions (
            transaction_id, invoice_no, stock_code, description,
            quantity, invoice_date, unit_price, customer_id,
            country, revenue, is_cancellation
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, records)

    con.commit()

    total = con.execute(
        "SELECT COUNT(*) FROM retail_transactions"
    ).fetchone()[0]

    print(f"Rows loaded: {total}")
    print(f"Database created at: {DB_PATH}")

except Exception:
    con.rollback()
    raise

finally:
    con.close()
