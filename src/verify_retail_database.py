
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "online_retail.db"

con = sqlite3.connect(DB_PATH)

print("\n--- DATABASE SUMMARY ---")

print(
    "Total transaction rows:",
    con.execute(
        "SELECT COUNT(*) FROM retail_transactions"
    ).fetchone()[0]
)

print(
    "Unique transaction IDs:",
    con.execute(
        "SELECT COUNT(DISTINCT transaction_id) "
        "FROM retail_transactions"
    ).fetchone()[0]
)

print(
    "Countries:",
    con.execute(
        "SELECT COUNT(DISTINCT country) "
        "FROM retail_transactions"
    ).fetchone()[0]
)

print("\n--- TOP 5 COUNTRIES BY REVENUE ---")
for row in con.execute("""
    SELECT country, ROUND(SUM(revenue), 2) AS revenue
    FROM retail_transactions
    GROUP BY country
    ORDER BY revenue DESC
    LIMIT 5
"""):
    print(row)

print("\n--- TOP 5 PRODUCTS BY QUANTITY ---")
for row in con.execute("""
    SELECT stock_code, SUM(quantity) AS total_quantity
    FROM retail_transactions
    GROUP BY stock_code
    ORDER BY total_quantity DESC
    LIMIT 5
"""):
    print(row)

print("\n--- MONTHLY REVENUE ---")
for row in con.execute("""
    SELECT SUBSTR(invoice_date, 1, 7) AS month,
           ROUND(SUM(revenue), 2) AS revenue
    FROM retail_transactions
    GROUP BY month
    ORDER BY month
    LIMIT 12
"""):
    print(row)

con.close()
