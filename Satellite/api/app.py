import os
import json

from flask import (
    Flask,
    jsonify,
    send_file
)

from flask_cors import CORS


BASE_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(
            os.path.abspath(__file__)
        ),
        "..",
        "sattelite_model"
    )
)

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "outputs"
)


app = Flask(
    __name__
)

CORS(
    app
)


# ============================================================
# JSON HELPER
# ============================================================

def load_json(
    filename
):

    path = os.path.join(
        OUTPUT_DIR,
        filename
    )

    if not os.path.exists(
        path
    ):

        return {}

    try:

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(
                file
            )

    except Exception as error:

        return {

            "error":
                str(error)
        }


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():

    return jsonify({

        "service":
            "Disaster Management API",

        "status":
            "online",

        "coverage": [

            "India",
            "Nepal",
            "Bhutan",
            "Bangladesh",
            "Pakistan",
            "Sri Lanka",
            "Myanmar"
        ],

        "monitor_interval_minutes":
            15
    })


# ============================================================
# LIVE SATELLITE STATUS
# ============================================================

@app.route(
    "/api/satellite"
)
def satellite():

    return jsonify(
        load_json(
            "live_monitor.json"
        )
    )


# ============================================================
# LANDSLIDE
# ============================================================

@app.route(
    "/api/landslides"
)
def landslides():

    return jsonify(
        load_json(
            "prediction_results.json"
        )
    )


# ============================================================
# FLOODS
# ============================================================

@app.route(
    "/api/floods"
)
def floods():

    return jsonify(
        load_json(
            "flood_prediction_results.json"
        )
    )


# ============================================================
# FLOOD GEOJSON
# ============================================================

@app.route(
    "/api/geojson/flood"
)
def flood_geojson():

    path = os.path.join(

        OUTPUT_DIR,

        "flood_regions.geojson"
    )

    if not os.path.exists(
        path
    ):

        return jsonify({

            "type":
                "FeatureCollection",

            "features":
                []
        })

    return send_file(
        path,
        mimetype=
            "application/geo+json"
    )


# ============================================================
# LANDSLIDE GEOJSON
# ============================================================

@app.route(
    "/api/geojson/landslide"
)
def landslide_geojson():

    path = os.path.join(

        OUTPUT_DIR,

        "landslide_regions.geojson"
    )

    if not os.path.exists(
        path
    ):

        return jsonify({

            "type":
                "FeatureCollection",

            "features":
                []
        })

    return send_file(
        path,
        mimetype=
            "application/geo+json"
    )


# ============================================================
# ALL DISASTERS
# ============================================================

@app.route(
    "/api/disasters"
)
def disasters():

    landslides = load_json(
        "prediction_results.json"
    )

    floods = load_json(
        "flood_prediction_results.json"
    )

    return jsonify({

        "timestamp":
            landslides.get(
                "timestamp"
            )
            or
            floods.get(
                "timestamp"
            ),

        "landslides":
            landslides,

        "floods":
            floods
    })


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    app.run(

        host="0.0.0.0",

        port=5000,

        debug=False
    )