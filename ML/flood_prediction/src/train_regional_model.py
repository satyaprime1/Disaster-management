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

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_FILE = BASE_DIR / "data" / "regional_labeled_data.csv"
MODEL_FILE = BASE_DIR / "models" / "regional_flood_model.pkl"

df = pd.read_csv(DATA_FILE)

features = [
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

X = df[features]
y = df["flood"]


X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)


model = RandomForestClassifier(
    n_estimators=300,
    random_state=42,
    class_weight="balanced",
    n_jobs=-1
)

model.fit(X_train, y_train)

predictions = model.predict(X_test)


print("\nRegional Flood Model")
print("====================")

print(f"Training samples: {len(X_train)}")
print(f"Testing samples : {len(X_test)}")

print(f"\nAccuracy : {accuracy_score(y_test, predictions):.4f}")
print(f"Precision: {precision_score(y_test, predictions, zero_division=0):.4f}")
print(f"Recall   : {recall_score(y_test, predictions, zero_division=0):.4f}")
print(f"F1 Score : {f1_score(y_test, predictions, zero_division=0):.4f}")

print("\nClassification Report:")
print(classification_report(
    y_test,
    predictions,
    zero_division=0
))


importance = pd.DataFrame({
    "feature": features,
    "importance": model.feature_importances_
}).sort_values(
    "importance",
    ascending=False
)

print("\nFeature Importance:")
print(importance.to_string(index=False))


joblib.dump(model, MODEL_FILE)

print("\nModel saved to:")
print(MODEL_FILE)