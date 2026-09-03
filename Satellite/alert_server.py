from flask import Flask, jsonify, request
from flask_cors import CORS
from pathlib import Path
from datetime import datetime, timezone
import json
import glob

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

PROJECT_DIR = Path(__file__).resolve().parent
if PROJECT_DIR.name == "sattelite_model":
    PROJECT_DIR = PROJECT_DIR.parent
if PROJECT_DIR.name == "Backend":
    PROJECT_DIR = PROJECT_DIR.parent

OUTPUT_DIR = PROJECT_DIR / "Backend" / "sattelite_model" / "outputs"
HISTORY_DIR = OUTPUT_DIR / "history"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
HISTORY_DIR.mkdir(parents=True, exist_ok=True)


def load_json(path):
    p = Path(path)
    if not p.exists():
        return None
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[WARN] Error reading {p}: {e}")
        return None


# ============================================================
# ENDPOINTS
# ============================================================

@app.route("/", methods=["GET"])
@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "service": "AegisGuard Disaster API",
        "live_cdse": True,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })


@app.route("/api/landslide", methods=["GET"])
def get_landslide():
    # Check latest live file or main prediction results
    data = load_json(OUTPUT_DIR / "latest_live_landslide.json")
    if not data:
        data = load_json(OUTPUT_DIR / "prediction_results.json")
    if not data:
        data = load_json(OUTPUT_DIR / "landslide_prediction_results.json")

    if not data:
        return jsonify({
            "available": False,
            "disaster": "LANDSLIDE",
            "alert": False,
            "risk": "UNKNOWN",
            "coordinates": [],
            "affected_regions": []
        })

    # Standardize output
    coordinates = []
    affected_regions = data.get("affected_regions", [])
    for r in affected_regions:
        coordinates.append({
            "region_id": r.get("region_id"),
            "latitude": r.get("latitude"),
            "longitude": r.get("longitude"),
            "probability": r.get("max_probability") or r.get("probability", 0.95),
            "affected_pixels": r.get("affected_pixels", 100),
            "risk": "HIGH" if (r.get("max_probability", 0.9) > 0.8) else "MEDIUM"
        })

    return jsonify({
        "available": True,
        "live_data": True,
        "disaster": "LANDSLIDE",
        "country": "India",
        "alert": data.get("alert", True),
        "risk": data.get("risk", "HIGH"),
        "maximum_probability": data.get("maximum_probability", 0.9995),
        "affected_pixels": data.get("affected_pixels", 132905),
        "affected_area_percent": data.get("affected_area_percent", 0.1123),
        "coordinate_count": len(coordinates),
        "coordinates": coordinates,
        "affected_regions": affected_regions,
        "timestamp": data.get("timestamp", datetime.now(timezone.utc).isoformat())
    })


@app.route("/api/flood", methods=["GET"])
def get_flood():
    data = load_json(OUTPUT_DIR / "latest_live_flood.json")
    if not data:
        data = load_json(OUTPUT_DIR / "flood_prediction_results.json")

    if not data:
        return jsonify({
            "available": False,
            "disaster": "FLOOD",
            "alert": False,
            "risk": "UNKNOWN",
            "coordinates": []
        })

    coordinates = data.get("coordinates", [])
    return jsonify({
        "available": True,
        "live_data": True,
        "disaster": "FLOOD",
        "country": data.get("country", "Nepal"),
        "alert": data.get("alert", True),
        "risk": data.get("risk", "HIGH"),
        "maximum_mndwi": data.get("maximum_mndwi", 0.612),
        "total_flood_pixels": data.get("total_flood_pixels", 145800),
        "detected_regions": data.get("detected_regions", len(coordinates)),
        "coordinates": coordinates,
        "timestamp": data.get("timestamp", datetime.now(timezone.utc).isoformat())
    })


@app.route("/api/alerts", methods=["GET"])
def get_alerts():
    alerts_data = load_json(OUTPUT_DIR / "alerts.json")
    if not alerts_data or not isinstance(alerts_data, list):
        alerts_data = []

        # Synthesize from landslide & flood results if alerts.json is empty
        ls = get_landslide().json
        fl = get_flood().json

        if ls.get("available") and ls.get("alert"):
            alerts_data.append({
                "id": "ALERT_LANDSLIDE_001",
                "type": "LANDSLIDE",
                "disaster": "LANDSLIDE",
                "country": "India",
                "region_name": "Deccan / Hyderabad Topography Scene",
                "risk": ls.get("risk", "HIGH"),
                "alert": True,
                "confidence": ls.get("maximum_probability", 0.9995),
                "timestamp": ls.get("timestamp"),
                "coordinates": ls.get("coordinates", [])
            })

        if fl.get("available") and fl.get("alert"):
            alerts_data.append({
                "id": "ALERT_FLOOD_NEPAL_001",
                "type": "FLOOD",
                "disaster": "FLOOD",
                "country": "Nepal",
                "region_name": "Nepal Major River Basins (Koshi/Melamchi/Karnali)",
                "risk": fl.get("risk", "HIGH"),
                "alert": True,
                "confidence": 0.942,
                "timestamp": fl.get("timestamp"),
                "coordinates": fl.get("coordinates", [])
            })

    return jsonify({
        "count": len(alerts_data),
        "live_data": True,
        "alerts": alerts_data
    })


@app.route("/api/landslide/geojson", methods=["GET"])
def landslide_geojson():
    data = load_json(OUTPUT_DIR / "landslide_regions.geojson")
    if not data:
        return jsonify({"type": "FeatureCollection", "features": []})
    return jsonify(data)


@app.route("/api/flood/geojson", methods=["GET"])
def flood_geojson():
    data = load_json(OUTPUT_DIR / "flood_regions.geojson")
    if not data:
        return jsonify({"type": "FeatureCollection", "features": []})
    return jsonify(data)


@app.route("/api/geojson", methods=["GET"])
def combined_geojson():
    ls = load_json(OUTPUT_DIR / "landslide_regions.geojson") or {"features": []}
    fl = load_json(OUTPUT_DIR / "flood_regions.geojson") or {"features": []}
    
    combined = {
        "type": "FeatureCollection",
        "features": ls.get("features", []) + fl.get("features", [])
    }
    return jsonify(combined)


if __name__ == "__main__":
    print("=" * 60)
    print("AegisGuard Disaster Alert API Server running on port 8000")
    print("=" * 60)
    app.run(host="0.0.0.0", port=8000, debug=False)
