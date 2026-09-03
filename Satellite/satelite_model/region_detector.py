from pathlib import Path
import json

import numpy as np
import rasterio
from rasterio.transform import Affine


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

METADATA_FILE = (
    BASE_DIR.parent
    / "data"
    / "satellite"
    / "metadata"
    / "scene_metadata.json"
)


# ============================================================
# COUNTRY BOUNDARIES
# Approximate bounding boxes
# Used for regional classification.
# ============================================================

REGIONS = {

    "India": {
        "lat_min": 6.0,
        "lat_max": 37.5,
        "lon_min": 68.0,
        "lon_max": 97.5
    },

    "Pakistan": {
        "lat_min": 23.5,
        "lat_max": 37.5,
        "lon_min": 60.0,
        "lon_max": 77.5
    },

    "China": {
        "lat_min": 18.0,
        "lat_max": 53.5,
        "lon_min": 73.0,
        "lon_max": 135.0
    },

    "Nepal": {
        "lat_min": 26.3,
        "lat_max": 30.5,
        "lon_min": 80.0,
        "lon_max": 88.3
    },

    "Bhutan": {
        "lat_min": 26.5,
        "lat_max": 28.4,
        "lon_min": 88.7,
        "lon_max": 92.2
    },

    "Bangladesh": {
        "lat_min": 20.5,
        "lat_max": 26.7,
        "lon_min": 88.0,
        "lon_max": 92.7
    },

    "Myanmar": {
        "lat_min": 9.5,
        "lat_max": 28.5,
        "lon_min": 92.0,
        "lon_max": 101.5
    },

    "Afghanistan": {
        "lat_min": 29.0,
        "lat_max": 38.5,
        "lon_min": 60.5,
        "lon_max": 74.9
    },

    "Sri Lanka": {
        "lat_min": 5.8,
        "lat_max": 9.9,
        "lon_min": 79.5,
        "lon_max": 82.2
    }
}


# ============================================================
# LOAD SCENE
# ============================================================

def load_scene():

    if not METADATA_FILE.exists():

        return None

    try:

        with open(
            METADATA_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except Exception:

        return None


# ============================================================
# REGION FROM COORDINATES
# ============================================================

def identify_region(
    latitude,
    longitude
):

    for country, bounds in REGIONS.items():

        if (
            bounds["lat_min"]
            <= latitude
            <= bounds["lat_max"]
            and
            bounds["lon_min"]
            <= longitude
            <= bounds["lon_max"]
        ):

            return country

    return "Outside monitored region"


# ============================================================
# DETECT LOCATION
# ============================================================

def get_scene_location():

    scene = load_scene()

    if scene is None:

        return {

            "country":
                "Unknown",

            "latitude":
                None,

            "longitude":
                None,

            "location_source":
                "unavailable"

        }

    center = scene.get(
        "center",
        {}
    )

    latitude = center.get(
        "latitude"
    )

    longitude = center.get(
        "longitude"
    )

    if latitude is None or longitude is None:

        return {

            "country":
                "Unknown",

            "latitude":
                None,

            "longitude":
                None,

            "location_source":
                "scene metadata unavailable"

        }

    country = identify_region(
        latitude,
        longitude
    )

    return {

        "country":
            country,

        "latitude":
            latitude,

        "longitude":
            longitude,

        "location_source":
            "Sentinel-2 scene center",

        "product_name":
            scene.get(
                "product_name"
            )

    }


# ============================================================
# DETECT HIGH-RISK PIXEL LOCATION
# ============================================================

def get_detected_location(
    probability_map,
    threshold=0.5
):

    scene = load_scene()

    if scene is None:

        return get_scene_location()

    transform_data = scene.get(
        "transform"
    )

    crs_string = scene.get(
        "crs"
    )

    if not transform_data or not crs_string:

        return get_scene_location()

    transform = Affine(
        *transform_data
    )

    mask = (
        probability_map >= threshold
    )

    ys, xs = np.where(mask)

    if len(xs) == 0:

        return get_scene_location()

    # --------------------------------------------------------
    # Use average detected-pixel position
    # --------------------------------------------------------

    mean_y = float(
        np.mean(ys)
    )

    mean_x = float(
        np.mean(xs)
    )

    x, y = rasterio.transform.xy(
        transform,
        mean_y,
        mean_x,
        offset="center"
    )

    # --------------------------------------------------------
    # Convert to WGS84
    # --------------------------------------------------------

    try:

        from rasterio.warp import transform as warp_transform

        lon, lat = warp_transform(
            crs_string,
            "EPSG:4326",
            [x],
            [y]
        )

        longitude = float(
            lon[0]
        )

        latitude = float(
            lat[0]
        )

    except Exception:

        return get_scene_location()

    country = identify_region(
        latitude,
        longitude
    )

    return {

        "country":
            country,

        "latitude":
            latitude,

        "longitude":
            longitude,

        "location_source":
            "high-probability pixels",

        "detected_pixels":
            int(len(xs)),

        "product_name":
            scene.get(
                "product_name"
            )

    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    location = get_scene_location()

    print(
        json.dumps(
            location,
            indent=4
        )
    )