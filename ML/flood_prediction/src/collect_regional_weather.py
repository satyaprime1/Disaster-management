import pandas as pd
import requests
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

REGIONS_FILE = BASE_DIR / "data" / "training_regions_geocoded.csv"
OUTPUT_FILE = BASE_DIR / "data" / "regional_weather_data.csv"

URL = "https://archive-api.open-meteo.com/v1/archive"

regions = pd.read_csv(REGIONS_FILE)

# Load previous progress if it exists
if OUTPUT_FILE.exists():
    existing = pd.read_csv(OUTPUT_FILE)
    completed = set(existing["district"].unique())

    print(f"Already collected: {len(completed)} regions")

else:
    existing = pd.DataFrame()
    completed = set()


all_data = []

for _, row in regions.iterrows():

    district = row["district"]

    # Skip regions already downloaded
    if district in completed:
        print(f"Skipping: {district}")
        continue

    params = {
        "latitude": row["latitude"],
        "longitude": row["longitude"],
        "start_date": "2020-01-01",
        "end_date": "2022-12-31",
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

    print(f"Collecting: {district}, {row['state']}")

    success = False

    for attempt in range(5):

        try:

            response = requests.get(
                URL,
                params=params,
                timeout=120
            )

            if response.status_code == 429:

                wait_time = 30 * (attempt + 1)

                print(
                    f"Rate limited. Waiting {wait_time} seconds..."
                )

                time.sleep(wait_time)
                continue

            response.raise_for_status()

            data = response.json()

            weather = pd.DataFrame(data["hourly"])

            weather["district"] = district
            weather["state"] = row["state"]
            weather["latitude"] = row["latitude"]
            weather["longitude"] = row["longitude"]

            all_data.append(weather)

            success = True

            print(f"✅ Completed: {district}")

            break

        except Exception as e:

            print(
                f"Attempt {attempt + 1}/5 failed: {e}"
            )

            time.sleep(15)

    if not success:

        print(f"❌ Failed: {district}")
        continue

    # Save progress after every successful region
    current = pd.concat(
        [existing] + all_data,
        ignore_index=True
    )

    current.to_csv(
        OUTPUT_FILE,
        index=False
    )

    existing = current
    all_data = []

    # Slow down requests
    time.sleep(10)


print("\n==============================")
print("Regional weather collection complete!")
print("Rows:", len(existing))
print("Regions:", existing["district"].nunique())
print("Saved to:")
print(OUTPUT_FILE)
print("==============================")