
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"

# Find the Excel dataset
excel_files = list(RAW_DIR.glob("*.xlsx"))

if not excel_files:
    raise FileNotFoundError(
        f"No .xlsx file found in {RAW_DIR}"
    )

FILE_PATH = excel_files[0]

print("Dataset:", FILE_PATH.name)
print("\nReading dataset...")

df = pd.read_excel(FILE_PATH)

print("\n--- BASIC INFORMATION ---")
print("Total rows:", len(df))
print("Total columns:", len(df.columns))

print("\n--- COLUMN NAMES ---")
print(df.columns.tolist())

print("\n--- FIRST 5 ROWS ---")
print(df.head())

print("\n--- DATA TYPES ---")
print(df.dtypes)

print("\n--- MISSING VALUES ---")
print(df.isnull().sum())

print("\n--- DUPLICATE ROWS ---")
print("Exact duplicate rows:", df.duplicated().sum())

print("\n--- NUMERIC SUMMARY ---")
print(df.describe())

print("\nDataset inspection completed!")
