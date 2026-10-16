
import sqlite3
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

CLEAN_FILE = ROOT / "data" / "processed" / "online_retail_clean.csv"
DB_PATH = ROOT / "data" / "online_retail.db"

if not CLEAN_FILE.exists():
    raise FileNotFoundError(
        f"Clean dataset not found: {CLEAN_FILE}"
    )

df = pd.read_csv(CLEAN_FILE)

if "source_row" not in df.columns:
    raise ValueError(
        "source_row missing. Run py src/retail_etl.py first."
    )

df["transaction_id"] = df["source_row"].astype(str)

columns = [
    "transaction_id", "InvoiceNo", "StockCode", "Description",
    "Quantity", "InvoiceDate", "UnitPrice", "CustomerID",
    "Country", "revenue", "is_cancellation"
]

df["CustomerID"] = df["CustomerID"].astype("Int64").astype("string")

con = sqlite3.connect(DB_PATH)

try:
    inserted = 0
    updated = 0
    unchanged = 0

    con.execute("BEGIN")

    for row in df[columns].itertuples(index=False, name=None):
        transaction_id = str(row[0])

        values = (
            str(row[1]),
            str(row[2]),
            None if pd.isna(row[3]) else str(row[3]),
            int(row[4]),
            str(row[5]),
            float(row[6]),
            None if pd.isna(row[7]) else str(row[7]),
            None if pd.isna(row[8]) else str(row[8]),
            float(row[9]),
            int(bool(row[10]))
        )

        existing = con.execute("""
            SELECT invoice_no, stock_code, description, quantity,
                   invoice_date, unit_price, customer_id, country,
                   revenue, is_cancellation
            FROM retail_transactions
            WHERE transaction_id = ?
        """, (transaction_id,)).fetchone()

        if existing is None:
            con.execute("""
                INSERT INTO retail_transactions (
                    transaction_id, invoice_no, stock_code, description,
                    quantity, invoice_date, unit_price, customer_id,
                    country, revenue, is_cancellation
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (transaction_id, *values))
            inserted += 1

        elif tuple(existing) == values:
            unchanged += 1

        else:
            con.execute("""
                UPDATE retail_transactions
                SET invoice_no = ?, stock_code = ?, description = ?,
                    quantity = ?, invoice_date = ?, unit_price = ?,
                    customer_id = ?, country = ?, revenue = ?,
                    is_cancellation = ?
                WHERE transaction_id = ?
            """, (*values, transaction_id))
            updated += 1

    con.commit()

    total = con.execute(
        "SELECT COUNT(*) FROM retail_transactions"
    ).fetchone()[0]

    print("Incoming rows:", len(df))
    print("Inserted:", inserted)
    print("Updated:", updated)
    print("Unchanged:", unchanged)
    print("Total database rows:", total)

except Exception:
    con.rollback()
    raise

finally:
    con.close()
