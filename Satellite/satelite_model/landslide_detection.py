import os
import json
import glob
import re
from datetime import datetime, timezone

import numpy as np
import rasterio
from rasterio.features import shapes
from rasterio.warp import transform as warp_transform
from scipy.ndimage import (
    gaussian_filter,
    binary_opening,
    binary_closing,
    label,
)
from shapely.geometry import shape


# ============================================================
# DIRECTORIES
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")

HISTORY_DIR = os.path.join(
    OUTPUT_DIR,
    "landslide_history"
)

BASELINE_DIR = os.path.join(
    OUTPUT_DIR,
    "baselines"
)

GEOJSON_PATH = os.path.join(
    OUTPUT_DIR,
    "landslide_regions.geojson"
)

RESULT_PATH = os.path.join(
    OUTPUT_DIR,
    "landslide_prediction_results.json"
)

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(HISTORY_DIR, exist_ok=True)
os.makedirs(BASELINE_DIR, exist_ok=True)


# ============================================================
# FIND SENTINEL-1 BAND
# ============================================================

def find_band(product_path, polarization):

    polarization = polarization.lower()

    candidates = []

    for pattern in (
        "*.tiff",
        "*.tif",
        "*.jp2",
    ):

        candidates.extend(
            glob.glob(
                os.path.join(
                    product_path,
                    "**",
                    pattern,
                ),
                recursive=True,
            )
        )

    for file in candidates:

        name = os.path.basename(file).lower()

        if (
            f"-{polarization}-" in name
            or f"-{polarization}." in name
            or f"_{polarization}_" in name
            or f"_{polarization}." in name
            or name.endswith(f"-{polarization}")
            or name.endswith(f"_{polarization}")
        ):
            return file

    return None


# ============================================================
# READ SAR
# ============================================================

def read_sar(path):

    with rasterio.open(path) as src:

        data = src.read(1).astype(np.float32)

        transform = src.transform
        crs = src.crs

        height = src.height
        width = src.width

    data = np.where(
        np.isfinite(data),
        data,
        np.nan,
    )

    data[data <= 0] = np.nan

    return (
        data,
        transform,
        crs,
        height,
        width,
    )


# ============================================================
# CONVERT TO dB
# ============================================================

def to_db(data):

    return (
        10.0
        * np.log10(
            np.maximum(data, 1e-8)
        )
    )


# ============================================================
# RESIZE
# ============================================================

def resize_array(
    array,
    height,
    width,
):

    from scipy.ndimage import zoom

    zoom_y = height / array.shape[0]
    zoom_x = width / array.shape[1]

    result = zoom(
        array,
        (zoom_y, zoom_x),
        order=1,
    )

    return result[:height, :width]


# ============================================================
# GET SENTINEL-1 TRACK
# ============================================================

def baseline_key(product_name):

    """
    Sentinel-1 product example:

    S1D_IW_GRDH_1SDV_20260827T234812_20260827T234832_004318_007F6B_A893.SAFE

    We use:

        satellite + acquisition mode + relative orbit

    so that observations from the same Sentinel-1 track
    can be compared.
    """

    name = os.path.basename(
        product_name.rstrip("\\/")
    )

    parts = name.split("_")

    satellite = parts[0] if parts else "S1"

    mode = "IW"

    if "EW" in parts:
        mode = "EW"
    elif "SM" in parts:
        mode = "SM"
    elif "WV" in parts:
        mode = "WV"

    orbit = "unknown"

    # Sentinel-1 relative orbit is normally
    # the six-digit value before the product datatake ID.
    for i, part in enumerate(parts):

        if (
            part.isdigit()
            and len(part) == 6
        ):

            orbit = part
            break

    return (
        f"{satellite}_{mode}_ORBIT_{orbit}"
    )


# ============================================================
# BASELINE PATH
# ============================================================

def baseline_path(key):

    safe_key = re.sub(
        r"[^A-Za-z0-9_.-]",
        "_",
        key,
    )

    return os.path.join(
        BASELINE_DIR,
        safe_key + ".npz",
    )


# ============================================================
# SAVE BASELINE
# ============================================================

def save_baseline(
    key,
    vv,
    vh,
    product_name,
    sensing_time,
):

    path = baseline_path(key)

    np.savez_compressed(
        path,
        vv=vv.astype(np.float32),
        vh=vh.astype(np.float32),
        product=np.array(
            product_name
        ),
        sensing_time=np.array(
            sensing_time or ""
        ),
    )

    return path


# ============================================================
# LOAD BASELINE
# ============================================================

def load_baseline(key):

    path = baseline_path(key)

    if not os.path.exists(path):
        return None

    try:

        data = np.load(
            path,
            allow_pickle=False,
        )

        return {
            "vv": data["vv"],
            "vh": data["vh"],
            "product": (
                str(data["product"])
                if "product" in data
                else ""
            ),
            "sensing_time": (
                str(data["sensing_time"])
                if "sensing_time" in data
                else ""
            ),
        }

    except Exception as e:

        print(
            f"WARNING: Could not load baseline: {e}"
        )

        return None


# ============================================================
# EXTRACT SENSING TIME
# ============================================================

def extract_sensing_time(product_name):

    match = re.search(
        r"_(\d{8}T\d{6})_",
        product_name,
    )

    if not match:
        return None

    value = match.group(1)

    try:

        dt = datetime.strptime(
            value,
            "%Y%m%dT%H%M%S",
        )

        dt = dt.replace(
            tzinfo=timezone.utc
        )

        return dt.isoformat()

    except Exception:

        return None


# ============================================================
# PIXEL -> LAT/LON
# ============================================================

def pixel_to_lonlat(
    transform,
    row,
    col,
    crs,
):

    x, y = rasterio.transform.xy(
        transform,
        row,
        col,
    )

    try:

        lon, lat = warp_transform(
            crs,
            "EPSG:4326",
            [x],
            [y],
        )

        return (
            float(lon[0]),
            float(lat[0]),
        )

    except Exception:

        return (
            float(x),
            float(y),
        )


# ============================================================
# DETECT REGIONS
# ============================================================

def generate_regions(
    change_mask,
    transform,
    crs,
    risk,
):

    regions = []

    labeled, count = label(
        change_mask
    )

    for region_id in range(
        1,
        count + 1,
    ):

        region_mask = (
            labeled == region_id
        )

        pixels = int(
            np.sum(region_mask)
        )

        if pixels < 100:
            continue

        rows, cols = np.where(
            region_mask
        )

        if len(rows) == 0:
            continue

        center_row = int(
            np.mean(rows)
        )

        center_col = int(
            np.mean(cols)
        )

        lon, lat = pixel_to_lonlat(
            transform,
            center_row,
            center_col,
            crs,
        )

        regions.append(
            {
                "type": "LANDSLIDE_CANDIDATE",
                "latitude": lat,
                "longitude": lon,
                "change_pixels": pixels,
                "risk": risk,
            }
        )

    return regions


# ============================================================
# GEOJSON
# ============================================================

def save_geojson(
    change_mask,
    transform,
    crs,
    risk,
):

    features = []

    for geom, value in shapes(
        change_mask.astype(
            np.uint8
        ),
        mask=change_mask,
        transform=transform,
    ):

        if value != 1:
            continue

        polygon = shape(geom)

        if polygon.area <= 0:
            continue

        try:

            from rasterio.warp import transform_geom

            geo = transform_geom(
                crs,
                "EPSG:4326",
                geom,
            )

        except Exception:

            geo = geom

        polygon_geo = shape(geo)

        centroid = (
            polygon_geo.centroid
        )

        features.append(
            {
                "type": "Feature",
                "geometry": geo,
                "properties": {
                    "disaster": "LANDSLIDE",
                    "risk": risk,
                    "latitude": float(
                        centroid.y
                    ),
                    "longitude": float(
                        centroid.x
                    ),
                },
            }
        )

    geojson = {
        "type": "FeatureCollection",
        "features": features,
    }

    with open(
        GEOJSON_PATH,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            geojson,
            f,
            indent=2,
        )

    return features


# ============================================================
# SAVE RESULT + HISTORY
# ============================================================

def save_result(result):

    with open(
        RESULT_PATH,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            result,
            f,
            indent=2,
        )

    timestamp = datetime.now(
        timezone.utc
    ).strftime(
        "%Y%m%d_%H%M%S"
    )

    history_file = os.path.join(
        HISTORY_DIR,
        f"{timestamp}_landslide.json",
    )

    with open(
        history_file,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            result,
            f,
            indent=2,
        )


# ============================================================
# MAIN LANDSLIDE DETECTOR
# ============================================================

def detect_landslide(
    product_path,
    sensing_time=None,
):

    product_name = os.path.basename(
        product_path.rstrip("\\/")
    )

    print()
    print("=" * 70)
    print("LANDSLIDE DETECTION ON LIVE DATA")
    print("=" * 70)

    print(
        "EXACT PRODUCT:"
    )

    print(product_path)

    # --------------------------------------------------------
    # FIND VV
    # --------------------------------------------------------

    vv_path = find_band(
        product_path,
        "vv",
    )

    # --------------------------------------------------------
    # FIND VH
    # --------------------------------------------------------

    vh_path = find_band(
        product_path,
        "vh",
    )

    print()

    print(
        f"[FOUND] VV: "
        f"{vv_path if vv_path else 'NOT FOUND'}"
    )

    print(
        f"[FOUND] VH: "
        f"{vh_path if vh_path else 'NOT FOUND'}"
    )

    if not vv_path:

        raise RuntimeError(
            "Sentinel-1 VV band not found."
        )

    # --------------------------------------------------------
    # READ VV
    # --------------------------------------------------------

    vv, transform, crs, h, w = read_sar(
        vv_path
    )

    # --------------------------------------------------------
    # READ VH
    # --------------------------------------------------------

    if vh_path:

        vh, _, _, vh_h, vh_w = read_sar(
            vh_path
        )

        if (
            vh.shape[0] != h
            or vh.shape[1] != w
        ):

            vh = resize_array(
                vh,
                h,
                w,
            )

    else:

        vh = np.copy(vv)

    print()

    print(
        f"Scene: {w} x {h}"
    )

    # --------------------------------------------------------
    # CONVERT TO dB
    # --------------------------------------------------------

    vv_db = to_db(vv)
    vh_db = to_db(vh)

    # --------------------------------------------------------
    # SMOOTH
    # --------------------------------------------------------

    vv_smooth = gaussian_filter(
        np.nan_to_num(
            vv_db,
            nan=-30,
        ),
        sigma=2,
    )

    vh_smooth = gaussian_filter(
        np.nan_to_num(
            vh_db,
            nan=-30,
        ),
        sigma=2,
    )

    # --------------------------------------------------------
    # BASELINE
    # --------------------------------------------------------

    key = baseline_key(
        product_name
    )

    print()

    print(
        f"Baseline track: {key}"
    )

    baseline = load_baseline(
        key
    )

    # --------------------------------------------------------
    # FIRST SCENE
    # --------------------------------------------------------

    if baseline is None:

        print()
        print(
            "No historical Sentinel-1 "
            "baseline available for this track."
        )

        print(
            "Creating baseline."
        )

        target_size = 512

        small_vv = resize_array(
            vv_smooth,
            target_size,
            target_size,
        )

        small_vh = resize_array(
            vh_smooth,
            target_size,
            target_size,
        )

        save_baseline(
            key,
            small_vv,
            small_vh,
            product_name,
            sensing_time
            or extract_sensing_time(
                product_name
            ),
        )

        result = {

            "disaster":
                "landslide",

            "alert":
                False,

            "risk":
                "LOW",

            "reason":
                "Baseline created; "
                "waiting for a comparable "
                "Sentinel-1 observation.",

            "product":
                product_name,

            "satellite":
                "Sentinel-1 GRD",

            "sensor":
                "Sentinel-1",

            "baseline_key":
                key,

            "coordinates":
                [],

            "detected_regions":
                0,

            "timestamp":
                datetime.now(
                    timezone.utc
                ).isoformat(),
        }

        save_result(
            result
        )

        print()
        print(
            "=" * 70
        )

        print(
            "BASELINE CREATED"
        )

        print(
            "Risk: LOW"
        )

        print(
            "Alert: False"
        )

        print(
            "=" * 70
        )

        return result

    # --------------------------------------------------------
    # LOAD BASELINE
    # --------------------------------------------------------

    baseline_vv = baseline["vv"]
    baseline_vh = baseline["vh"]

    baseline_vv = resize_array(
        baseline_vv,
        h,
        w,
    )

    baseline_vh = resize_array(
        baseline_vh,
        h,
        w,
    )

    # --------------------------------------------------------
    # CHANGE DETECTION
    # --------------------------------------------------------

    vv_change = np.abs(
        vv_smooth
        - baseline_vv
    )

    vh_change = np.abs(
        vh_smooth
        - baseline_vh
    )

    combined_change = (
        0.6 * vv_change
        +
        0.4 * vh_change
    )

    valid = np.isfinite(
        combined_change
    )

    if not np.any(valid):

        raise RuntimeError(
            "No valid SAR pixels."
        )

    values = combined_change[
        valid
    ]

    p95 = np.percentile(
        values,
        95,
    )

    p99 = np.percentile(
        values,
        99,
    )

    # Conservative adaptive threshold
    threshold = max(
        3.0,
        float(p99),
    )

    print()

    print(
        f"P95 change: {p95:.4f} dB"
    )

    print(
        f"P99 change: {p99:.4f} dB"
    )

    print(
        f"Detection threshold: "
        f"{threshold:.4f} dB"
    )

    change_mask = (
        combined_change
        >= threshold
    )

    # --------------------------------------------------------
    # CLEAN MASK
    # --------------------------------------------------------

    change_mask = binary_opening(
        change_mask,
        structure=np.ones(
            (3, 3),
            dtype=bool,
        ),
    )

    change_mask = binary_closing(
        change_mask,
        structure=np.ones(
            (5, 5),
            dtype=bool,
        ),
    )

    # --------------------------------------------------------
    # REMOVE SMALL REGIONS
    # --------------------------------------------------------

    labeled, count = label(
        change_mask
    )

    cleaned = np.zeros_like(
        change_mask,
        dtype=bool,
    )

    minimum_pixels = 100

    for region_id in range(
        1,
        count + 1,
    ):

        region = (
            labeled == region_id
        )

        pixels = int(
            np.sum(region)
        )

        if pixels >= minimum_pixels:

            cleaned |= region

    change_mask = cleaned

    # --------------------------------------------------------
    # AREA
    # --------------------------------------------------------

    change_pixels = int(
        np.sum(change_mask)
    )

    total_pixels = int(
        np.sum(valid)
    )

    change_percentage = (
        change_pixels
        /
        max(
            total_pixels,
            1,
        )
    ) * 100.0

    # --------------------------------------------------------
    # TEMPORARY REGION COUNT
    # --------------------------------------------------------

    raw_regions = []

    labeled, count = label(
        change_mask
    )

    for region_id in range(
        1,
        count + 1,
    ):

        region = (
            labeled == region_id
        )

        pixels = int(
            np.sum(region)
        )

        if pixels < minimum_pixels:
            continue

        raw_regions.append(
            pixels
        )

    # --------------------------------------------------------
    # RISK
    # --------------------------------------------------------

    if (
        change_percentage >= 1.0
        and len(raw_regions) >= 5
    ):

        risk = "HIGH"

    elif (
        change_percentage >= 0.2
        and len(raw_regions) >= 1
    ):

        risk = "MEDIUM"

    else:

        risk = "LOW"

    alert = (
        risk in
        ("HIGH", "MEDIUM")
    )

    # --------------------------------------------------------
    # GEO REGIONS
    # --------------------------------------------------------

    regions = generate_regions(
        change_mask,
        transform,
        crs,
        risk,
    )

    # --------------------------------------------------------
    # GEOJSON
    # --------------------------------------------------------

    features = save_geojson(
        change_mask,
        transform,
        crs,
        risk,
    )

    # --------------------------------------------------------
    # UPDATE BASELINE
    # --------------------------------------------------------

    small_vv = resize_array(
        vv_smooth,
        512,
        512,
    )

    small_vh = resize_array(
        vh_smooth,
        512,
        512,
    )

    save_baseline(
        key,
        small_vv,
        small_vh,
        product_name,
        sensing_time
        or extract_sensing_time(
            product_name
        ),
    )

    # --------------------------------------------------------
    # COORDINATES
    # --------------------------------------------------------

    coordinates = []

    for region in regions:

        coordinates.append(
            {
                "latitude":
                    region["latitude"],

                "longitude":
                    region["longitude"],

                "risk":
                    risk,

                "type":
                    "LANDSLIDE",
            }
        )

    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

    result = {

        "disaster":
            "landslide",

        "alert":
            bool(alert),

        "risk":
            risk,

        "satellite":
            "Sentinel-1 GRD",

        "sensor":
            "Sentinel-1",

        "product":
            product_name,

        "sensing_time":
            sensing_time
            or extract_sensing_time(
                product_name
            ),

        "baseline_key":
            key,

        "baseline_product":
            baseline.get(
                "product",
                "",
            ),

        "changed_pixels":
            change_pixels,

        "change_percentage":
            float(
                change_percentage
            ),

        "threshold_db":
            float(
                threshold
            ),

        "detected_regions":
            len(features),

        "coordinates":
            coordinates,

        "geojson":
            GEOJSON_PATH,

        "timestamp":
            datetime.now(
                timezone.utc
            ).isoformat(),
    }

    save_result(
        result
    )

    # --------------------------------------------------------
    # PRINT RESULT
    # --------------------------------------------------------

    print()

    print(
        "=" * 70
    )

    print(
        "LANDSLIDE LIVE RESULT"
    )

    print(
        "=" * 70
    )

    print(
        f"Product: {product_name}"
    )

    print(
        f"Satellite sensing time: "
        f"{result['sensing_time']}"
    )

    print()

    print(
        f"Changed pixels: "
        f"{change_pixels}"
    )

    print(
        f"Change percentage: "
        f"{change_percentage:.6f}%"
    )

    print(
        f"Detected regions: "
        f"{len(features)}"
    )

    print(
        f"Risk: {risk}"
    )

    print(
        f"Alert: {alert}"
    )

    if coordinates:

        print()

        print(
            "DETECTED COORDINATES"
        )

        for index, coord in enumerate(
            coordinates,
            start=1,
        ):

            print(
                f"{index}. "
                f"{coord['latitude']:.6f}, "
                f"{coord['longitude']:.6f}"
            )

    if alert:

        print()

        print(
            "=" * 70
        )

        print(
            "🚨 LANDSLIDE ALERT"
        )

        print(
            f"Risk: {risk}"
        )

        print(
            f"Coordinates: "
            f"{len(coordinates)}"
        )

        print(
            "=" * 70
        )

    else:

        print()

        print(
            "No landslide detected."
        )

    return result


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(
        description=
        "Sentinel-1 Landslide Detector"
    )

    parser.add_argument(
        "--product",
        required=True,
        help=
        "Path to Sentinel-1 .SAFE product",
    )

    parser.add_argument(
        "--sensing-time",
        required=False,
        default=None,
        help=
        "Satellite sensing time in ISO format",
    )

    args = parser.parse_args()

    detect_landslide(
        args.product,
        args.sensing_time,
    )