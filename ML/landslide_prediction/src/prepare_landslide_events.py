import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "data" / "india_landslides.csv"
OUTPUT_FILE = BASE_DIR / "data" / "landslide_events_prepared.csv"

df = pd.read_csv(INPUT_FILE)

# Parse dates safely
df["event_date"] = pd.to_datetime(
    df["event_date"],
    format="mixed",
    errors="coerce"
)

df = df.dropna(
    subset=["event_date", "latitude", "longitude"]
)

# Keep rainfall-related events for the first model
rain_triggers = [
    "downpour",
    "rain",
    "continuous_rain",
    "monsoon",
    "tropical_cyclone",
    "flooding"
]

df = df[
    df["landslide_trigger"].isin(rain_triggers)
].copy()

# Normalize date to day
df["date"] = df["event_date"].dt.date

# Keep useful columns
df = df[
    [
        "date",
        "latitude",
        "longitude",
        "admin_division_name",
        "landslide_trigger"
    ]
]

# Remove duplicate event location/date combinations
df = df.drop_duplicates(
    subset=["date", "latitude", "longitude"]
)

df = df.sort_values("date")

df.to_csv(
    OUTPUT_FILE,
    index=False
)

print("Prepared landslide events!")
print("Events:", len(df))

print("\nDate range:")
print(df["date"].min())
print(df["date"].max())

print("\nRegions:")
print(df["admin_division_name"].nunique())

print("\nSaved to:")
print(OUTPUT_FILE)