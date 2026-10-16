import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "retailai.db"

con = sqlite3.connect(DB_PATH)

print("Total rows:")
print(con.execute(
    "SELECT COUNT(*) FROM retail_sales"
).fetchone()[0])

print("\nDuplicate order IDs:")
print(con.execute("""
    SELECT COUNT(*)
    FROM (
        SELECT order_id
        FROM retail_sales
        GROUP BY order_id
        HAVING COUNT(*) > 1
    )
""").fetchone()[0])

print("\nLatest records:")
for row in con.execute("""
    SELECT order_id, store, product, quantity, revenue
    FROM retail_sales
    ORDER BY CAST(order_id AS INTEGER) DESC
    LIMIT 5
"""):
    print(row)

con.close()