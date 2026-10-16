from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "online_retail.db"

def main():
    con = sqlite3.connect(DB_PATH)

    try:
        con.execute("PRAGMA foreign_keys = ON")

        # Create dimension and fact tables
        con.executescript(
            (ROOT / "sql" / "star_schema.sql").read_text(encoding="utf-8")
        )

        # Rebuild star-schema data safely on each run
        con.execute("BEGIN")
        con.execute("DELETE FROM FactSales")
        con.execute("DELETE FROM DimProduct")
        con.execute("DELETE FROM DimCustomer")
        con.execute("DELETE FROM DimDate")

        # Populate product dimension
        con.execute("""
            INSERT INTO DimProduct (stock_code, description)
            SELECT DISTINCT stock_code, description
            FROM retail_transactions
            WHERE stock_code IS NOT NULL
        """)

        # Populate customer dimension
        con.execute("""
            INSERT INTO DimCustomer (customer_id, country)
            SELECT DISTINCT customer_id, country
            FROM retail_transactions
            WHERE customer_id IS NOT NULL
        """)

        # Populate date dimension
        con.execute("""
            INSERT INTO DimDate (date_key, full_date, year, month, day)
            SELECT DISTINCT
                CAST(strftime('%Y%m%d', date(invoice_date)) AS INTEGER),
                date(invoice_date),
                CAST(strftime('%Y', invoice_date) AS INTEGER),
                CAST(strftime('%m', invoice_date) AS INTEGER),
                CAST(strftime('%d', invoice_date) AS INTEGER)
            FROM retail_transactions
            WHERE date(invoice_date) IS NOT NULL
        """)

        # Populate sales fact table
        con.execute("""
            INSERT INTO FactSales (
                transaction_id, product_key, customer_key, date_key,
                quantity, unit_price, revenue, is_cancellation
            )
            SELECT
                r.transaction_id,
                p.product_key,
                c.customer_key,
                d.date_key,
                r.quantity,
                r.unit_price,
                r.revenue,
                r.is_cancellation
            FROM retail_transactions r
            JOIN DimProduct p
              ON p.stock_code = r.stock_code
             AND p.description IS r.description
            LEFT JOIN DimCustomer c
              ON c.customer_id = CAST(r.customer_id AS TEXT)
             AND c.country IS r.country
            JOIN DimDate d
              ON d.full_date = date(r.invoice_date)
        """)

        con.commit()

        for table in ("DimProduct", "DimCustomer", "DimDate", "FactSales"):
            count = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(f"{table}: {count:,} rows")

        source_count = con.execute(
            "SELECT COUNT(*) FROM retail_transactions"
        ).fetchone()[0]
        fact_count = con.execute(
            "SELECT COUNT(*) FROM FactSales"
        ).fetchone()[0]

        print(f"Source rows: {source_count:,}")
        print(f"Fact rows:   {fact_count:,}")

        if source_count != fact_count:
            raise RuntimeError(
                "Source and fact row counts differ. Check source records "
                "that have missing product descriptions or invalid dates."
            )

        print("Star schema loaded and row counts verified.")

    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


if __name__ == "__main__":
    main()