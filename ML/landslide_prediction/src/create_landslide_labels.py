import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

WEATHER_FILE = BASE_DIR / "data" / "landslide_weather.csv"
OUTPUT_FILE = BASE_DIR / "data" / "landslide_labeled_data.csv"

df = pd.read_csv(WEATHER_FILE)

df["date"] = pd.to_datetime(df["date"])

# Every row currently represents a real landslide event
positive = df.copy()
positive["landslide"] = 1

# Create negative samples by shifting each event date
# to a nearby day from the same location.
negative = df.copy()

negative["date"] = negative["date"] - pd.Timedelta(days=7)
negative["landslide"] = 0

# Keep the same weather features but avoid copying
# the original event date.
negative = negative[
    [
        "date",
        "latitude",
        "longitude",
        "region",
        "rainfall",
        "rainfall_3day",
        "rainfall_7day",
        "max_hourly_rain",
        "avg_temperature",
        "max_temperature",
        "min_temperature",
        "avg_humidity",
        "avg_pressure",
        "min_pressure",
        "avg_soil_moisture_0_7",
        "avg_soil_moisture_7_28",
        "avg_soil_moisture_28_100",
        "landslide",
    ]
]

positive = positive[
    [
        "date",
        "latitude",
        "longitude",
        "region",
        "rainfall",
        "rainfall_3day",
        "rainfall_7day",
        "max_hourly_rain",
        "avg_temperature",
        "max_temperature",
        "min_temperature",
        "avg_humidity",
        "avg_pressure",
        "min_pressure",
        "avg_soil_moisture_0_7",
        "avg_soil_moisture_7_28",
        "avg_soil_moisture_28_100",
        "landslide",
    ]
]

labeled = pd.concat(
    [positive, negative],
    ignore_index=True
)

# Remove accidental duplicate location/date records
labeled = labeled.drop_duplicates(
    subset=["date", "latitude", "longitude"]
)

# Shuffle
labeled = labeled.sample(
    frac=1,
    random_state=42
).reset_index(drop=True)

labeled.to_csv(
    OUTPUT_FILE,
    index=False
)

print("Landslide labeling complete!")

print("\nDataset shape:")
print(labeled.shape)

print("\nClass distribution:")
print(labeled["landslide"].value_counts())

print("\nClass percentage:")
print(
    (labeled["landslide"].value_counts(normalize=True) * 100).round(2)
)

print("\nSaved to:")
print(OUTPUT_FILE)