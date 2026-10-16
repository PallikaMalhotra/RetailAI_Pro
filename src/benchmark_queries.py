
import sqlite3
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "online_retail.db"

con = sqlite3.connect(DB_PATH)

query = """
SELECT country, ROUND(SUM(revenue), 2) AS total_revenue
FROM retail_transactions
GROUP BY country
ORDER BY total_revenue DESC
"""

def benchmark(label):
    # Warm up the query
    con.execute(query).fetchall()

    runs = 5
    timings = []

    for _ in range(runs):
        start = time.perf_counter()
        con.execute(query).fetchall()
        timings.append(time.perf_counter() - start)

    avg_ms = sum(timings) / len(timings) * 1000
    print(f"{label}: average {avg_ms:.2f} ms over {runs} runs")

print("--- QUERY PERFORMANCE TEST ---")

benchmark("Before index")

con.execute("""
    CREATE INDEX IF NOT EXISTS idx_retail_country
    ON retail_transactions(country)
""")
con.commit()

benchmark("After country index")

print("\n--- QUERY PLAN ---")
for row in con.execute(
    "EXPLAIN QUERY PLAN " + query
):
    print(row)

con.close()
