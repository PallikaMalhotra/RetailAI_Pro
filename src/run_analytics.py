import sqlite3
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
csv_path = ROOT / "data" / "processed" / "retail_sales_clean.csv"
df = pd.read_csv(csv_path)
con = sqlite3.connect(":memory:")
df.to_sql("retail_sales", con, index=False, if_exists="replace")

queries = {
    "Revenue by store": """
        SELECT store, ROUND(SUM(revenue), 2) AS total_revenue
        FROM retail_sales GROUP BY store ORDER BY total_revenue DESC
    """,
    "Top products": """
        SELECT product, SUM(quantity) AS units_sold, ROUND(SUM(revenue), 2) AS revenue
        FROM retail_sales GROUP BY product ORDER BY units_sold DESC
    """,
    "Monthly sales trend": """
        SELECT substr(order_date, 1, 7) AS month, ROUND(SUM(revenue), 2) AS revenue
        FROM retail_sales GROUP BY month ORDER BY month
    """,
}
for title, query in queries.items():
    print(f"\\n--- {title} ---")
    print(pd.read_sql_query(query, con).to_string(index=False))
