import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "data" / "landslide_catalog.csv"
OUTPUT_FILE = BASE_DIR / "data" / "india_landslides.csv"

df = pd.read_csv(INPUT_FILE)

india = df[
    (df["country_code"] == "IN") |
    (df["country_name"].str.lower() == "india")
].copy()

india["event_date"] = pd.to_datetime(
    india["event_date"],
    errors="coerce"
)

india = india.dropna(
    subset=["event_date", "latitude", "longitude"]
)

print("India landslide events:")
print(len(india))

print("\nDate range:")
print(india["event_date"].min())
print(india["event_date"].max())

print("\nTop states/regions:")
print(
    india["admin_division_name"]
    .value_counts()
    .head(20)
)

print("\nLandslide triggers:")
print(
    india["landslide_trigger"]
    .value_counts()
)

india.to_csv(
    OUTPUT_FILE,
    index=False
)

print("\nSaved to:")
print(OUTPUT_FILE)