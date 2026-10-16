
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / "data" / "processed" / "online_retail_clean.csv"

df = pd.read_csv(FILE)

print("Clean rows:", len(df))
print("Columns:", df.columns.tolist())
print("Duplicate rows:", df.duplicated().sum())
print("\nMissing values:")
print(df.isna().sum())
print("\nSample:")
print(df.head())
