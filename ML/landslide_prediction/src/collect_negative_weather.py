import pandas as pd
import requests
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "data" / "landslide_events_prepared.csv"
NEGATIVE_FILE = BASE_DIR / "data" / "landslide_negative_weather.csv"

URL = "https://archive-api.open-meteo.com/v1/archive"

events = pd.read_csv(INPUT_FILE)

events["date"] = pd.to_datetime(
    events["date"],
    format="mixed",
    errors="coerce"
)

events = events.dropna(
    subset=["date", "latitude", "longitude"]
)

results = []

print("Starting negative weather collection...")
print("Events:", len(events))
print("=" * 50)

for i, row in events.iterrows():

    latitude = row["latitude"]
    longitude = row["longitude"]
    event_date = row["date"]

    # Choose a date 14 days before the landslide event
    negative_date = event_date - pd.Timedelta(days=14)

    date_str = negative_date.strftime("%Y-%m-%d")

    print(
        f"[{i + 1}/{len(events)}] "
        f"{row['admin_division_name']} → {date_str}"
    )

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": date_str,
        "end_date": date_str,
        "hourly": ",".join([
            "temperature_2m",
            "relative_humidity_2m",
            "pressure_msl",
            "precipitation",
            "rain",
            "soil_moisture_0_to_7cm",
            "soil_moisture_7_to_28cm",
            "soil_moisture_28_to_100cm",
        ]),
        "timezone": "Asia/Kolkata",
    }

    success = False

    for attempt in range(4):

        try:

            response = requests.get(
                URL,
                params=params,
                timeout=120
            )

            # Open-Meteo rate limit
            if response.status_code == 429:

                wait = 30 * (attempt + 1)

                print(
                    f"Rate limited. "
                    f"Waiting {wait} seconds..."
                )

                time.sleep(wait)
                continue

            response.raise_for_status()

            data = response.json()

            if "hourly" not in data:
                raise ValueError(
                    "Hourly weather data missing"
                )

            weather = pd.DataFrame(
                data["hourly"]
            )

            if weather.empty:
                raise ValueError(
                    "No weather data returned"
                )

            result = {
                "date": negative_date.date(),

                "latitude": latitude,

                "longitude": longitude,

                "region": row[
                    "admin_division_name"
                ],

                "rainfall": weather[
                    "precipitation"
                ].sum(),

                # For a single-day request these are
                # the actual rainfall for that day.
                "rainfall_3day": weather[
                    "precipitation"
                ].sum(),

                "rainfall_7day": weather[
                    "precipitation"
                ].sum(),

                "max_hourly_rain": weather[
                    "precipitation"
                ].max(),

                "avg_temperature": weather[
                    "temperature_2m"
                ].mean(),

                "max_temperature": weather[
                    "temperature_2m"
                ].max(),

                "min_temperature": weather[
                    "temperature_2m"
                ].min(),

                "avg_humidity": weather[
                    "relative_humidity_2m"
                ].mean(),

                "avg_pressure": weather[
                    "pressure_msl"
                ].mean(),

                "min_pressure": weather[
                    "pressure_msl"
                ].min(),

                "avg_soil_moisture_0_7": weather[
                    "soil_moisture_0_to_7cm"
                ].mean(),

                "avg_soil_moisture_7_28": weather[
                    "soil_moisture_7_to_28cm"
                ].mean(),

                "avg_soil_moisture_28_100": weather[
                    "soil_moisture_28_to_100cm"
                ].mean(),

                "landslide": 0
            }

            results.append(result)

            success = True
            break

        except Exception as e:

            print(
                f"Attempt {attempt + 1} failed: {e}"
            )

            if attempt < 3:
                time.sleep(15)

    if not success:

        print(
            "FAILED:",
            latitude,
            longitude,
            negative_date
        )

    # Save progress every 25 successful records
    if len(results) % 25 == 0 and results:

        pd.DataFrame(results).to_csv(
            NEGATIVE_FILE,
            index=False
        )

        print(
            f"Progress saved: "
            f"{len(results)} records"
        )

    # Avoid hitting API too quickly
    time.sleep(2)


# Final save
negative_df = pd.DataFrame(results)

negative_df.to_csv(
    NEGATIVE_FILE,
    index=False
)

print("\n" + "=" * 50)
print("Negative weather collection complete!")
print("Rows:", len(negative_df))

print("\nClass distribution:")
print(
    negative_df["landslide"].value_counts()
)

print("\nSaved to:")
print(NEGATIVE_FILE)

print("=" * 50)