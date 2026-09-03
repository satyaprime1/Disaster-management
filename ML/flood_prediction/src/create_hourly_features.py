import pandas as pd
from pathlib import Path

# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "data" / "regional_weather_data.csv"
OUTPUT_FILE = BASE_DIR / "data" / "regional_hourly_features.csv"


# ============================================================
# LOAD DATA
# ============================================================

print("\nLoading regional weather data...")

df = pd.read_csv(INPUT_FILE)

print("Original dataset shape:", df.shape)


# ============================================================
# TIME
# ============================================================

df["time"] = pd.to_datetime(df["time"])

df = df.sort_values(
    ["district", "time"]
).reset_index(drop=True)


# ============================================================
# CHECK REQUIRED COLUMNS
# ============================================================

required_columns = [
    "district",
    "state",
    "time",
    "precipitation",
    "temperature_2m",
    "relative_humidity_2m",
    "pressure_msl",
    "soil_moisture_0_to_7cm",
    "soil_moisture_7_to_28cm",
    "soil_moisture_28_to_100cm",
]

missing = [
    column
    for column in required_columns
    if column not in df.columns
]

if missing:

    raise ValueError(
        f"Missing columns in weather dataset: {missing}"
    )


# ============================================================
# NUMERIC CLEANUP
# ============================================================

numeric_columns = [
    "precipitation",
    "temperature_2m",
    "relative_humidity_2m",
    "pressure_msl",
    "soil_moisture_0_to_7cm",
    "soil_moisture_7_to_28cm",
    "soil_moisture_28_to_100cm",
]

for column in numeric_columns:

    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    )


# ============================================================
# REMOVE INVALID ROWS
# ============================================================

df = df.dropna(
    subset=[
        "district",
        "time"
    ]
).copy()


# ============================================================
# RAINFALL FEATURES
# ============================================================

print("\nCreating hourly rainfall features...")


# Current hourly rainfall

df["rainfall_1h"] = (
    df["precipitation"]
    .fillna(0)
)


# ------------------------------------------------------------
# Rolling rainfall windows
# ------------------------------------------------------------

grouped = df.groupby(
    "district",
    group_keys=False
)


df["rainfall_3h"] = (
    grouped["precipitation"]
    .transform(
        lambda x:
        x.fillna(0)
        .rolling(
            window=3,
            min_periods=1
        )
        .sum()
    )
)


df["rainfall_6h"] = (
    grouped["precipitation"]
    .transform(
        lambda x:
        x.fillna(0)
        .rolling(
            window=6,
            min_periods=1
        )
        .sum()
    )
)


df["rainfall_24h"] = (
    grouped["precipitation"]
    .transform(
        lambda x:
        x.fillna(0)
        .rolling(
            window=24,
            min_periods=1
        )
        .sum()
    )
)


df["rainfall_72h"] = (
    grouped["precipitation"]
    .transform(
        lambda x:
        x.fillna(0)
        .rolling(
            window=72,
            min_periods=1
        )
        .sum()
    )
)


df["rainfall_168h"] = (
    grouped["precipitation"]
    .transform(
        lambda x:
        x.fillna(0)
        .rolling(
            window=168,
            min_periods=1
        )
        .sum()
    )
)


# ============================================================
# MAXIMUM RAINFALL
# ============================================================

df["max_rainfall_6h"] = (
    grouped["precipitation"]
    .transform(
        lambda x:
        x.fillna(0)
        .rolling(
            window=6,
            min_periods=1
        )
        .max()
    )
)


df["max_rainfall_24h"] = (
    grouped["precipitation"]
    .transform(
        lambda x:
        x.fillna(0)
        .rolling(
            window=24,
            min_periods=1
        )
        .max()
    )
)


# ============================================================
# CURRENT WEATHER FEATURES
# ============================================================

df["temperature"] = df["temperature_2m"]

df["humidity"] = df["relative_humidity_2m"]

df["pressure"] = df["pressure_msl"]

df["soil_moisture_0_7"] = (
    df["soil_moisture_0_to_7cm"]
)

df["soil_moisture_7_28"] = (
    df["soil_moisture_7_to_28cm"]
)

df["soil_moisture_28_100"] = (
    df["soil_moisture_28_to_100cm"]
)


# ============================================================
# SELECT FINAL FEATURES
# ============================================================

hourly_features = [

    "district",
    "state",
    "time",

    # Rainfall
    "rainfall_1h",
    "rainfall_3h",
    "rainfall_6h",
    "rainfall_24h",
    "rainfall_72h",
    "rainfall_168h",

    "max_rainfall_6h",
    "max_rainfall_24h",

    # Weather
    "temperature",
    "humidity",
    "pressure",

    # Soil
    "soil_moisture_0_7",
    "soil_moisture_7_28",
    "soil_moisture_28_100",

]


hourly = df[hourly_features].copy()


# ============================================================
# REMOVE INVALID FEATURE ROWS
# ============================================================

hourly = hourly.dropna(
    subset=[
        "rainfall_1h",
        "rainfall_3h",
        "rainfall_6h",
        "rainfall_24h",
        "rainfall_72h",
        "rainfall_168h",
        "temperature",
        "humidity",
        "pressure",
        "soil_moisture_0_7",
        "soil_moisture_7_28",
        "soil_moisture_28_100",
    ]
)


# ============================================================
# SAVE
# ============================================================

hourly.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# INFORMATION
# ============================================================

print("\n========================================")
print("HOURLY FEATURES CREATED")
print("========================================")

print(
    "Dataset shape:",
    hourly.shape
)

print(
    "Regions:",
    hourly["district"].nunique()
)

print(
    "Time range:"
)

print(
    hourly["time"].min(),
    "→",
    hourly["time"].max()
)

print("\nRows per region:")

print(
    hourly.groupby("district").size()
)

print("\nFeatures:")

for feature in hourly_features:

    print(
        " -",
        feature
    )

print("\nSaved to:")

print(
    OUTPUT_FILE
)