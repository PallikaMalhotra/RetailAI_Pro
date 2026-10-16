from pathlib import Path
import json

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]

CLEAN_FILE = ROOT / "data" / "processed" / "online_retail_clean.csv"
REJECTED_FILE = ROOT / "data" / "rejected" / "online_retail_rejected.csv"
REPORT_FILE = ROOT / "reports" / "online_retail_quality_report.json"


@pytest.fixture(scope="module")
def clean():
    assert CLEAN_FILE.exists(), f"Clean CSV is missing: {CLEAN_FILE}"
    return pd.read_csv(CLEAN_FILE)


@pytest.fixture(scope="module")
def rejected():
    assert REJECTED_FILE.exists(), f"Rejected CSV is missing: {REJECTED_FILE}"
    return pd.read_csv(REJECTED_FILE)


@pytest.fixture(scope="module")
def report():
    assert REPORT_FILE.exists(), f"Quality report is missing: {REPORT_FILE}"
    with open(REPORT_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def test_required_output_files_exist():
    assert CLEAN_FILE.exists(), "Clean CSV is missing!"
    assert REJECTED_FILE.exists(), "Rejected CSV is missing!"
    assert REPORT_FILE.exists(), "Quality report is missing!"


def test_required_columns_exist(clean):
    required = [
        "InvoiceNo",
        "StockCode",
        "Quantity",
        "InvoiceDate",
        "UnitPrice",
        "revenue",
    ]

    missing = [column for column in required if column not in clean.columns]
    assert not missing, f"Missing columns: {missing}"


def test_no_duplicate_business_records(clean):
    business_columns = [
        "InvoiceNo",
        "StockCode",
        "Description",
        "Quantity",
        "InvoiceDate",
        "UnitPrice",
        "CustomerID",
        "Country",
    ]

    missing = [
        column for column in business_columns
        if column not in clean.columns
    ]
    assert not missing, f"Missing columns needed for duplicate check: {missing}"

    duplicates = clean.duplicated(subset=business_columns).sum()
    assert duplicates == 0, f"Found {duplicates} duplicate business records"


def test_numeric_values_are_valid(clean):
    assert clean["Quantity"].notna().all(), "Missing quantities found!"
    assert (clean["Quantity"] != 0).all(), "Zero quantities found!"

    assert clean["UnitPrice"].notna().all(), "Missing prices found!"
    assert (clean["UnitPrice"] >= 0).all(), "Negative prices found!"


def test_revenue_calculation(clean):
    expected_revenue = clean["Quantity"] * clean["UnitPrice"]

    matches = (
        clean["revenue"] - expected_revenue
    ).abs() < 0.001

    assert matches.all(), "Revenue calculation mismatch!"


def test_input_and_output_row_counts_reconcile(report):
    expected_input_rows = (
        report["clean_rows"]
        + report["rejected_rows"]
        + report["exact_duplicates_removed"]
    )

    assert report["input_rows"] == expected_input_rows, (
        "Input/output row counts do not reconcile!"
    )
