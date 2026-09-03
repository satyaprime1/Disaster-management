import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

POSITIVE_FILE = BASE_DIR / "data" / "landslide_weather.csv"
NEGATIVE_FILE = BASE_DIR / "data" / "landslide_negative_weather.csv"
OUTPUT_FILE = BASE_DIR / "data" / "landslide_final_data.csv"

positive = pd.read_csv(POSITIVE_FILE)
negative = pd.read_csv(NEGATIVE_FILE)

features = [
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

positive = positive[features]
negative = negative[features]

df = pd.concat(
    [positive, negative],
    ignore_index=True
)

df = df.drop_duplicates(
    subset=[
        "date",
        "latitude",
        "longitude"
    ]
)

df = df.sample(
    frac=1,
    random_state=42
).reset_index(drop=True)

df.to_csv(
    OUTPUT_FILE,
    index=False
)

print("Final landslide dataset created!")

print("\nDataset shape:")
print(df.shape)

print("\nClass distribution:")
print(df["landslide"].value_counts())

print("\nClass percentage:")
print(
    (
        df["landslide"]
        .value_counts(normalize=True) * 100
    ).round(2)
)

print("\nMissing values:")
print(df.isnull().sum())

print("\nSaved to:")
print(OUTPUT_FILE)