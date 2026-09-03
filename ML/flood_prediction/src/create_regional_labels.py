import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

WEATHER_FILE = BASE_DIR / "data" / "regional_daily_features.csv"
FLOOD_FILE = BASE_DIR / "data" / "India_Flood_Inventory_v3.csv"
OUTPUT_FILE = BASE_DIR / "data" / "regional_labeled_data.csv"


# Load data
weather = pd.read_csv(WEATHER_FILE)
floods = pd.read_csv(FLOOD_FILE)

weather["date"] = pd.to_datetime(weather["date"])

floods["Start Date"] = pd.to_datetime(
    floods["Start Date"],
    errors="coerce",
    dayfirst=True
)

floods["End Date"] = pd.to_datetime(
    floods["End Date"],
    errors="coerce",
    dayfirst=True
)


# Start with no flood
weather["flood"] = 0


# --------------------------------------------------
# Match each weather region against flood events
# --------------------------------------------------

for _, event in floods.iterrows():

    district = event["Districts"]
    start = event["Start Date"]
    end = event["End Date"]

    if pd.isna(district) or pd.isna(start) or pd.isna(end):
        continue

    mask = (
        (weather["district"] == district) &
        (weather["date"] >= start) &
        (weather["date"] <= end)
    )

    weather.loc[mask, "flood"] = 1


# Save
weather.to_csv(OUTPUT_FILE, index=False)


print("Regional flood labels created!")

print("\nDataset shape:")
print(weather.shape)

print("\nRegions:")
print(weather["district"].nunique())

print("\nClass distribution:")
print(weather["flood"].value_counts())

print("\nClass percentage:")
print(
    (weather["flood"].value_counts(normalize=True) * 100).round(2)
)

print("\nFlood samples:")
print(
    weather[weather["flood"] == 1][
        [
            "district",
            "state",
            "date",
            "rainfall",
            "rainfall_3day",
            "rainfall_7day",
            "flood"
        ]
    ].head(30).to_string(index=False)
)

print("\nSaved to:")
print(OUTPUT_FILE)