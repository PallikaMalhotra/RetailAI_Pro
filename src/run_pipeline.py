
import subprocess
import sys
import logging
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(
            LOG_DIR / "pipeline_run.log",
            encoding="utf-8"
        ),
        logging.StreamHandler()
    ]
)

STEPS = [
    "retail_etl.py",
    "test_retail_quality.py",
    "load_retail_database.py",
    "verify_retail_database.py",
    "pipeline_monitor.py"
]

def run_step(filename):
    script = ROOT / "src" / filename

    logging.info("Starting step: %s", filename)

    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=ROOT,
        text=True
    )

    if result.returncode != 0:
        logging.error("Step failed: %s", filename)
        raise RuntimeError(
            f"Pipeline stopped because {filename} failed"
        )

    logging.info("Step completed: %s", filename)

def main():
    start = datetime.now(timezone.utc)
    logging.info("RetailAI pipeline started")

    try:
        for step in STEPS:
            run_step(step)

        logging.info("RetailAI pipeline completed successfully")

    except Exception:
        logging.exception("RetailAI pipeline failed")
        sys.exit(1)

    finally:
        duration = (
            datetime.now(timezone.utc) - start
        ).total_seconds()

        logging.info("Total duration: %.2f seconds", duration)

if __name__ == "__main__":
    main()
