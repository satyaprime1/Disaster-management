from flask import Blueprint, request, jsonify

from ML.flood_prediction.src.predict_city import predict_flood
from ML.landslide_prediction.src.predict_city import predict_landslide


prediction_bp = Blueprint("prediction", __name__)


@prediction_bp.route("/predict", methods=["POST"])
def predict():

    # =========================================================
    # GET REQUEST DATA
    # =========================================================

    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "error": "Request body is required"
        }), 400

    city = data.get("city")

    if not city or not isinstance(city, str):
        return jsonify({
            "error": "City is required"
        }), 400

    city = city.strip()

    if not city:
        return jsonify({
            "error": "City cannot be empty"
        }), 400

    # =========================================================
    # RUN FLOOD MODEL
    # =========================================================

    try:

        print(f"\n========== PREDICTION START ==========")
        print(f"City: {city}")

        flood_result = predict_flood(city)

        print("\n---------- FLOOD RESULT ----------")
        print(flood_result)

    except Exception as e:

        print("\n========== FLOOD MODEL ERROR ==========")
        print(type(e).__name__, str(e))

        return jsonify({
            "error": "Flood prediction failed",
            "details": str(e)
        }), 500

    # =========================================================
    # VALIDATE FLOOD RESULT
    # =========================================================

    if not isinstance(flood_result, dict):

        return jsonify({
            "error": "Flood model returned invalid data"
        }), 500

    if "flood" not in flood_result:

        return jsonify({
            "error": "Flood model response missing 'flood'",
            "details": str(flood_result)
        }), 500

    if "location" not in flood_result:

        return jsonify({
            "error": "Flood model response missing 'location'",
            "details": str(flood_result)
        }), 500

    flood_data = flood_result["flood"]

    # =========================================================
    # VALIDATE FLOOD KEYS
    # =========================================================

    required_flood_keys = [
        "prediction",
        "probability",
        "risk"
    ]

    missing_flood_keys = [
        key for key in required_flood_keys
        if key not in flood_data
    ]

    if missing_flood_keys:

        return jsonify({
            "error": "Flood model response is incomplete",
            "missing_keys": missing_flood_keys,
            "flood_result": flood_data
        }), 500

    flood_risk = str(
        flood_data["risk"]
    ).upper()

    # =========================================================
    # RUN LANDSLIDE MODEL
    # =========================================================

    try:

        landslide_result = predict_landslide(city)

        print("\n---------- LANDSLIDE RESULT ----------")
        print(landslide_result)

    except Exception as e:

        print("\n========== LANDSLIDE MODEL ERROR ==========")
        print(type(e).__name__, str(e))

        return jsonify({
            "error": "Landslide prediction failed",
            "details": str(e)
        }), 500

    # =========================================================
    # VALIDATE LANDSLIDE RESULT
    # =========================================================

    if not isinstance(landslide_result, dict):

        return jsonify({
            "error": "Landslide model returned invalid data"
        }), 500

    print("\n---------- LANDSLIDE KEYS ----------")
    print(list(landslide_result.keys()))

    # =========================================================
    # LANDSLIDE DATA
    # =========================================================

    # Do NOT blindly use:
    #
    # landslide_result["prediction"]
    #
    # because this was likely causing your KeyError.
    #
    # First check what the model actually returned.

    landslide_prediction = landslide_result.get(
        "prediction"
    )

    landslide_probability = landslide_result.get(
        "ml_probability"
    )

    landslide_risk_score = landslide_result.get(
        "risk_score"
    )

    landslide_risk = landslide_result.get(
        "risk_level"
    )

    # =========================================================
    # VALIDATE LANDSLIDE FIELDS
    # =========================================================

    missing_landslide_keys = []

    if landslide_prediction is None:
        missing_landslide_keys.append("prediction")

    if landslide_probability is None:
        missing_landslide_keys.append("ml_probability")

    if landslide_risk_score is None:
        missing_landslide_keys.append("risk_score")

    if landslide_risk is None:
        missing_landslide_keys.append("risk_level")

    if missing_landslide_keys:

        print("\n========== LANDSLIDE RESPONSE MISMATCH ==========")
        print("Missing:", missing_landslide_keys)
        print("Received:", landslide_result)

        return jsonify({
            "error": "Landslide model response is incomplete",
            "missing_keys": missing_landslide_keys,
            "received_keys": list(
                landslide_result.keys()
            ),
            "landslide_result": landslide_result
        }), 500

    # =========================================================
    # NORMALIZE LANDSLIDE OUTPUT
    # =========================================================

    landslide_data = {

        "prediction": landslide_prediction,

        "probability": landslide_probability,

        "risk": str(
            landslide_risk
        ).upper(),

        "risk_score": landslide_risk_score

    }

    # =========================================================
    # OVERALL RISK
    # =========================================================

    risk_order = {

        "LOW": 1,

        "LOW-MEDIUM": 2,

        "MEDIUM": 3,

        "MEDIUM-HIGH": 4,

        "HIGH": 5

    }

    flood_value = risk_order.get(
        flood_risk,
        0
    )

    landslide_value = risk_order.get(
        landslide_data["risk"],
        0
    )

    highest_risk_value = max(
        flood_value,
        landslide_value
    )

    overall_risk = "LOW"

    for level, value in risk_order.items():

        if value == highest_risk_value:

            overall_risk = level
            break

    # =========================================================
    # ALERTS
    # =========================================================

    alerts = [

        {
            "type": "flood",

            "risk": flood_risk,

            "message":
                f"Flood risk currently "
                f"{flood_risk.lower()}"
        },

        {
            "type": "landslide",

            "risk":
                landslide_data["risk"],

            "message":
                f"Landslide risk currently "
                f"{landslide_data['risk'].lower()}"
        }

    ]

    # =========================================================
    # FINAL RESPONSE
    # =========================================================

    response = {

        # -----------------------------------------------------
        # LOCATION
        # -----------------------------------------------------

        "location":
            flood_result["location"],

        # -----------------------------------------------------
        # OVERALL
        # -----------------------------------------------------

        "overall": {

            "risk":
                overall_risk

        },

        # -----------------------------------------------------
        # FLOOD
        # -----------------------------------------------------

        "flood": {

            "prediction":
                flood_data["prediction"],

            "probability":
                flood_data["probability"],

            "risk":
                flood_data["risk"],

            "weather_records":
                flood_data.get(
                    "weather_records"
                ),

            "prediction_date":
                flood_data.get(
                    "prediction_date"
                )

        },

        # -----------------------------------------------------
        # LANDSLIDE
        # -----------------------------------------------------

        "landslide":
            landslide_data,

        # -----------------------------------------------------
        # SATELLITE
        # -----------------------------------------------------

        "satellite": {

            "status":
                "PENDING"

        },

        # -----------------------------------------------------
        # ENVIRONMENT
        # -----------------------------------------------------

        "environment":
            flood_result.get(
                "environment",
                {}
            ),

        # -----------------------------------------------------
        # LIVE WEATHER
        # -----------------------------------------------------

        "live_weather":
            flood_result.get(
                "live_weather",
                {}
            ),

        # -----------------------------------------------------
        # ALERTS
        # -----------------------------------------------------

        "alerts":
            alerts

    }

    # =========================================================
    # DEBUG OUTPUT
    # =========================================================

    print("\n========== FINAL RESPONSE ==========")
    print(response)

    print("\n========== PREDICTION SUCCESS ==========\n")

    return jsonify(response), 200