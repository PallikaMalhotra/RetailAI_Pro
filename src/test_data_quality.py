
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

file_path = ROOT / "data" / "processed" / "retail_sales_clean.csv"

df = pd.read_csv(file_path)

print("Running data quality tests...\n")

# Test 1: Check duplicate order IDs
assert df["order_id"].is_unique, "Duplicate order IDs found!"

# Test 2: Check missing store names
assert df["store"].notna().all(), "Missing store names found!"

# Test 3: Check valid quantities
assert (df["quantity"] > 0).all(), "Invalid quantities found!"

# Test 4: Check non-negative revenue
assert (df["revenue"] >= 0).all(), "Negative revenue found!"

# Test 5: Check missing product names
assert df["product"].notna().all(), "Missing product names found!"

print("PASS: No duplicate order IDs")
print("PASS: No missing store names")
print("PASS: All quantities are positive")
print("PASS: Revenue is non-negative")
print("PASS: No missing product names")
print("\nAll data quality tests passed!")
