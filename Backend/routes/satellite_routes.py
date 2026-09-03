from flask import Blueprint, jsonify
from pathlib import Path
from datetime import datetime, timezone
import json


satellite_bp = Blueprint(
    "satellite",
    __name__
)


# ============================================================
# FIND SATELLITE OUTPUT DIRECTORY
# ============================================================

ROOT_DIR = Path(__file__).resolve().parents[2]

SATELLITE_DIR = ROOT_DIR / "Satellite"

# Original project sometimes uses "sattelite_model"
# while some versions use "satellite_model".
SATTELITE_MODEL_DIR = SATELLITE_DIR / "sattelite_model"
SATELLITE_MODEL_DIR = SATELLITE_DIR / "satellite_model"


if SATTELITE_MODEL_DIR.exists():
    MODEL_DIR = SATTELITE_MODEL_DIR
else:
    MODEL_DIR = SATELLITE_MODEL_DIR


OUTPUT_DIR = MODEL_DIR / "outputs"


# ============================================================
# JSON HELPER
# ============================================================

def load_json(filename):

    path = OUTPUT_DIR / filename

    if not path.exists():
        return None

    try:

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except Exception as error:

        print(
            f"[SATELLITE] Error reading {path}: {error}"
        )

        return None


# ============================================================
# SATELLITE SERVICE HEALTH
# ============================================================

@satellite_bp.route(
    "/api/satellite/health",
    methods=["GET"]
)
def satellite_health():

    return jsonify({

        "status": "ok",

        "service":
            "Satellite Monitoring",

        "backend":
            "connected",

        "output_directory":
            str(OUTPUT_DIR),

        "output_directory_exists":
            OUTPUT_DIR.exists(),

        "timestamp":
            datetime.now(
                timezone.utc
            ).isoformat()

    })


# ============================================================
# SATELLITE STATUS
# ============================================================

@satellite_bp.route(
    "/api/satellite",
    methods=["GET"]
)
def satellite_status():

    live_state = load_json(
        "live_monitor_state.json"
    )

    if live_state is None:

        live_state = load_json(
            "live_monitor.json"
        )

    return jsonify({

        "available":
            True,

        "service":
            "Satellite Monitoring",

        "live_data":
            live_state is not None,

        "monitor":
            live_state or {},

        "timestamp":
            datetime.now(
                timezone.utc
            ).isoformat()

    })


# ============================================================
# LANDSLIDE DATA
# ============================================================

@satellite_bp.route(
    "/api/landslide",
    methods=["GET"]
)
def get_landslide():

    # Prefer latest live prediction
    data = load_json(
        "latest_live_landslide.json"
    )

    # Fallback to prediction results
    if not data:

        data = load_json(
            "prediction_results.json"
        )

    if not data:

        data = load_json(
            "landslide_prediction_results.json"
        )


    # No data available
    if not data:

        return jsonify({

            "available":
                False,

            "live_data":
                False,

            "disaster":
                "LANDSLIDE",

            "alert":
                False,

            "risk":
                "UNKNOWN",

            "maximum_probability":
                0,

            "affected_pixels":
                0,

            "affected_area_percent":
                0,

            "coordinate_count":
                0,

            "coordinates":
                [],

            "affected_regions":
                []

        })


    # ========================================================
    # NORMALIZE REGIONS
    # ========================================================

    affected_regions = data.get(
        "affected_regions",
        []
    )

    coordinates = []


    for region in affected_regions:

        probability = (
            region.get(
                "max_probability"
            )
            or
            region.get(
                "probability",
                0
            )
        )

        coordinates.append({

            "region_id":
                region.get(
                    "region_id"
                ),

            "latitude":
                region.get(
                    "latitude"
                ),

            "longitude":
                region.get(
                    "longitude"
                ),

            "probability":
                probability,

            "affected_pixels":
                region.get(
                    "affected_pixels",
                    0
                ),

            "risk":
                (
                    "HIGH"
                    if probability > 0.8
                    else "MEDIUM"
                )

        })


    return jsonify({

        "available":
            True,

        "live_data":
            True,

        "disaster":
            "LANDSLIDE",

        "country":
            "India",

        "alert":
            data.get(
                "alert",
                True
            ),

        "risk":
            data.get(
                "risk",
                "HIGH"
            ),

        "maximum_probability":
            data.get(
                "maximum_probability",
                0
            ),

        "affected_pixels":
            data.get(
                "affected_pixels",
                0
            ),

        "affected_area_percent":
            data.get(
                "affected_area_percent",
                0
            ),

        "coordinate_count":
            len(coordinates),

        "coordinates":
            coordinates,

        "affected_regions":
            affected_regions,

        "timestamp":
            data.get(
                "timestamp",
                datetime.now(
                    timezone.utc
                ).isoformat()
            )

    })


# ============================================================
# FLOOD DATA
# ============================================================

@satellite_bp.route(
    "/api/flood",
    methods=["GET"]
)
def get_flood():

    data = load_json(
        "latest_live_flood.json"
    )

    if not data:

        data = load_json(
            "flood_prediction_results.json"
        )


    if not data:

        return jsonify({

            "available":
                False,

            "live_data":
                False,

            "disaster":
                "FLOOD",

            "alert":
                False,

            "risk":
                "UNKNOWN",

            "maximum_mndwi":
                0,

            "total_flood_pixels":
                0,

            "detected_regions":
                0,

            "coordinates":
                []

        })


    coordinates = data.get(
        "coordinates",
        []
    )


    return jsonify({

        "available":
            True,

        "live_data":
            True,

        "disaster":
            "FLOOD",

        "country":
            data.get(
                "country",
                "Nepal"
            ),

        "alert":
            data.get(
                "alert",
                True
            ),

        "risk":
            data.get(
                "risk",
                "HIGH"
            ),

        "maximum_mndwi":
            data.get(
                "maximum_mndwi",
                0
            ),

        "total_flood_pixels":
            data.get(
                "total_flood_pixels",
                0
            ),

        "detected_regions":
            data.get(
                "detected_regions",
                len(coordinates)
            ),

        "coordinates":
            coordinates,

        "timestamp":
            data.get(
                "timestamp",
                datetime.now(
                    timezone.utc
                ).isoformat()
            )

    })


# ============================================================
# LANDSLIDE GEOJSON
# ============================================================

@satellite_bp.route(
    "/api/landslide/geojson",
    methods=["GET"]
)
def landslide_geojson():

    data = load_json(
        "landslide_regions.geojson"
    )

    if not data:

        return jsonify({

            "type":
                "FeatureCollection",

            "features":
                []

        })


    return jsonify(data)


# ============================================================
# FLOOD GEOJSON
# ============================================================

@satellite_bp.route(
    "/api/flood/geojson",
    methods=["GET"]
)
def flood_geojson():

    data = load_json(
        "flood_regions.geojson"
    )

    if not data:

        return jsonify({

            "type":
                "FeatureCollection",

            "features":
                []

        })


    return jsonify(data)


# ============================================================
# COMBINED GEOJSON
# ============================================================

@satellite_bp.route(
    "/api/geojson",
    methods=["GET"]
)
def combined_geojson():

    landslide = load_json(
        "landslide_regions.geojson"
    )

    flood = load_json(
        "flood_regions.geojson"
    )


    landslide = (
        landslide
        if landslide
        else {
            "features": []
        }
    )

    flood = (
        flood
        if flood
        else {
            "features": []
        }
    )


    return jsonify({

        "type":
            "FeatureCollection",

        "features":
            landslide.get(
                "features",
                []
            )
            +
            flood.get(
                "features",
                []
            )

    })


# ============================================================
# ALL DISASTERS
# ============================================================

@satellite_bp.route(
    "/api/disasters",
    methods=["GET"]
)
def all_disasters():

    landslide = load_json(
        "prediction_results.json"
    )

    flood = load_json(
        "flood_prediction_results.json"
    )


    return jsonify({

        "timestamp":
            (
                landslide or {}
            ).get(
                "timestamp"
            )
            or
            (
                flood or {}
            ).get(
                "timestamp"
            ),

        "landslides":
            landslide or {},

        "floods":
            flood or {}

    })


# ============================================================
# ALERTS
# ============================================================

@satellite_bp.route(
    "/api/alerts",
    methods=["GET"]
)
def get_alerts():

    alerts = load_json(
        "alerts.json"
    )


    if not isinstance(
        alerts,
        list
    ):

        alerts = []


    return jsonify({

        "count":
            len(alerts),

        "live_data":
            True,

        "alerts":
            alerts

    })