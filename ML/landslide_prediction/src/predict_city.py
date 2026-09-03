import requests
import joblib
import pandas as pd

from pathlib import Path


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_FILE = BASE_DIR / "models" / "landslide_model.pkl"


# ============================================================
# MODEL FEATURES
# ============================================================

FEATURES = [
    "latitude",
    "longitude",
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
    "avg_soil_moisture_28_100"
]


# ============================================================
# LOAD MODEL
# ============================================================

model = joblib.load(MODEL_FILE)


# ============================================================
# API URLS
# ============================================================

GEOCODING_URL = (
    "https://geocoding-api.open-meteo.com/v1/search"
)

WEATHER_URL = (
    "https://api.open-meteo.com/v1/forecast"
)


# ============================================================
# GET CITY COORDINATES
# ============================================================

def get_coordinates(city):

    params = {
        "name": city,
        "count": 1,
        "language": "en",
        "format": "json"
    }

    response = requests.get(
        GEOCODING_URL,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    if "results" not in data:
        return None

    if not data["results"]:
        return None

    location = data["results"][0]

    return {
        "city": location.get(
            "name",
            city
        ),

        "country": location.get(
            "country",
            "Unknown"
        ),

        "latitude": float(
            location["latitude"]
        ),

        "longitude": float(
            location["longitude"]
        )
    }


# ============================================================
# GET WEATHER DATA
# ============================================================

def get_weather(
    latitude,
    longitude
):

    params = {

        "latitude": latitude,

        "longitude": longitude,

        "hourly": ",".join([

            "temperature_2m",

            "relative_humidity_2m",

            "pressure_msl",

            "precipitation",

            "rain",

            "soil_moisture_0_to_7cm",

            "soil_moisture_7_to_28cm",

            "soil_moisture_28_to_100cm"

        ]),

        "past_days": 7,

        "forecast_days": 1,

        "timezone": "Asia/Kolkata"
    }

    response = requests.get(
        WEATHER_URL,
        params=params,
        timeout=60
    )

    response.raise_for_status()

    data = response.json()

    if "hourly" not in data:
        raise ValueError(
            "Weather data unavailable."
        )

    return pd.DataFrame(
        data["hourly"]
    )


# ============================================================
# CREATE FEATURES
# ============================================================

def create_features(
    weather,
    latitude,
    longitude
):

    weather["time"] = pd.to_datetime(
        weather["time"]
    )

    weather = (
        weather
        .sort_values("time")
        .reset_index(drop=True)
    )

    # --------------------------------------------------------
    # USE CURRENT DAY / LATEST AVAILABLE DAY
    # --------------------------------------------------------

    latest_date = (
        weather["time"]
        .dt.date
        .max()
    )

    target_day = weather[
        weather["time"].dt.date == latest_date
    ]

    # --------------------------------------------------------
    # LAST 3 / 7 DAYS
    # --------------------------------------------------------

    last_time = weather["time"].max()

    last_3_days = weather[
        weather["time"]
        >= last_time - pd.Timedelta(days=3)
    ]

    last_7_days = weather[
        weather["time"]
        >= last_time - pd.Timedelta(days=7)
    ]

    # --------------------------------------------------------
    # CREATE FEATURES
    # --------------------------------------------------------

    features = {

        "latitude":
            latitude,

        "longitude":
            longitude,

        "rainfall":
            target_day[
                "precipitation"
            ].sum(),

        "rainfall_3day":
            last_3_days[
                "precipitation"
            ].sum(),

        "rainfall_7day":
            last_7_days[
                "precipitation"
            ].sum(),

        "max_hourly_rain":
            target_day[
                "precipitation"
            ].max(),

        "avg_temperature":
            target_day[
                "temperature_2m"
            ].mean(),

        "max_temperature":
            target_day[
                "temperature_2m"
            ].max(),

        "min_temperature":
            target_day[
                "temperature_2m"
            ].min(),

        "avg_humidity":
            target_day[
                "relative_humidity_2m"
            ].mean(),

        "avg_pressure":
            target_day[
                "pressure_msl"
            ].mean(),

        "min_pressure":
            target_day[
                "pressure_msl"
            ].min(),

        "avg_soil_moisture_0_7":
            target_day[
                "soil_moisture_0_to_7cm"
            ].mean(),

        "avg_soil_moisture_7_28":
            target_day[
                "soil_moisture_7_to_28cm"
            ].mean(),

        "avg_soil_moisture_28_100":
            target_day[
                "soil_moisture_28_to_100cm"
            ].mean()
    }

    return features


# ============================================================
# CALCULATE ENVIRONMENTAL RISK SCORE
# ============================================================

def calculate_risk_score(

    model_probability,

    rainfall,

    rainfall_3day,

    rainfall_7day,

    humidity,

    soil_0_7,

    soil_7_28,

    soil_28_100
):

    # --------------------------------------------------------
    # RAINFALL
    # --------------------------------------------------------

    daily_score = min(
        rainfall / 25.0,
        1.0
    )

    three_day_score = min(
        rainfall_3day / 100.0,
        1.0
    )

    seven_day_score = min(
        rainfall_7day / 150.0,
        1.0
    )

    rainfall_score = (

        daily_score * 0.20

        + three_day_score * 0.30

        + seven_day_score * 0.50
    )


    # --------------------------------------------------------
    # SOIL MOISTURE
    # --------------------------------------------------------

    soil_average = (

        soil_0_7

        + soil_7_28

        + soil_28_100

    ) / 3.0

    soil_score = min(
        soil_average / 0.50,
        1.0
    )


    # --------------------------------------------------------
    # HUMIDITY
    # --------------------------------------------------------

    humidity_score = min(

        max(
            (humidity - 50.0) / 50.0,
            0.0
        ),

        1.0
    )


    # --------------------------------------------------------
    # ENVIRONMENTAL SCORE
    # --------------------------------------------------------

    environmental_score = (

        rainfall_score * 0.60

        + soil_score * 0.25

        + humidity_score * 0.15
    )


    # --------------------------------------------------------
    # COMBINE MODEL + ENVIRONMENT
    # --------------------------------------------------------

    combined_score = (

        environmental_score * 0.75

        + model_probability * 0.25
    )


    # --------------------------------------------------------
    # CONVERT TO PERCENTAGE
    # --------------------------------------------------------

    risk_score = combined_score * 100.0


    # --------------------------------------------------------
    # LIMIT SCORE
    # --------------------------------------------------------

    risk_score = min(
        risk_score,
        49.0
    )


    return risk_score


# ============================================================
# RISK LEVEL
# ============================================================

def get_risk_level(score):

    if score >= 35:

        return "HIGH"

    elif score >= 20:

        return "MEDIUM"

    else:

        return "LOW"


# ============================================================
# GET MODEL PROBABILITY
# ============================================================

def get_positive_probability(probabilities):

    """
    Get probability of the positive/landslide class.

    For normal binary models with classes [0, 1],
    this returns probability of class 1.

    If the model uses another class representation,
    try to identify the positive class safely.
    """

    probabilities = list(probabilities)

    # --------------------------------------------------------
    # NORMAL BINARY CLASSIFICATION
    # --------------------------------------------------------

    if hasattr(model, "classes_"):

        classes = list(model.classes_)

        # Prefer class 1
        if 1 in classes:

            index = classes.index(1)

            return float(probabilities[index])

        # Try string "1"
        if "1" in classes:

            index = classes.index("1")

            return float(probabilities[index])

        # Try positive/landslide labels
        positive_labels = [
            "landslide",
            "yes",
            "true",
            "positive",
            "high"
        ]

        for label in positive_labels:

            for index, current_class in enumerate(classes):

                if str(current_class).lower() == label:

                    return float(
                        probabilities[index]
                    )

    # --------------------------------------------------------
    # FALLBACK
    # --------------------------------------------------------

    if len(probabilities) >= 2:

        return float(probabilities[1])

    return float(probabilities[0])


# ============================================================
# MAIN BACKEND FUNCTION
# ============================================================

def predict_landslide(city):

    # --------------------------------------------------------
    # LOCATION
    # --------------------------------------------------------

    location = get_coordinates(city)

    if location is None:

        raise ValueError(
            "City not found"
        )


    # --------------------------------------------------------
    # WEATHER
    # --------------------------------------------------------

    weather = get_weather(

        location["latitude"],

        location["longitude"]
    )


    # --------------------------------------------------------
    # FEATURES
    # --------------------------------------------------------

    feature_values = create_features(

        weather,

        location["latitude"],

        location["longitude"]
    )


    # --------------------------------------------------------
    # CREATE MODEL INPUT
    # --------------------------------------------------------

    input_data = pd.DataFrame(

        [[
            feature_values[feature]
            for feature in FEATURES
        ]],

        columns=FEATURES
    )


    # --------------------------------------------------------
    # ML PREDICTION
    # --------------------------------------------------------

    prediction_raw = model.predict(
        input_data
    )[0]


    # --------------------------------------------------------
    # CONVERT NUMPY VALUE TO NORMAL PYTHON VALUE
    # --------------------------------------------------------

    try:
        prediction = prediction_raw.item()
    except AttributeError:
        prediction = prediction_raw


    # --------------------------------------------------------
    # MODEL PROBABILITY
    # --------------------------------------------------------

    if hasattr(model, "predict_proba"):

        probabilities = model.predict_proba(
            input_data
        )[0]

        model_probability = get_positive_probability(
            probabilities
        )

    else:

        raise ValueError(
            "Landslide model does not support probability prediction."
        )


    # --------------------------------------------------------
    # ENSURE VALID PROBABILITY
    # --------------------------------------------------------

    model_probability = max(
        0.0,
        min(
            float(model_probability),
            1.0
        )
    )


    # --------------------------------------------------------
    # ENVIRONMENTAL RISK SCORE
    # --------------------------------------------------------

    risk_score = calculate_risk_score(

        model_probability,

        feature_values["rainfall"],

        feature_values["rainfall_3day"],

        feature_values["rainfall_7day"],

        feature_values["avg_humidity"],

        feature_values[
            "avg_soil_moisture_0_7"
        ],

        feature_values[
            "avg_soil_moisture_7_28"
        ],

        feature_values[
            "avg_soil_moisture_28_100"
        ]
    )


    # --------------------------------------------------------
    # RISK LEVEL
    # --------------------------------------------------------

    risk_level = get_risk_level(
        risk_score
    )


    # --------------------------------------------------------
    # RETURN COMPLETE BACKEND DATA
    # --------------------------------------------------------

    return {

        # LOCATION
        "city":
            location["city"],

        "country":
            location["country"],

        "latitude":
            location["latitude"],

        "longitude":
            location["longitude"],


        # ML PREDICTION
        "prediction":
            prediction,


        # ML PROBABILITY
        "ml_probability":
            round(
                model_probability,
                4
            ),


        # FINAL RISK SCORE
        "risk_score":
            round(
                float(risk_score),
                2
            ),


        # RISK LEVEL
        "risk_level":
            risk_level

    }