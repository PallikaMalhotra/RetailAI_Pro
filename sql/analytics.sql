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

-- 1. Country-wise sales revenue
SELECT
    c.country,
    ROUND(SUM(f.revenue), 2) AS total_revenue
FROM FactSales f
JOIN DimCustomer c
    ON f.customer_key = c.customer_key
WHERE f.is_cancellation = 0
GROUP BY c.country
ORDER BY total_revenue DESC
LIMIT 10;


-- 2. Monthly revenue trend
SELECT
    d.year,
    d.month,
    ROUND(SUM(f.revenue), 2) AS monthly_revenue
FROM FactSales f
JOIN DimDate d
    ON f.date_key = d.date_key
WHERE f.is_cancellation = 0
GROUP BY d.year, d.month
ORDER BY d.year, d.month;


-- 3. Top 10 products by revenue
SELECT
    p.stock_code,
    p.description,
    ROUND(SUM(f.revenue), 2) AS total_revenue
FROM FactSales f
JOIN DimProduct p
    ON f.product_key = p.product_key
WHERE f.is_cancellation = 0
GROUP BY p.stock_code, p.description
ORDER BY total_revenue DESC
LIMIT 10;
