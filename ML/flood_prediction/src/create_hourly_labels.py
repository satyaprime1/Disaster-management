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

print("Input file:")
print(INPUT_FILE)

if not INPUT_FILE.exists():
    raise FileNotFoundError(
        f"\nRegional weather file not found:\n{INPUT_FILE}"
    )

df = pd.read_csv(INPUT_FILE)

print("Original dataset shape:", df.shape)


# ============================================================
# TIME
# ============================================================

df["time"] = pd.to_datetime(
    df["time"],
    errors="coerce"
)

df = df.dropna(
    subset=["time"]
).copy()


# ============================================================
# SORT
# ============================================================

df = df.sort_values(
    ["district", "time"]
).reset_index(drop=True)


# ============================================================
# HOURLY RAINFALL FEATURES
# ============================================================

print("\nCreating hourly rainfall features...")


# Current-hour rainfall
df["rainfall_1h"] = (
    df.groupby("district")["precipitation"]
    .transform(
        lambda x: x.rolling(
            window=1,
            min_periods=1
        ).sum()
    )
)


# Last 3 hours
df["rainfall_3h"] = (
    df.groupby("district")["precipitation"]
    .transform(
        lambda x: x.rolling(
            window=3,
            min_periods=1
        ).sum()
    )
)


# Last 6 hours
df["rainfall_6h"] = (
    df.groupby("district")["precipitation"]
    .transform(
        lambda x: x.rolling(
            window=6,
            min_periods=1
        ).sum()
    )
)


# Last 24 hours
df["rainfall_24h"] = (
    df.groupby("district")["precipitation"]
    .transform(
        lambda x: x.rolling(
            window=24,
            min_periods=1
        ).sum()
    )
)


# Last 72 hours
df["rainfall_72h"] = (
    df.groupby("district")["precipitation"]
    .transform(
        lambda x: x.rolling(
            window=72,
            min_periods=1
        ).sum()
    )
)


# Last 168 hours = 7 days
df["rainfall_168h"] = (
    df.groupby("district")["precipitation"]
    .transform(
        lambda x: x.rolling(
            window=168,
            min_periods=1
        ).sum()
    )
)


# ============================================================
# MAXIMUM RAINFALL FEATURES
# ============================================================

df["max_rainfall_6h"] = (
    df.groupby("district")["precipitation"]
    .transform(
        lambda x: x.rolling(
            window=6,
            min_periods=1
        ).max()
    )
)


df["max_rainfall_24h"] = (
    df.groupby("district")["precipitation"]
    .transform(
        lambda x: x.rolling(
            window=24,
            min_periods=1
        ).max()
    )
)


# ============================================================
# SELECT FINAL FEATURES
# ============================================================

hourly = df[
    [
        "district",
        "state",
        "time",

        "rainfall_1h",
        "rainfall_3h",
        "rainfall_6h",
        "rainfall_24h",
        "rainfall_72h",
        "rainfall_168h",

        "max_rainfall_6h",
        "max_rainfall_24h",

        "temperature",
        "humidity",
        "pressure",

        "soil_moisture_0_7",
        "soil_moisture_7_28",
        "soil_moisture_28_100",
    ]
].copy()


# ============================================================
# CREATE DATA DIRECTORY
# ============================================================

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# SAVE
# ============================================================

print("\nSaving hourly feature dataset...")

hourly.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# VERIFY FILE
# ============================================================

if not OUTPUT_FILE.exists():

    raise RuntimeError(
        "\nCSV was not created!"
    )


# ============================================================
# INFORMATION
# ============================================================

print("\n")
print("=" * 40)
print("HOURLY FEATURES CREATED")
print("=" * 40)

print("\nDataset shape:")
print(hourly.shape)

print("\nRegions:")
print(hourly["district"].nunique())

print("\nTime range:")

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

for column in hourly.columns:
    print(" -", column)

print("\nSaved to:")

print(OUTPUT_FILE)

print("\nFile size:")

print(
    f"{OUTPUT_FILE.stat().st_size / (1024 * 1024):.2f} MB"
)

print("\nVerified: CSV exists.")