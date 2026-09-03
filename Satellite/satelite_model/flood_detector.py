import os
import json
import glob
from datetime import datetime, timezone

import numpy as np
import rasterio

from rasterio.features import shapes
from rasterio.warp import (
    reproject,
    transform_geom,
    transform as coordinate_transform
)
from rasterio.enums import Resampling

from shapely.geometry import shape
from scipy import ndimage


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

PRODUCTS_DIR = os.path.abspath(
    os.path.join(
        BASE_DIR,
        "..",
        "data",
        "satellite",
        "products"
    )
)

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "outputs"
)

HISTORY_DIR = os.path.join(
    OUTPUT_DIR,
    "history"
)

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)

os.makedirs(
    HISTORY_DIR,
    exist_ok=True
)


# ============================================================
# FLOOD CONFIG
# ============================================================

MNDWI_THRESHOLD = 0.25

MIN_REGION_PIXELS = 25

MIN_DETECTION_PROBABILITY = 0.35

# This is deliberately NOT used to decide
# whether a whole country is flooded.
MIN_FLOOD_PIXELS = 500


# ============================================================
# MONITORING COUNTRIES
# ============================================================

MONITORED_COUNTRIES = [
    "India",
    "Nepal",
    "Bhutan",
    "Bangladesh",
    "Pakistan",
    "Sri Lanka",
    "Myanmar"
]


# ============================================================
# PRODUCT SEARCH
# ============================================================

def find_all_sentinel1_products():

    matches = glob.glob(
        os.path.join(
            PRODUCTS_DIR,
            "**",
            "*.SAFE"
        ),
        recursive=True
    )

    products = []

    for product in matches:

        name = os.path.basename(
            product
        ).upper()

        if name.startswith("S1"):

            products.append(
                product
            )

    products.sort(
        key=os.path.getmtime,
        reverse=True
    )

    return products

    
def find_all_products():

    print()
    print("=" * 70)
    print("SEARCHING ALL SENTINEL-2 PRODUCTS")
    print("=" * 70)

    print()
    print("Search directory:")
    print(PRODUCTS_DIR)

    if not os.path.exists(PRODUCTS_DIR):

        raise FileNotFoundError(
            f"\nProduct directory not found:\n"
            f"{PRODUCTS_DIR}"
        )

    matches = glob.glob(
        os.path.join(
            PRODUCTS_DIR,
            "**",
            "*.SAFE"
        ),
        recursive=True
    )

    products = []

    for path in matches:

        if os.path.isdir(path):

            products.append(
                os.path.abspath(path)
            )

    products = list(
        dict.fromkeys(products)
    )

    products.sort()

    if not products:

        raise FileNotFoundError(
            "\n"
            "No Sentinel-2 SAFE products found.\n\n"
            f"Searched:\n{PRODUCTS_DIR}\n"
        )

    print()
    print(
        "Products found:",
        len(products)
    )

    for i, product in enumerate(
        products,
        start=1
    ):

        print(
            f"  {i}. {product}"
        )

    return products


# ============================================================
# FIND BAND
# ============================================================

def find_band(
    product,
    band
):

    patterns = [

        os.path.join(
            product,
            "**",
            f"*_{band}_*.jp2"
        ),

        os.path.join(
            product,
            "**",
            f"*{band}*.jp2"
        )
    ]

    matches = []

    for pattern in patterns:

        matches.extend(
            glob.glob(
                pattern,
                recursive=True
            )
        )

    matches = list(
        dict.fromkeys(matches)
    )

    if not matches:

        raise FileNotFoundError(
            f"{band} not found in:\n{product}"
        )

    return matches[0]


# ============================================================
# REFLECTANCE NORMALIZATION
# ============================================================

def normalize_reflectance(
    data
):

    data = data.astype(
        np.float32
    )

    finite = np.isfinite(
        data
    )

    if not np.any(finite):

        return np.zeros_like(
            data,
            dtype=np.float32
        )

    maximum = np.nanmax(
        data
    )

    if maximum > 2.0:

        data = data / 10000.0

    return data


# ============================================================
# RESAMPLE BAND
# ============================================================

def read_resampled_band(
    path,
    reference_shape,
    reference_transform,
    reference_crs
):

    destination = np.zeros(
        reference_shape,
        dtype=np.float32
    )

    with rasterio.open(
        path
    ) as src:

        reproject(

            source=rasterio.band(
                src,
                1
            ),

            destination=destination,

            src_transform=src.transform,

            src_crs=src.crs,

            dst_transform=reference_transform,

            dst_crs=reference_crs,

            resampling=Resampling.bilinear
        )

    return destination


# ============================================================
# REMOVE SMALL REGIONS
# ============================================================

def clean_mask(
    mask
):

    labels, count = ndimage.label(
        mask
    )

    if count == 0:

        return mask

    sizes = np.bincount(
        labels.ravel()
    )

    output = np.zeros_like(
        mask,
        dtype=bool
    )

    for label_id in range(
        1,
        count + 1
    ):

        if (
            sizes[label_id]
            >= MIN_REGION_PIXELS
        ):

            output[
                labels == label_id
            ] = True

    return output


# ============================================================
# GEOJSON FOR ONE PRODUCT
# ============================================================

def generate_geojson(
    mask,
    probability,
    transform,
    crs,
    product_name
):

    features = []

    labels, number = ndimage.label(
        mask
    )

    for region_id in range(
        1,
        number + 1
    ):

        region_mask = (
            labels == region_id
        )

        pixel_count = int(
            np.sum(
                region_mask
            )
        )

        if pixel_count < MIN_REGION_PIXELS:

            continue

        region_probability = float(
            np.max(
                probability[
                    region_mask
                ]
            )
        )

        if (
            region_probability
            < MIN_DETECTION_PROBABILITY
        ):

            continue

        polygon_shapes = shapes(
            region_mask.astype(
                np.uint8
            ),
            mask=region_mask,
            transform=transform
        )

        for geom, value in polygon_shapes:

            if value != 1:

                continue

            if geom is None:

                continue

            try:

                polygon = shape(
                    geom
                )

            except Exception:

                continue

            if polygon.is_empty:

                continue

            try:

                geo_geom = transform_geom(
                    crs,
                    "EPSG:4326",
                    geom
                )

            except Exception:

                continue

            try:

                centroid = polygon.centroid

                longitude_values, latitude_values = (
                    coordinate_transform(
                        crs,
                        "EPSG:4326",
                        [centroid.x],
                        [centroid.y]
                    )
                )

                longitude = float(
                    longitude_values[0]
                )

                latitude = float(
                    latitude_values[0]
                )

            except Exception:

                continue

            if region_probability >= 0.80:

                risk = "HIGH"

            elif region_probability >= 0.50:

                risk = "MEDIUM"

            else:

                risk = "LOW"

            feature = {

                "type": "Feature",

                "geometry": geo_geom,

                "properties": {

                    "disaster": "flood",

                    "region_id": int(
                        region_id
                    ),

                    "latitude": latitude,

                    "longitude": longitude,

                    "probability":
                        region_probability,

                    "probability_percent":
                        region_probability * 100.0,

                    "risk": risk,

                    "pixels": pixel_count,

                    "product":
                        product_name
                }
            }

            features.append(
                feature
            )

    return features


# ============================================================
# PROCESS ONE SENTINEL PRODUCT
# ============================================================

def process_product(
    product
):

    product_name = os.path.basename(
        product
    )

    print()
    print("=" * 70)
    print(
        "PROCESSING PRODUCT"
    )
    print("=" * 70)

    print()
    print(product_name)

    # --------------------------------------------------------
    # B03
    # --------------------------------------------------------

    b03_path = find_band(
        product,
        "B03"
    )

    # --------------------------------------------------------
    # B11
    # --------------------------------------------------------

    b11_path = find_band(
        product,
        "B11"
    )

    print()
    print(
        "[FOUND] B03:",
        os.path.basename(
            b03_path
        )
    )

    print(
        "[FOUND] B11:",
        os.path.basename(
            b11_path
        )
    )

    # --------------------------------------------------------
    # OPEN B03
    # --------------------------------------------------------

    with rasterio.open(
        b03_path
    ) as src:

        b03 = src.read(
            1
        ).astype(
            np.float32
        )

        reference_shape = b03.shape

        transform = src.transform

        crs = src.crs

        width = src.width

        height = src.height

    print()
    print(
        "Scene:",
        width,
        "x",
        height
    )

    # --------------------------------------------------------
    # RESAMPLE B11
    # --------------------------------------------------------

    b11 = read_resampled_band(

        b11_path,

        reference_shape,

        transform,

        crs
    )

    # --------------------------------------------------------
    # NORMALIZE
    # --------------------------------------------------------

    b03 = normalize_reflectance(
        b03
    )

    b11 = normalize_reflectance(
        b11
    )

    b03 = np.nan_to_num(
        b03,
        nan=0.0,
        posinf=0.0,
        neginf=0.0
    )

    b11 = np.nan_to_num(
        b11,
        nan=0.0,
        posinf=0.0,
        neginf=0.0
    )

    # --------------------------------------------------------
    # MNDWI
    # --------------------------------------------------------

    denominator = (
        b03 + b11
    )

    mndwi = np.zeros_like(
        b03,
        dtype=np.float32
    )

    valid = (
        denominator != 0
    )

    mndwi[valid] = (

        b03[valid]
        -
        b11[valid]

    ) / denominator[valid]

    mndwi = np.nan_to_num(
        mndwi,
        nan=-1.0,
        posinf=-1.0,
        neginf=-1.0
    )

    # --------------------------------------------------------
    # WATER MASK
    # --------------------------------------------------------

    water_mask = (
        mndwi >= MNDWI_THRESHOLD
    )

    water_mask = clean_mask(
        water_mask
    )

    # --------------------------------------------------------
    # PROBABILITY
    # --------------------------------------------------------

    probability = np.clip(

        (
            mndwi
            -
            MNDWI_THRESHOLD
        )

        /

        (
            1.0
            -
            MNDWI_THRESHOLD
        ),

        0.0,
        1.0
    )

    # --------------------------------------------------------
    # STATISTICS
    # --------------------------------------------------------

    total_pixels = int(
        water_mask.size
    )

    flood_pixels = int(
        np.sum(
            water_mask
        )
    )

    flood_percentage = (

        flood_pixels
        /
        total_pixels
        *
        100.0

    )

    maximum_mndwi = float(
        np.max(
            mndwi
        )
    )

    mean_mndwi = float(
        np.mean(
            mndwi
        )
    )

    median_mndwi = float(
        np.median(
            mndwi
        )
    )

    # --------------------------------------------------------
    # GEOJSON
    # --------------------------------------------------------

    features = generate_geojson(

        water_mask,

        probability,

        transform,

        crs,

        product_name
    )

    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

    result = {

        "disaster": "flood",

        "product":
            product_name,

        "product_path":
            product,

        "timestamp":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "scene_width":
            width,

        "scene_height":
            height,

        "flood_pixels":
            flood_pixels,

        "flood_percentage":
            flood_percentage,

        "maximum_mndwi":
            maximum_mndwi,

        "mean_mndwi":
            mean_mndwi,

        "median_mndwi":
            median_mndwi,

        "mndwi_threshold":
            MNDWI_THRESHOLD,

        "detection_count":
            len(features),

        "detections":
            [
                feature[
                    "properties"
                ]

                for feature in features
            ]
    }

    return result, features


# ============================================================
# COMBINE ALL PRODUCTS
# ============================================================

def run_flood_detection():

    print()
    print("=" * 70)
    print("MULTI-REGION FLOOD DETECTION")
    print("=" * 70)

    print()
    print(
        "Monitoring:"
    )

    print(
        ", ".join(
            MONITORED_COUNTRIES
        )
    )

    # --------------------------------------------------------
    # FIND PRODUCTS
    # --------------------------------------------------------

    products = find_all_products()

    all_features = []

    product_results = []

    total_flood_pixels = 0

    maximum_mndwi = -1.0

    # --------------------------------------------------------
    # PROCESS EACH PRODUCT
    # --------------------------------------------------------

    for index, product in enumerate(
        products,
        start=1
    ):

        print()
        print(
            "=" * 70
        )

        print(
            f"PRODUCT {index}/{len(products)}"
        )

        print(
            "=" * 70
        )

        try:

            result, features = (
                process_product(
                    product
                )
            )

            product_results.append(
                result
            )

            all_features.extend(
                features
            )

            total_flood_pixels += (
                result[
                    "flood_pixels"
                ]
            )

            maximum_mndwi = max(
                maximum_mndwi,
                result[
                    "maximum_mndwi"
                ]
            )

        except Exception as error:

            print()
            print(
                "PRODUCT FAILED:"
            )

            print(
                product
            )

            print(
                "Reason:",
                error
            )

    # --------------------------------------------------------
    # GLOBAL STATISTICS
    # --------------------------------------------------------

    total_scene_pixels = sum(
        result[
            "scene_width"
        ]
        *
        result[
            "scene_height"
        ]

        for result
        in product_results
    )

    if total_scene_pixels > 0:

        total_flood_percentage = (

            total_flood_pixels
            /
            total_scene_pixels
            *
            100.0
        )

    else:

        total_flood_percentage = 0.0

    # --------------------------------------------------------
    # ALERT LOGIC
    # --------------------------------------------------------

    high_regions = [

        feature

        for feature
        in all_features

        if feature[
            "properties"
        ][
            "risk"
        ] == "HIGH"
    ]

    medium_regions = [

        feature

        for feature
        in all_features

        if feature[
            "properties"
        ][
            "risk"
        ] == "MEDIUM"
    ]

    if len(high_regions) > 0:

        risk = "HIGH"

        alert = True

    elif len(medium_regions) > 0:

        risk = "MEDIUM"

        alert = True

    elif total_flood_pixels >= MIN_FLOOD_PIXELS:

        risk = "LOW"

        alert = False

    else:

        risk = "LOW"

        alert = False

    # --------------------------------------------------------
    # GEOJSON
    # --------------------------------------------------------

    geojson = {

        "type":
            "FeatureCollection",

        "features":
            all_features
    }

    geojson_path = os.path.join(
        OUTPUT_DIR,
        "flood_regions.geojson"
    )

    with open(
        geojson_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            geojson,
            file,
            indent=2
        )

    # --------------------------------------------------------
    # FINAL RESULT
    # --------------------------------------------------------

    timestamp = datetime.now(
        timezone.utc
    ).isoformat()

    result = {

        "service":
            "Multi-Region Flood Detection",

        "disaster":
            "flood",

        "timestamp":
            timestamp,

        "monitoring_countries":
            MONITORED_COUNTRIES,

        "products_found":
            len(products),

        "products_processed":
            len(product_results),

        "risk":
            risk,

        "alert":
            alert,

        "flood_pixels":
            total_flood_pixels,

        "flood_percentage":
            total_flood_percentage,

        "maximum_mndwi":
            maximum_mndwi,

        "detection_count":
            len(all_features),

        "high_risk_regions":
            len(high_regions),

        "medium_risk_regions":
            len(medium_regions),

        "detections":

            [
                feature[
                    "properties"
                ]

                for feature
                in all_features
            ],

        "products":
            product_results,

        "geojson":
            geojson_path
    }

    # --------------------------------------------------------
    # CURRENT JSON
    # --------------------------------------------------------

    result_path = os.path.join(
        OUTPUT_DIR,
        "flood_prediction_results.json"
    )

    with open(
        result_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            result,
            file,
            indent=2
        )

    # --------------------------------------------------------
    # HISTORY
    # --------------------------------------------------------

    history_filename = (

        datetime.now(
            timezone.utc
        ).strftime(
            "%Y%m%d_%H%M%S"
        )

        +

        "_flood.json"
    )

    history_path = os.path.join(
        HISTORY_DIR,
        history_filename
    )

    with open(
        history_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            result,
            file,
            indent=2
        )

    # --------------------------------------------------------
    # OUTPUT
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("MULTI-REGION FLOOD DETECTION COMPLETE")
    print("=" * 70)

    print()
    print(
        "Products found:",
        len(products)
    )

    print(
        "Products processed:",
        len(product_results)
    )

    print()
    print(
        "Flood pixels:",
        total_flood_pixels
    )

    print(
        "Flood percentage:",
        f"{total_flood_percentage:.6f}%"
    )

    print(
        "Maximum MNDWI:",
        f"{maximum_mndwi:.6f}"
    )

    print()
    print(
        "Detected regions:",
        len(all_features)
    )

    print(
        "HIGH regions:",
        len(high_regions)
    )

    print(
        "MEDIUM regions:",
        len(medium_regions)
    )

    print()
    print(
        "Risk:",
        risk
    )

    print(
        "Alert:",
        alert
    )

    # --------------------------------------------------------
    # COORDINATES
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("GEOGRAPHIC DETECTIONS")
    print("=" * 70)

    for index, feature in enumerate(
        all_features[:100],
        start=1
    ):

        p = feature[
            "properties"
        ]

        print(

            f"{index}. "

            f"{p['latitude']:.6f}, "

            f"{p['longitude']:.6f} | "

            f"{p['probability_percent']:.2f}% | "

            f"{p['risk']}"

        )

    if len(all_features) > 100:

        print(
            f"... {len(all_features) - 100} more"
        )

    # --------------------------------------------------------
    # FILES
    # --------------------------------------------------------

    print()
    print(
        "Results:"
    )

    print(
        result_path
    )

    print()
    print(
        "GeoJSON:"
    )

    print(
        geojson_path
    )

    print()
    print(
        "History:"
    )

    print(
        history_path
    )

    # --------------------------------------------------------
    # ALERT
    # --------------------------------------------------------

    if alert:

        print()
        print("=" * 70)
        print("🚨 FLOOD ALERT")
        print("=" * 70)

        print(
            f"Risk: {risk}"
        )

        print(
            f"Detected regions: "
            f"{len(all_features)}"
        )

        print(
            "Use flood_regions.geojson "
            "to display the affected areas."
        )

        print(
            "=" * 70
        )

    print()
    print("=" * 70)
    print("DONE")
    print("=" * 70)

    return result


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--product",
        required=True
    )

    args = parser.parse_args()

    process_product(
        args.product
    )