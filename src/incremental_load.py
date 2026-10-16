import sqlite3
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

DB_PATH = ROOT / "data" / "retailai.db"
CLEAN_FILE = ROOT / "data" / "processed" / "retail_sales_clean.csv"
INCOMING_FILE = ROOT / "data" / "incoming" / "new_sales.csv"

DB_PATH.parent.mkdir(parents=True, exist_ok=True)

if not CLEAN_FILE.exists():
    raise FileNotFoundError(f"Clean file not found: {CLEAN_FILE}")

if not INCOMING_FILE.exists():
    raise FileNotFoundError(f"Incoming file not found: {INCOMING_FILE}")

columns = [
    "order_id", "store", "product", "quantity",
    "order_date", "unit_price", "revenue"
]

con = sqlite3.connect(DB_PATH)

try:
    con.execute("""
        CREATE TABLE IF NOT EXISTS retail_sales (
            order_id TEXT PRIMARY KEY,
            store TEXT NOT NULL,
            product TEXT NOT NULL,
            quantity INTEGER NOT NULL CHECK (quantity > 0),
            order_date TEXT NOT NULL,
            unit_price REAL NOT NULL CHECK (unit_price >= 0),
            revenue REAL NOT NULL CHECK (revenue >= 0)
        )
    """)

    row_count = con.execute(
        "SELECT COUNT(*) FROM retail_sales"
    ).fetchone()[0]

    if row_count == 0:
        initial = pd.read_csv(CLEAN_FILE)
        initial["order_id"] = initial["order_id"].astype(str)

        records = list(
            initial[columns].itertuples(index=False, name=None)
        )

        con.executemany("""
            INSERT INTO retail_sales
            (order_id, store, product, quantity, order_date,
             unit_price, revenue)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, records)

        con.commit()
        print(f"Initial load complete: {len(records)} rows")

    incoming = pd.read_csv(INCOMING_FILE)
    incoming["order_id"] = incoming["order_id"].astype(str)

    inserted = 0
    updated = 0
    unchanged = 0

    con.execute("BEGIN")

    for record in incoming[columns].itertuples(
        index=False, name=None
    ):
        order_id = record[0]

        existing = con.execute("""
            SELECT store, product, quantity, order_date,
                   unit_price, revenue
            FROM retail_sales
            WHERE order_id = ?
        """, (order_id,)).fetchone()

        if existing is None:
            con.execute("""
                INSERT INTO retail_sales
                (order_id, store, product, quantity, order_date,
                 unit_price, revenue)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, record)

            inserted += 1

        else:
            new_values = record[1:]

            if tuple(existing) == tuple(new_values):
                unchanged += 1
            else:
                con.execute("""
                    UPDATE retail_sales
                    SET store = ?, product = ?, quantity = ?,
                        order_date = ?, unit_price = ?, revenue = ?
                    WHERE order_id = ?
                """, (*new_values, order_id))

                updated += 1

    con.commit()

    total = con.execute(
        "SELECT COUNT(*) FROM retail_sales"
    ).fetchone()[0]

    print(f"Incoming rows: {len(incoming)}")
    print(f"New records inserted: {inserted}")
    print(f"Existing records updated: {updated}")
    print(f"Unchanged records skipped: {unchanged}")
    print(f"Total unique order IDs: {total}")

except Exception:
    con.rollback()
    raise

finally:
    con.close()

print("Incremental loading script completed")
print("Database path:", DB_PATH)
print("Incoming file exists:", INCOMING_FILE.exists())