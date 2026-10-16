from pathlib import Path
import sqlite3

import pytest

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "online_retail.db"


@pytest.fixture(scope="module")
def con():
    assert DB_PATH.exists(), f"Database missing: {DB_PATH}"
    connection = sqlite3.connect(DB_PATH)
    yield connection
    connection.close()


def test_star_schema_tables_exist(con):
    tables = {
        row[0]
        for row in con.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }

    assert {"DimProduct", "DimCustomer", "DimDate", "FactSales"} <= tables


def test_fact_row_count_matches_source(con):
    source_count = con.execute(
        "SELECT COUNT(*) FROM retail_transactions"
    ).fetchone()[0]

    fact_count = con.execute(
        "SELECT COUNT(*) FROM FactSales"
    ).fetchone()[0]

    assert fact_count == source_count


def test_fact_table_has_no_duplicate_transaction_ids(con):
    duplicates = con.execute("""
        SELECT COUNT(*)
        FROM (
            SELECT transaction_id
            FROM FactSales
            GROUP BY transaction_id
            HAVING COUNT(*) > 1
        )
    """).fetchone()[0]

    assert duplicates == 0


def test_fact_foreign_keys_are_valid(con):
    assert con.execute("""
        SELECT COUNT(*)
        FROM FactSales f
        LEFT JOIN DimProduct p ON f.product_key = p.product_key
        WHERE p.product_key IS NULL
    """).fetchone()[0] == 0

    assert con.execute("""
        SELECT COUNT(*)
        FROM FactSales f
        LEFT JOIN DimDate d ON f.date_key = d.date_key
        WHERE d.date_key IS NULL
    """).fetchone()[0] == 0


def test_country_revenue_query_returns_results(con):
    rows = con.execute("""
        SELECT c.country, ROUND(SUM(f.revenue), 2)
        FROM FactSales f
        JOIN DimCustomer c ON f.customer_key = c.customer_key
        WHERE f.is_cancellation = 0
        GROUP BY c.country
        ORDER BY SUM(f.revenue) DESC
        LIMIT 10
    """).fetchall()

    assert 0 < len(rows) <= 10
    assert all(country and revenue is not None for country, revenue in rows)
