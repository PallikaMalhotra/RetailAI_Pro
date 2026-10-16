
import sqlite3
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "online_retail.db"

query = """
SELECT country, ROUND(SUM(revenue), 2) AS total_revenue
FROM retail_transactions
GROUP BY country
ORDER BY total_revenue DESC
LIMIT 10
"""

con = sqlite3.connect(DB_PATH)

# Warm-up
con.execute(query).fetchall()

runs = 5
times = []

for _ in range(runs):
    start = time.perf_counter()
    result = con.execute(query).fetchall()
    elapsed = time.perf_counter() - start
    times.append(elapsed)

print("SQLite average runtime (ms):",
      round(sum(times) / runs * 1000, 2))

print("\nTop 10 countries:")
for row in result:
    print(row)

con.close()
