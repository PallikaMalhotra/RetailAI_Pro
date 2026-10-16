-- RetailAI Star Schema
-- Source: retail_transactions
-- SQLite analytical data warehouse tables

PRAGMA foreign_keys = ON;

-- 1. Product dimension
CREATE TABLE IF NOT EXISTS DimProduct (
    product_key INTEGER PRIMARY KEY,
    stock_code TEXT NOT NULL,
    description TEXT,
    UNIQUE (stock_code, description)
);

-- 2. Customer dimension
CREATE TABLE IF NOT EXISTS DimCustomer (
    customer_key INTEGER PRIMARY KEY,
    customer_id TEXT,
    country TEXT,
    UNIQUE (customer_id, country)
);

-- 3. Date dimension
CREATE TABLE IF NOT EXISTS DimDate (
    date_key INTEGER PRIMARY KEY,
    full_date TEXT NOT NULL UNIQUE,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    day INTEGER NOT NULL
);

-- 4. Sales fact table
CREATE TABLE IF NOT EXISTS FactSales (
    sales_key INTEGER PRIMARY KEY,
    transaction_id TEXT NOT NULL UNIQUE,
    product_key INTEGER NOT NULL,
    customer_key INTEGER,
    date_key INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price REAL NOT NULL,
    revenue REAL NOT NULL,
    is_cancellation INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (product_key) REFERENCES DimProduct(product_key),
    FOREIGN KEY (customer_key) REFERENCES DimCustomer(customer_key),
    FOREIGN KEY (date_key) REFERENCES DimDate(date_key)
);

-- Indexes for common analytical joins
CREATE INDEX IF NOT EXISTS idx_factsales_product
    ON FactSales(product_key);

CREATE INDEX IF NOT EXISTS idx_factsales_customer
    ON FactSales(customer_key);

CREATE INDEX IF NOT EXISTS idx_factsales_date
    ON FactSales(date_key);