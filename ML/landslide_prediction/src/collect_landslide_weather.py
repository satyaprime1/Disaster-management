import pandas as pd
import requests
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "data" / "landslide_events_prepared.csv"
OUTPUT_FILE = BASE_DIR / "data" / "landslide_weather.csv"

URL = "https://archive-api.open-meteo.com/v1/archive"

events = pd.read_csv(INPUT_FILE)

events["date"] = pd.to_datetime(events["date"])

results = []

for i, row in events.iterrows():

    latitude = row["latitude"]
    longitude = row["longitude"]
    date = row["date"]

    start_date = (date - pd.Timedelta(days=7)).strftime("%Y-%m-%d")
    end_date = date.strftime("%Y-%m-%d")

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
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

    print(
        f"[{i + 1}/{len(events)}] "
        f"{latitude}, {longitude} → {date.date()}"
    )

    success = False

    for attempt in range(4):

        try:

            response = requests.get(
                URL,
                params=params,
                timeout=120
            )

            if response.status_code == 429:

                wait = 30 * (attempt + 1)

                print(
                    f"Rate limited. Waiting {wait}s..."
                )

                time.sleep(wait)
                continue

            response.raise_for_status()

            data = response.json()

            weather = pd.DataFrame(
                data["hourly"]
            )

            weather["time"] = pd.to_datetime(
                weather["time"]
            )

            event_day = weather[
                weather["time"].dt.date == date.date()
            ]

            last_3_days = weather[
                weather["time"] >= date - pd.Timedelta(days=3)
            ]

            last_7_days = weather

            result = {
                "date": date.date(),
                "latitude": latitude,
                "longitude": longitude,
                "region": row["admin_division_name"],

                "rainfall": event_day[
                    "precipitation"
                ].sum(),

                "rainfall_3day": last_3_days[
                    "precipitation"
                ].sum(),

                "rainfall_7day": last_7_days[
                    "precipitation"
                ].sum(),

                "max_hourly_rain": event_day[
                    "precipitation"
                ].max(),

                "avg_temperature": event_day[
                    "temperature_2m"
                ].mean(),

                "max_temperature": event_day[
                    "temperature_2m"
                ].max(),

                "min_temperature": event_day[
                    "temperature_2m"
                ].min(),

                "avg_humidity": event_day[
                    "relative_humidity_2m"
                ].mean(),

                "avg_pressure": event_day[
                    "pressure_msl"
                ].mean(),

                "min_pressure": event_day[
                    "pressure_msl"
                ].min(),

                "avg_soil_moisture_0_7": event_day[
                    "soil_moisture_0_to_7cm"
                ].mean(),

                "avg_soil_moisture_7_28": event_day[
                    "soil_moisture_7_to_28cm"
                ].mean(),

                "avg_soil_moisture_28_100": event_day[
                    "soil_moisture_28_to_100cm"
                ].mean(),

                "landslide": 1
            }

            results.append(result)

            success = True
            break

        except Exception as e:

            print(
                f"Attempt {attempt + 1} failed: {e}"
            )

            time.sleep(15)

    if not success:

        print("FAILED:", latitude, longitude, date)

    # Save progress every 25 events
    if len(results) % 25 == 0 and results:

        pd.DataFrame(results).to_csv(
            OUTPUT_FILE,
            index=False
        )

        print("Progress saved.")

    time.sleep(2)


pd.DataFrame(results).to_csv(
    OUTPUT_FILE,
    index=False
)

print("\n==============================")
print("Landslide weather collection complete!")
print("Events:", len(results))
print("Saved to:")
print(OUTPUT_FILE)
print("==============================")