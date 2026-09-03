import requests
import pandas as pd
import time
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = DATA_DIR / "regional_weather_data.csv"


# ============================================================
# CAPITAL CITIES
# ============================================================

CAPITALS = [
    ("Amaravati", "Andhra Pradesh", 16.5745, 80.3575),
    ("Itanagar", "Arunachal Pradesh", 27.0844, 93.6053),
    ("Dispur", "Assam", 26.1433, 91.7898),
    ("Patna", "Bihar", 25.5941, 85.1376),
    ("Raipur", "Chhattisgarh", 21.2514, 81.6296),
    ("Panaji", "Goa", 15.4909, 73.8278),
    ("Gandhinagar", "Gujarat", 23.2156, 72.6369),
    ("Chandigarh", "Haryana", 30.7333, 76.7794),
    ("Shimla", "Himachal Pradesh", 31.1048, 77.1734),
    ("Ranchi", "Jharkhand", 23.3441, 85.3096),
    ("Bengaluru", "Karnataka", 12.9716, 77.5946),
    ("Thiruvananthapuram", "Kerala", 8.5241, 76.9366),
    ("Bhopal", "Madhya Pradesh", 23.2599, 77.4126),
    ("Mumbai", "Maharashtra", 19.0760, 72.8777),
    ("Imphal", "Manipur", 24.8170, 93.9368),
    ("Shillong", "Meghalaya", 25.5788, 91.8933),
    ("Aizawl", "Mizoram", 23.7271, 92.7176),
    ("Kohima", "Nagaland", 25.6751, 94.1086),
    ("Bhubaneswar", "Odisha", 20.2961, 85.8245),
    ("Jaipur", "Rajasthan", 26.9124, 75.7873),
    ("Gangtok", "Sikkim", 27.3389, 88.6065),
    ("Chennai", "Tamil Nadu", 13.0827, 80.2707),
    ("Hyderabad", "Telangana", 17.3850, 78.4867),
    ("Agartala", "Tripura", 23.8315, 91.2868),
    ("Lucknow", "Uttar Pradesh", 26.8467, 80.9462),
    ("Dehradun", "Uttarakhand", 30.3165, 78.0322),
    ("Kolkata", "West Bengal", 22.5726, 88.3639),

    # Union Territories
    ("Port Blair", "Andaman and Nicobar Islands", 11.6234, 92.7265),
    ("Daman", "Dadra and Nagar Haveli and Daman and Diu", 20.3974, 72.8328),
    ("New Delhi", "Delhi", 28.6139, 77.2090),
    ("Srinagar", "Jammu and Kashmir", 34.0837, 74.7973),
    ("Jammu", "Jammu and Kashmir", 32.7266, 74.8570),
    ("Leh", "Ladakh", 34.1526, 77.5771),
    ("Kavaratti", "Lakshadweep", 10.5669, 72.6420),
    ("Puducherry", "Puducherry", 11.9416, 79.8083),
]


# ============================================================
# SETTINGS
# ============================================================

START_DATE = "2020-01-01"
END_DATE = "2025-12-31"

API_URL = "https://archive-api.open-meteo.com/v1/archive"


HOURLY_VARIABLES = [
    "temperature_2m",
    "relative_humidity_2m",
    "pressure_msl",
    "precipitation",
    "soil_moisture_0_to_7cm",
    "soil_moisture_7_to_28cm",
    "soil_moisture_28_to_100cm",
]


# ============================================================
# DOWNLOAD ONE CITY
# ============================================================

def download_city(city, state, latitude, longitude):

    print()
    print("=" * 60)
    print(f"Downloading: {city}, {state}")
    print("=" * 60)

    params = {
        "latitude": latitude,
        "longitude": longitude,

        "start_date": START_DATE,
        "end_date": END_DATE,

        "hourly": ",".join(HOURLY_VARIABLES),

        "timezone": "auto",

        "temperature_unit": "celsius",
        "precipitation_unit": "mm",
    }

    response = requests.get(
        API_URL,
        params=params,
        timeout=120
    )

    response.raise_for_status()

    data = response.json()

    if "hourly" not in data:
        raise RuntimeError(
            f"No hourly data returned for {city}"
        )

    hourly = data["hourly"]

    df = pd.DataFrame(hourly)

    df["district"] = city
    df["state"] = state

    # Keep requested coordinates
    df["latitude"] = latitude
    df["longitude"] = longitude

    # Make time column
    df["time"] = pd.to_datetime(df["time"])

    # Reorder
    columns = [
        "district",
        "state",
        "latitude",
        "longitude",
        "time",
        "temperature_2m",
        "relative_humidity_2m",
        "pressure_msl",
        "precipitation",
        "soil_moisture_0_to_7cm",
        "soil_moisture_7_to_28cm",
        "soil_moisture_28_to_100cm",
    ]

    df = df[columns]

    print(f"Rows downloaded: {len(df):,}")

    return df


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print("CAPITAL CITY HISTORICAL WEATHER DOWNLOADER")
    print("=" * 70)

    print(f"Cities: {len(CAPITALS)}")
    print(f"Period: {START_DATE} → {END_DATE}")
    print()

    all_data = []

    for index, (city, state, lat, lon) in enumerate(CAPITALS, start=1):

        print(
            f"\n[{index}/{len(CAPITALS)}] "
            f"{city}, {state}"
        )

        try:

            df = download_city(
                city,
                state,
                lat,
                lon
            )

            all_data.append(df)

            print("✓ Success")

        except Exception as e:

            print(f"✗ FAILED: {city}")
            print(f"Reason: {e}")

        # Avoid hammering the API
        time.sleep(1)


    # ========================================================
    # COMBINE
    # ========================================================

    if not all_data:

        raise RuntimeError(
            "No weather data was downloaded."
        )

    final_df = pd.concat(
        all_data,
        ignore_index=True
    )


    # ========================================================
    # SORT
    # ========================================================

    final_df = final_df.sort_values(
        ["district", "time"]
    ).reset_index(drop=True)


    # ========================================================
    # SAVE
    # ========================================================

    final_df.to_csv(
        OUTPUT_FILE,
        index=False
    )


    # ========================================================
    # SUMMARY
    # ========================================================

    print()
    print("=" * 70)
    print("DOWNLOAD COMPLETE")
    print("=" * 70)

    print()
    print("Dataset shape:")
    print(final_df.shape)

    print()
    print("Unique locations:")
    print(final_df["district"].nunique())

    print()
    print("Locations:")
    print(
        final_df["district"]
        .drop_duplicates()
        .to_string(index=False)
    )

    print()
    print("Time range:")
    print(final_df["time"].min())
    print("→")
    print(final_df["time"].max())

    print()
    print("Rows per location:")

    print(
        final_df
        .groupby("district")
        .size()
        .to_string()
    )

    print()
    print("Saved to:")
    print(OUTPUT_FILE)


if __name__ == "__main__":
    main()