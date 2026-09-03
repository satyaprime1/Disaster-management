import pandas as pd
import joblib

from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_FILE = BASE_DIR / "data" / "landslide_final_data.csv"
MODEL_FILE = BASE_DIR / "models" / "landslide_model.pkl"


# ============================================================
# FEATURES
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
# LOAD DATA
# ============================================================

print("=" * 60)
print("NEW LANDSLIDE MODEL")
print("=" * 60)

df = pd.read_csv(DATA_FILE)

print("\nDataset shape:")
print(df.shape)


# ============================================================
# CLEAN DATA
# ============================================================

df = df.dropna(
    subset=FEATURES + ["landslide"]
).reset_index(drop=True)


X = df[FEATURES]
y = df["landslide"]


print("\nClass distribution:")
print(y.value_counts())


# ============================================================
# TRAIN / TEST SPLIT
# ============================================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)


print("\nTraining samples:", len(X_train))
print("Testing samples :", len(X_test))


# ============================================================
# RANDOM FOREST
# ============================================================

model = RandomForestClassifier(
    n_estimators=500,
    max_depth=8,
    min_samples_leaf=5,
    min_samples_split=10,
    max_features="sqrt",
    class_weight="balanced",
    random_state=42,
    n_jobs=-1
)


print("\nTraining new Random Forest...")

model.fit(
    X_train,
    y_train
)


# ============================================================
# TEST
# ============================================================

predictions = model.predict(X_test)

probabilities = model.predict_proba(X_test)[:, 1]


# ============================================================
# METRICS
# ============================================================

accuracy = accuracy_score(
    y_test,
    predictions
)

precision = precision_score(
    y_test,
    predictions,
    zero_division=0
)

recall = recall_score(
    y_test,
    predictions,
    zero_division=0
)

f1 = f1_score(
    y_test,
    predictions,
    zero_division=0
)


print("\n")
print("=" * 60)
print("NEW LANDSLIDE MODEL RESULTS")
print("=" * 60)

print(f"Accuracy : {accuracy:.4f}")
print(f"Precision: {precision:.4f}")
print(f"Recall   : {recall:.4f}")
print(f"F1 Score : {f1:.4f}")


# ============================================================
# CLASSIFICATION REPORT
# ============================================================

print("\nClassification Report:")

print(
    classification_report(
        y_test,
        predictions,
        zero_division=0
    )
)


# ============================================================
# FEATURE IMPORTANCE
# ============================================================

importance = pd.DataFrame({

    "feature": FEATURES,

    "importance":
        model.feature_importances_

})


importance = importance.sort_values(
    "importance",
    ascending=False
)


print("\nFeature Importance:")

print(
    importance.to_string(
        index=False
    )
)


# ============================================================
# PROBABILITY RANGE
# ============================================================

print("\nProbability range on test data:")

print(
    f"Minimum: {probabilities.min() * 100:.2f}%"
)

print(
    f"Maximum: {probabilities.max() * 100:.2f}%"
)

print(
    f"Average : {probabilities.mean() * 100:.2f}%"
)


# ============================================================
# SAVE MODEL
# ============================================================

MODEL_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)


joblib.dump(
    model,
    MODEL_FILE
)


print("\nModel saved to:")

print(MODEL_FILE)

print("=" * 60)