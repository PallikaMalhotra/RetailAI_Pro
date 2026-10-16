-- Run these queries against data/processed/retail_sales_clean.csv using DuckDB.
-- First install DuckDB: pip install duckdb

-- 1. Revenue by store
SELECT store, ROUND(SUM(revenue), 2) AS total_revenue
FROM read_csv_auto('data/processed/retail_sales_clean.csv')
GROUP BY store
ORDER BY total_revenue DESC;

-- 2. Best-selling products by units
SELECT product, SUM(quantity) AS units_sold, ROUND(SUM(revenue), 2) AS revenue
FROM read_csv_auto('data/processed/retail_sales_clean.csv')
GROUP BY product
ORDER BY units_sold DESC;

-- 3. Monthly sales trend
SELECT strftime(TRY_CAST(order_date AS DATE), '%Y-%m') AS month,
       ROUND(SUM(revenue), 2) AS monthly_revenue
FROM read_csv_auto('data/processed/retail_sales_clean.csv')
GROUP BY month
ORDER BY month;

-- 4. Data quality summary
SELECT COUNT(*) AS rows, COUNT(DISTINCT order_id) AS distinct_orders
FROM read_csv_auto('data/processed/retail_sales_clean.csv');
