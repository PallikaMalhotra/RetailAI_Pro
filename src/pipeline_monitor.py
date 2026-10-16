
import logging
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "online_retail.db"
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "retailai_pipeline.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

def monitor_database():
    logging.info("RetailAI monitoring started")

    if not DB_PATH.exists():
        logging.error("Database not found: %s", DB_PATH)
        return

    try:
        with sqlite3.connect(DB_PATH) as con:
            total_rows = con.execute(
                "SELECT COUNT(*) FROM retail_transactions"
            ).fetchone()[0]

            unique_ids = con.execute(
                "SELECT COUNT(DISTINCT transaction_id) "
                "FROM retail_transactions"
            ).fetchone()[0]

            null_ids = con.execute(
                "SELECT COUNT(*) FROM retail_transactions "
                "WHERE transaction_id IS NULL"
            ).fetchone()[0]

        logging.info("Check time (UTC): %s",
                     datetime.now(timezone.utc).isoformat())
        logging.info("Total rows: %s", total_rows)
        logging.info("Unique transaction IDs: %s", unique_ids)
        logging.info("Null transaction IDs: %s", null_ids)

        if total_rows != unique_ids:
            logging.warning("Duplicate transaction IDs detected")

        if null_ids > 0:
            logging.warning("Null transaction IDs detected")

        logging.info("Monitoring completed successfully")

    except sqlite3.Error:
        logging.exception("Database monitoring failed")
        raise

if __name__ == "__main__":
    monitor_database()

