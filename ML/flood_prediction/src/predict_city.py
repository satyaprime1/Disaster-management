
import requests
import joblib
import pandas as pd
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_FILE = BASE_DIR / "models" / "regional_flood_model.pkl"

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"


# ============================================================
# MODEL
# ============================================================

# Load model once when backend starts
model = joblib.load(MODEL_FILE)


# ============================================================
# MODEL FEATURES
# ============================================================

# IMPORTANT:
# This order MUST match train_regional_model.py

MODEL_FEATURES = [
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
]


# ============================================================
# HELPERS
# ============================================================

def safe_round(value, digits=2):
    """
    Safely round a numeric value.
    """
    if pd.isna(value):
        return None

    return round(float(value), digits)


# ============================================================
# MAIN PREDICTION FUNCTION
# ============================================================

def predict_flood(city):

    # ========================================================
    # 1. GEOCODE CITY
    # ========================================================

    geo_params = {
        "name": city,
        "count": 1,
        "language": "en",
        "format": "json",
    }

    response = requests.get(
        GEOCODING_URL,
        params=geo_params,
        timeout=30
    )

    response.raise_for_status()

    geo = response.json()

    if "results" not in geo or not geo["results"]:
        raise ValueError(f"City not found: {city}")

    location = geo["results"][0]

    latitude = location["latitude"]
    longitude = location["longitude"]

    resolved_city = location.get("name", city)
    country = location.get("country", "")


    # ========================================================
    # 2. GET WEATHER DATA
    # ========================================================
    #
    # We request:
    #
    # CURRENT:
    #   - actual current temperature
    #   - actual current humidity
    #   - actual current pressure
    #   - current precipitation
    #
    # HOURLY:
    #   - past 8 days
    #
    # Why 8 days?
    #
    # The ML model was trained on COMPLETE DAILY DATA.
    # We therefore need enough history to construct:
    #
    #   latest completed day
    #   previous 3 days
    #   previous 7 days
    #
    # Today's incomplete data should NOT be treated as a
    # complete day.
    # ========================================================

    weather_params = {

        "latitude": latitude,
        "longitude": longitude,

        "past_days": 8,

        "current": ",".join([
            "temperature_2m",
            "relative_humidity_2m",
            "pressure_msl",
            "precipitation",
            "rain",
        ]),

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

    response = requests.get(
        WEATHER_URL,
        params=weather_params,
        timeout=60
    )

    response.raise_for_status()

    weather_data = response.json()


    # ========================================================
    # 3. CURRENT LIVE WEATHER
    # ========================================================

    current = weather_data.get("current", {})

    live_temperature = current.get("temperature_2m")
    live_humidity = current.get("relative_humidity_2m")
    live_pressure = current.get("pressure_msl")
    live_precipitation = current.get("precipitation")
    live_rain = current.get("rain")

    current_time = current.get("time")


    # ========================================================
    # 4. HOURLY DATAFRAME
    # ========================================================

    if "hourly" not in weather_data:
        raise ValueError("Hourly weather data unavailable")

    weather = pd.DataFrame(weather_data["hourly"])

    if weather.empty:
        raise ValueError("No weather data returned")

    weather["time"] = pd.to_datetime(
        weather["time"]
    )

    weather["date"] = weather["time"].dt.date


    # ========================================================
    # 5. REMOVE CURRENT INCOMPLETE DAY
    # ========================================================
    #
    # Training data was created like this:
    #
    # hourly data
    #       ↓
    # group by complete date
    #       ↓
    # daily features
    #
    # Therefore today's incomplete day should not be directly
    # used as a "full day".
    #
    # We use the latest completed calendar day.
    # ========================================================

    today = pd.Timestamp.now(
        tz="Asia/Kolkata"
    ).date()

    completed_days = weather[
        weather["date"] < today
    ].copy()


    # If timezone/date behavior gives us no completed day,
    # fall back to the latest available date.

    if completed_days.empty:

        latest_date = weather["date"].max()

        completed_days = weather[
            weather["date"] == latest_date
        ].copy()


    # ========================================================
    # 6. CREATE DAILY FEATURES
    # ========================================================

    daily = (
        completed_days
        .groupby("date")
        .agg(
            rainfall=(
                "precipitation",
                "sum"
            ),

            max_hourly_rain=(
                "precipitation",
                "max"
            ),

            avg_temperature=(
                "temperature_2m",
                "mean"
            ),

            max_temperature=(
                "temperature_2m",
                "max"
            ),

            min_temperature=(
                "temperature_2m",
                "min"
            ),

            avg_humidity=(
                "relative_humidity_2m",
                "mean"
            ),

            avg_pressure=(
                "pressure_msl",
                "mean"
            ),

            min_pressure=(
                "pressure_msl",
                "min"
            ),

            avg_soil_moisture_0_7=(
                "soil_moisture_0_to_7cm",
                "mean"
            ),

            avg_soil_moisture_7_28=(
                "soil_moisture_7_to_28cm",
                "mean"
            ),

            avg_soil_moisture_28_100=(
                "soil_moisture_28_to_100cm",
                "mean"
            ),
        )
        .reset_index()
    )


    if daily.empty:
        raise ValueError(
            "Unable to create daily weather features"
        )


    # ========================================================
    # 7. SORT DAILY DATA
    # ========================================================

    daily = daily.sort_values(
        "date"
    ).reset_index(drop=True)


    # ========================================================
    # 8. RAINFALL ROLLING FEATURES
    # ========================================================
    #
    # This matches:
    #
    # create_regional_daily_features.py
    #
    # rainfall_3day =
    # rolling 3-day rainfall
    #
    # rainfall_7day =
    # rolling 7-day rainfall
    # ========================================================

    daily["rainfall_3day"] = (
        daily["rainfall"]
        .rolling(
            window=3,
            min_periods=1
        )
        .sum()
    )

    daily["rainfall_7day"] = (
        daily["rainfall"]
        .rolling(
            window=7,
            min_periods=1
        )
        .sum()
    )


    # ========================================================
    # 9. GET LATEST COMPLETED DAY
    # ========================================================

    latest = daily.iloc[-1]


    # ========================================================
    # 10. BUILD MODEL INPUT
    # ========================================================

    features = {

        "rainfall":
            latest["rainfall"],

        "rainfall_3day":
            latest["rainfall_3day"],

        "rainfall_7day":
            latest["rainfall_7day"],

        "max_hourly_rain":
            latest["max_hourly_rain"],

        "avg_temperature":
            latest["avg_temperature"],

        "max_temperature":
            latest["max_temperature"],

        "min_temperature":
            latest["min_temperature"],

        "avg_humidity":
            latest["avg_humidity"],

        "avg_pressure":
            latest["avg_pressure"],

        "min_pressure":
            latest["min_pressure"],

        "avg_soil_moisture_0_7":
            latest["avg_soil_moisture_0_7"],

        "avg_soil_moisture_7_28":
            latest["avg_soil_moisture_7_28"],

        "avg_soil_moisture_28_100":
            latest["avg_soil_moisture_28_100"],
    }


    # ========================================================
    # 11. CREATE MODEL DATAFRAME
    # ========================================================

    X = pd.DataFrame(
        [features],
        columns=MODEL_FEATURES
    )


    # ========================================================
    # 12. HANDLE MISSING VALUES
    # ========================================================

    if X.isnull().any().any():

        # Fill missing numeric values using available
        # historical median.

        X = X.fillna(
            X.median(numeric_only=True)
        )

        # If anything is STILL missing, stop instead of
        # sending invalid data to the model.

        if X.isnull().any().any():

            raise ValueError(
                "Weather data contains missing values required "
                "for flood prediction"
            )


    # ========================================================
    # 13. FLOOD PREDICTION
    # ========================================================

    prediction = model.predict(X)[0]

    probability = model.predict_proba(X)[0][1]

    probability_percent = probability * 100


    # ========================================================
    # 14. RISK LEVEL
    # ========================================================

    if probability_percent >= 70:

        risk = "HIGH"

    elif probability_percent >= 40:

        risk = "MEDIUM"

    else:

        risk = "LOW"


    # ========================================================
    # 15. RETURN RESULT
    # ========================================================

    return {

        # ----------------------------------------------------
        # LOCATION
        # ----------------------------------------------------

        "location": {

            "city": resolved_city,

            "country": country,

            "latitude": latitude,

            "longitude": longitude,
        },


        # ----------------------------------------------------
        # FLOOD RESULT
        # ----------------------------------------------------

        "flood": {

            "prediction": int(prediction),

            "probability":
                round(
                    probability_percent,
                    2
                ),

            "risk": risk,

            "weather_records":
                len(weather),

            "prediction_date":
                str(latest["date"]),
        },


        # ----------------------------------------------------
        # LIVE WEATHER
        # ----------------------------------------------------
        #
        # IMPORTANT:
        # These values are ACTUAL CURRENT WEATHER.
        #
        # They are NOT the 7-day averages used by the model.
        # ----------------------------------------------------

        "live_weather": {

            "time":
                current_time,

            "temperature":
                safe_round(
                    live_temperature,
                    2
                ),

            "humidity":
                safe_round(
                    live_humidity,
                    2
                ),

            "pressure":
                safe_round(
                    live_pressure,
                    2
                ),

            "precipitation":
                safe_round(
                    live_precipitation,
                    2
                ),

            "rain":
                safe_round(
                    live_rain,
                    2
                ),
        },


        # ----------------------------------------------------
        # MODEL ENVIRONMENT
        # ----------------------------------------------------
        #
        # These are the features actually sent to the ML model.
        #
        # They represent the latest COMPLETED day.
        # ----------------------------------------------------

        "environment": {

            "rainfall":
                safe_round(
                    features["rainfall"],
                    2
                ),

            "rainfall_3day":
                safe_round(
                    features["rainfall_3day"],
                    2
                ),

            "rainfall_7day":
                safe_round(
                    features["rainfall_7day"],
                    2
                ),

            "max_hourly_rain":
                safe_round(
                    features["max_hourly_rain"],
                    2
                ),


            "temperature": {

                "average":
                    safe_round(
                        features["avg_temperature"],
                        2
                    ),

                "maximum":
                    safe_round(
                        features["max_temperature"],
                        2
                    ),

                "minimum":
                    safe_round(
                        features["min_temperature"],
                        2
                    ),
            },


            "humidity":
                safe_round(
                    features["avg_humidity"],
                    2
                ),


            "pressure": {

                "average":
                    safe_round(
                        features["avg_pressure"],
                        2
                    ),

                "minimum":
                    safe_round(
                        features["min_pressure"],
                        2
                    ),
            },


            "soil_moisture": {

                "0_7cm":
                    safe_round(
                        features[
                            "avg_soil_moisture_0_7"
                        ],
                        4
                    ),

                "7_28cm":
                    safe_round(
                        features[
                            "avg_soil_moisture_7_28"
                        ],
                        4
                    ),

                "28_100cm":
                    safe_round(
                        features[
                            "avg_soil_moisture_28_100"
                        ],
                        4
                    ),
            },
        },
    }

