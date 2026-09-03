
import os
import sys
import json
import time
import shutil
import zipfile
import tempfile
import traceback
from pathlib import Path
from datetime import datetime, timezone, timedelta

import requests
from dotenv import load_dotenv


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_DIR = Path(r"D:\Disaster-management")

BASE_DIR = (
    PROJECT_DIR
    / "Backend"
    / "sattelite_model"
)

OUTPUT_DIR = BASE_DIR / "outputs"

HISTORY_DIR = (
    OUTPUT_DIR
    / "history"
)

LIVE_DIR = (
    PROJECT_DIR
    / "Backend"
    / "data"
    / "satellite"
    / "live_products"
)

STATE_FILE = (
    OUTPUT_DIR
    / "live_monitor_state.json"
)


OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

HISTORY_DIR.mkdir(
    parents=True,
    exist_ok=True
)

LIVE_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

load_dotenv(
    PROJECT_DIR / ".env"
)

CDSE_USERNAME = os.getenv(
    "CDSE_USERNAME"
)

CDSE_PASSWORD = os.getenv(
    "CDSE_PASSWORD"
)


# ============================================================
# CDSE ENDPOINTS
# ============================================================

IDENTITY_URL = (
    "https://identity.dataspace.copernicus.eu"
    "/auth/realms/CDSE/protocol/openid-connect/token"
)

CATALOGUE_URL = (
    "https://catalogue.dataspace.copernicus.eu"
    "/odata/v1/Products"
)

DOWNLOAD_URL = (
    "https://download.dataspace.copernicus.eu"
    "/odata/v1/Products"
)


# ============================================================
# MONITOR SETTINGS
# ============================================================

CHECK_INTERVAL = 15 * 60

SEARCH_HOURS = 72

MAX_PRODUCTS = 20


# ============================================================
# MONITORED REGION
# ============================================================

WEST = 60.0
SOUTH = 5.0
EAST = 100.0
NORTH = 38.0


REGION_NAME = (
    "Pakistan + India + Nepal + Bhutan + "
    "Bangladesh + Myanmar + Sri Lanka"
)


# ============================================================
# HTTP SESSION
# ============================================================

session = requests.Session()

session.headers.update({
    "User-Agent":
        "Disaster-Management-Live-Monitor/2.0",

    "Accept":
        "application/json"
})


ACCESS_TOKEN = None


# ============================================================
# DETECTOR IMPORTS
# ============================================================

# IMPORTANT:
#
# Actual files:
#
# flood_detector.py
# landslide_detection.py
#
# We import them directly.
#
# NO flood_detection.py
# NO landslide_detector.py
# ============================================================

if str(BASE_DIR) not in sys.path:
    sys.path.insert(
        0,
        str(BASE_DIR)
    )


try:

    import flood_detector

except Exception as error:

    flood_detector = None

    print()
    print(
        "WARNING: flood_detector.py could not be imported."
    )

    print(error)


try:

    import landslide_detection

except Exception as error:

    landslide_detection = None

    print()
    print(
        "WARNING: landslide_detection.py could not be imported."
    )

    print(error)


# ============================================================
# PRINT HELPERS
# ============================================================

def separator():

    print(
        "=" * 70
    )


def title(text):

    print()
    separator()
    print(text)
    separator()


def now_utc():

    return datetime.now(
        timezone.utc
    )


def iso_utc(dt):

    return (
        dt
        .astimezone(timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )


# ============================================================
# AUTHENTICATION
# ============================================================

def authenticate():

    global ACCESS_TOKEN

    if not CDSE_USERNAME:
        raise RuntimeError(
            "CDSE_USERNAME missing from .env"
        )

    if not CDSE_PASSWORD:
        raise RuntimeError(
            "CDSE_PASSWORD missing from .env"
        )

    print(
        "Authenticating with "
        "Copernicus Data Space..."
    )

    response = session.post(
        IDENTITY_URL,

        data={
            "grant_type": "password",
            "client_id": "cdse-public",
            "username": CDSE_USERNAME,
            "password": CDSE_PASSWORD
        },

        timeout=60
    )

    if response.status_code != 200:

        raise RuntimeError(
            "CDSE authentication failed:\n"
            + response.text
        )

    data = response.json()

    ACCESS_TOKEN = data[
        "access_token"
    ]

    session.headers.update({
        "Authorization":
            f"Bearer {ACCESS_TOKEN}"
    })

    print(
        "Authentication successful."
    )


# ============================================================
# STATE
# ============================================================

def load_state():

    if not STATE_FILE.exists():

        return {
            "processed_ids": [],
            "last_check": None
        }

    try:

        with open(
            STATE_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        if not isinstance(data, dict):

            raise ValueError(
                "Invalid state file."
            )

        if "processed_ids" not in data:

            data["processed_ids"] = []

        return data

    except Exception:

        return {
            "processed_ids": [],
            "last_check": None
        }


def save_state(state):

    temporary = STATE_FILE.with_suffix(
        ".tmp"
    )

    with open(
        temporary,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            state,
            file,
            indent=2
        )

    temporary.replace(
        STATE_FILE
    )


# ============================================================
# PRODUCT INFORMATION
# ============================================================

def product_id(product):

    return product.get(
        "Id"
    )


def product_name(product):

    return product.get(
        "Name",
        ""
    )


def sensing_time(product):

    return (
        product
        .get("ContentDate", {})
        .get("Start")
    )


# ============================================================
# GEO FILTER
# ============================================================

def geographic_filter():

    polygon = (
        f"POLYGON(("
        f"{WEST} {SOUTH},"
        f"{EAST} {SOUTH},"
        f"{EAST} {NORTH},"
        f"{WEST} {NORTH},"
        f"{WEST} {SOUTH}"
        f"))"
    )

    return (
        "OData.CSC.Intersects("
        f"area=geography'SRID=4326;"
        f"{polygon}'"
        ")"
    )


# ============================================================
# SEARCH CDSE
# ============================================================

def search_cdse(sensor):

    end = now_utc()

    start = (
        end -
        timedelta(
            hours=SEARCH_HOURS
        )
    )

    start_text = iso_utc(
        start
    )

    end_text = iso_utc(
        end
    )


    # --------------------------------------------------------
    # SENTINEL-2 L2A
    # --------------------------------------------------------

    if sensor == "S2":

        collection = "SENTINEL-2"

        product_type = "S2MSI2A"


    # --------------------------------------------------------
    # SENTINEL-1 GRD
    # --------------------------------------------------------

    elif sensor == "S1":

        collection = "SENTINEL-1"

        product_type = "IW_GRDH_1S"


    else:

        raise ValueError(
            f"Unknown sensor: {sensor}"
        )


    product_filter = (
        f"Collection/Name eq "
        f"'{collection}' "
        "and "
        "Attributes/"
        "OData.CSC.StringAttribute/"
        "any(att:"
        "att/Name eq 'productType' "
        "and "
        "att/OData.CSC.StringAttribute/"
        "Value eq "
        f"'{product_type}'"
        ")"
    )


    time_filter = (
        "ContentDate/Start gt "
        f"{start_text} "
        "and "
        "ContentDate/Start lt "
        f"{end_text}"
    )


    full_filter = (
        product_filter
        + " and "
        + time_filter
        + " and "
        + geographic_filter()
    )


    params = {

        "$filter":
            full_filter,

        "$orderby":
            "ContentDate/Start desc",

        "$top":
            str(MAX_PRODUCTS)
    }


    if sensor == "S2":

        print(
            "Searching Sentinel-2 L2A..."
        )

    else:

        print(
            "Searching Sentinel-1 GRD..."
        )


    try:

        response = session.get(
            CATALOGUE_URL,
            params=params,
            timeout=120
        )


        # ----------------------------------------------------
        # TOKEN EXPIRED
        # ----------------------------------------------------

        if response.status_code == 401:

            print(
                "Authentication expired."
            )

            authenticate()

            response = session.get(
                CATALOGUE_URL,
                params=params,
                timeout=120
            )


        if response.status_code != 200:

            print()
            print(
                "CDSE search failed:"
            )

            print(
                response.status_code
            )

            print(
                response.text[:3000]
            )

            return []


        products = response.json().get(
            "value",
            []
        )


        # ----------------------------------------------------
        # EXTRA PRODUCT VALIDATION
        # ----------------------------------------------------

        if sensor == "S2":

            products = [
                p for p in products
                if "MSIL2A"
                in p.get("Name", "")
            ]

        else:

            products = [
                p for p in products
                if "IW_GRDH_1S"
                in p.get("Name", "")
            ]


        # ----------------------------------------------------
        # SORT NEWEST FIRST
        # ----------------------------------------------------

        products.sort(
            key=lambda p:
                sensing_time(p) or "",
            reverse=True
        )


        print(
            f"Products returned: "
            f"{len(products)}"
        )


        return products


    except Exception as error:

        print()
        print(
            "CDSE search exception:"
        )

        print(error)

        return []


# ============================================================
# SELECT NEWEST PRODUCT
# ============================================================

def select_new_product(
    products,
    state
):

    processed = set(
        state.get(
            "processed_ids",
            []
        )
    )


    for product in products:

        pid = product_id(
            product
        )

        if not pid:
            continue

        if pid in processed:
            continue

        return product


    return None


# ============================================================
# MARK PRODUCT PROCESSED
# ============================================================

def mark_processed(
    product,
    state
):

    pid = product_id(
        product
    )

    if not pid:
        return

    processed = state.setdefault(
        "processed_ids",
        []
    )


    if pid not in processed:

        processed.append(
            pid
        )


    # Keep state reasonably small.

    if len(processed) > 500:

        del processed[:-500]


    state[
        "last_check"
    ] = now_utc().isoformat()


    save_state(
        state
    )


# ============================================================
# DOWNLOAD LIVE PRODUCT
# ============================================================

def download_product(product):

    pid = product_id(
        product
    )

    name = product_name(
        product
    )


    if not pid:

        raise RuntimeError(
            "Product ID missing."
        )


    if not name:

        raise RuntimeError(
            "Product name missing."
        )


    work_dir = Path(
        tempfile.mkdtemp(
            prefix="LIVE_",
            dir=str(LIVE_DIR)
        )
    )


    zip_path = (
        work_dir /
        f"{name}.zip"
    )


    # --------------------------------------------------------
    # CDSE ZIP ENDPOINT
    # --------------------------------------------------------

    url = (
        f"{DOWNLOAD_URL}"
        f"({pid})"
        f"/$zip"
    )


    title(
        "DOWNLOADING LIVE SATELLITE DATA"
    )


    print(
        "Product:"
    )

    print(
        name
    )

    print()

    print(
        "Product ID:"
    )

    print(
        pid
    )

    print()


    catalogue_size = product.get(
        "ContentLength"
    )


    if catalogue_size:

        print(
            f"Catalogue size: "
            f"{catalogue_size / (1024**3):.2f} GB"
        )


    print()


    try:

        response = session.get(
            url,
            stream=True,
            timeout=(60, 300)
        )


        # ----------------------------------------------------
        # TOKEN EXPIRED
        # ----------------------------------------------------

        if response.status_code == 401:

            print(
                "Authentication expired."
            )

            authenticate()

            response.close()

            response = session.get(
                url,
                stream=True,
                timeout=(60, 300)
            )


        if response.status_code != 200:

            body = response.text[
                :2000
            ]

            raise RuntimeError(
                "Product download failed:\n"
                f"HTTP {response.status_code}\n"
                f"{body}"
            )


        # ----------------------------------------------------
        # ACTUAL ZIP SIZE
        # ----------------------------------------------------

        total = int(
            response.headers.get(
                "Content-Length",
                0
            )
            or 0
        )


        downloaded = 0

        last_percent = -1

        last_display_time = 0


        with open(
            zip_path,
            "wb"
        ) as file:

            for chunk in response.iter_content(
                chunk_size=8 * 1024 * 1024
            ):

                if not chunk:
                    continue


                file.write(
                    chunk
                )


                downloaded += len(
                    chunk
                )


                # ------------------------------------------------
                # CLEAN PROGRESS
                # ------------------------------------------------

                if total > 0:

                    percent = int(
                        downloaded
                        * 100
                        / total
                    )

                    current = time.time()


                    if (
                        percent != last_percent
                        and
                        (
                            percent % 5 == 0
                            or
                            current
                            - last_display_time
                            >= 2
                        )
                    ):

                        print(
                            "\rProgress: "
                            f"{percent:3d}% "
                            f"("
                            f"{downloaded / (1024**3):.2f}"
                            "/"
                            f"{total / (1024**3):.2f}"
                            " GB)",
                            end="",
                            flush=True
                        )

                        last_percent = percent

                        last_display_time = (
                            current
                        )


        print()

        print(
            "Download complete."
        )


        # ----------------------------------------------------
        # VERIFY ZIP
        # ----------------------------------------------------

        if not zipfile.is_zipfile(
            zip_path
        ):

            raise RuntimeError(
                "Downloaded file is not "
                "a valid ZIP archive."
            )


        # ----------------------------------------------------
        # EXTRACT
        # ----------------------------------------------------

        title(
            "EXTRACTING LIVE PRODUCT"
        )


        extract_dir = (
            work_dir /
            "extracted"
        )


        extract_dir.mkdir(
            parents=True,
            exist_ok=True
        )


        with zipfile.ZipFile(
            zip_path,
            "r"
        ) as archive:

            archive.extractall(
                extract_dir
            )


        print(
            "Extraction complete."
        )


        # Delete ZIP immediately.

        try:

            zip_path.unlink()

        except Exception:

            pass


        # ----------------------------------------------------
        # FIND EXACT SAFE
        # ----------------------------------------------------

        safe_products = list(
            extract_dir.rglob(
                "*.SAFE"
            )
        )


        if not safe_products:

            raise RuntimeError(
                "No .SAFE product found "
                "inside downloaded archive."
            )


        matching = [
            p for p in safe_products
            if p.name == name
        ]


        if matching:

            safe_path = matching[0]

        else:

            safe_path = safe_products[0]


        title(
            "LIVE PRODUCT READY"
        )


        print(
            "CDSE PRODUCT:"
        )

        print(
            name
        )

        print()

        print(
            "EXACT LIVE SAFE:"
        )

        print(
            safe_path
        )

        print()

        print(
            "[OK] Downloaded product "
            "will be processed directly."
        )


        return (
            safe_path,
            work_dir
        )


    except Exception:

        shutil.rmtree(
            work_dir,
            ignore_errors=True
        )

        raise


# ============================================================
# FLOOD MODEL
# ============================================================

def run_flood_model(
    safe_path,
    product
):

    if flood_detector is None:

        raise RuntimeError(
            "flood_detector.py could "
            "not be imported."
        )


    if not hasattr(
        flood_detector,
        "process_product"
    ):

        raise RuntimeError(
            "flood_detector.py does "
            "not contain process_product()."
        )


    title(
        "LIVE CDSE PRODUCT -> FLOOD MODEL"
    )


    print(
        "This EXACT Sentinel-2 product "
        "will be processed."
    )

    print()

    print(
        safe_path
    )


    # --------------------------------------------------------
    # DIRECT CALL
    #
    # Your actual flood_detector.py:
    #
    # process_product(product)
    #
    # returns:
    #
    # result, features
    # --------------------------------------------------------

    result, features = (
        flood_detector.process_product(
            str(safe_path)
        )
    )


    # --------------------------------------------------------
    # ADD LIVE METADATA
    # --------------------------------------------------------

    result[
        "live"
    ] = True


    result[
        "satellite"
    ] = "Sentinel-2 L2A"


    result[
        "sensor"
    ] = "Sentinel-2"


    result[
        "cdse_product_id"
    ] = product_id(
        product
    )


    result[
        "sensing_time"
    ] = sensing_time(
        product
    )


    result[
        "live_safe_path"
    ] = str(
        safe_path
    )


    # --------------------------------------------------------
    # SAVE FLOOD RESULT
    # --------------------------------------------------------

    result_path = (
        OUTPUT_DIR /
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
            indent=2,
            default=str
        )


    # --------------------------------------------------------
    # SAVE GEOJSON
    # --------------------------------------------------------

    geojson = {
        "type":
            "FeatureCollection",

        "features":
            features
    }


    geojson_path = (
        OUTPUT_DIR /
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
            indent=2,
            default=str
        )


    print()

    print(
        "Flood result saved:"
    )

    print(
        result_path
    )

    print()

    print(
        "Flood GeoJSON saved:"
    )

    print(
        geojson_path
    )


    return result


# ============================================================
# LANDSLIDE MODEL
# ============================================================

def run_landslide_model(
    safe_path,
    product
):

    if landslide_detection is None:

        raise RuntimeError(
            "landslide_detection.py "
            "could not be imported."
        )


    if not hasattr(
        landslide_detection,
        "detect_landslide"
    ):

        raise RuntimeError(
            "landslide_detection.py "
            "does not contain "
            "detect_landslide()."
        )


    title(
        "LIVE CDSE PRODUCT -> LANDSLIDE MODEL"
    )


    print(
        "This EXACT Sentinel-1 product "
        "will be processed."
    )

    print()

    print(
        safe_path
    )


    # --------------------------------------------------------
    # DIRECT CALL
    #
    # Your actual detector:
    #
    # detect_landslide(product_path)
    # --------------------------------------------------------

    result = (
        landslide_detection.detect_landslide(
            str(safe_path)
        )
    )


    if result is None:

        raise RuntimeError(
            "Landslide detector returned "
            "no result."
        )


    # --------------------------------------------------------
    # ADD LIVE METADATA
    # --------------------------------------------------------

    result[
        "live"
    ] = True


    result[
        "satellite"
    ] = "Sentinel-1 GRD"


    result[
        "sensor"
    ] = "Sentinel-1"


    result[
        "cdse_product_id"
    ] = product_id(
        product
    )


    result[
        "sensing_time"
    ] = sensing_time(
        product
    )


    result[
        "live_safe_path"
    ] = str(
        safe_path
    )


    # --------------------------------------------------------
    # SAVE RESULT
    # --------------------------------------------------------

    result_path = (
        OUTPUT_DIR /
        "landslide_prediction_results.json"
    )


    with open(
        result_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            result,
            file,
            indent=2,
            default=str
        )


    print()

    print(
        "Landslide result saved:"
    )

    print(
        result_path
    )


    return result


# ============================================================
# SHOW FLOOD RESULT
# ============================================================

def show_flood_result(
    result,
    product
):

    title(
        "FLOOD LIVE RESULT"
    )


    risk = result.get(
        "risk",
        "UNKNOWN"
    )


    alert = bool(
        result.get(
            "alert",
            False
        )
    )


    print(
        "Product:"
    )

    print(
        product_name(
            product
        )
    )

    print()

    print(
        "Satellite sensing time:"
    )

    print(
        sensing_time(
            product
        )
    )

    print()

    print(
        "Risk:"
    )

    print(
        risk
    )

    print()

    print(
        "Alert:"
    )

    print(
        alert
    )


    if "flood_pixels" in result:

        print()

        print(
            "Flood pixels:"
        )

        print(
            result[
                "flood_pixels"
            ]
        )


    if "flood_percentage" in result:

        print()

        print(
            "Flood percentage:"
        )

        print(
            f"{result['flood_percentage']:.6f}%"
        )


    if "detection_count" in result:

        print()

        print(
            "Detected regions:"
        )

        print(
            result[
                "detection_count"
            ]
        )


    if alert:

        print()

        print(
            "🚨🚨🚨 LIVE FLOOD ALERT 🚨🚨🚨"
        )

        print()

        print(
            f"Risk: {risk}"
        )

        print()

        print(
            "Flood coordinates are "
            "available in flood_regions.geojson."
        )

    else:

        print()

        print(
            "No flood detected."
        )


# ============================================================
# SHOW LANDSLIDE RESULT
# ============================================================

def show_landslide_result(
    result,
    product
):

    title(
        "LANDSLIDE LIVE RESULT"
    )


    risk = result.get(
        "risk",
        "UNKNOWN"
    )


    alert = bool(
        result.get(
            "alert",
            False
        )
    )


    print(
        "Product:"
    )

    print(
        product_name(
            product
        )
    )

    print()

    print(
        "Satellite sensing time:"
    )

    print(
        sensing_time(
            product
        )
    )

    print()

    print(
        "Risk:"
    )

    print(
        risk
    )

    print()

    print(
        "Alert:"
    )

    print(
        alert
    )


    print()

    print(
        "Detected regions:"
    )

    print(
        result.get(
            "detected_regions",
            0
        )
    )


    if "change_percentage" in result:

        print()

        print(
            "Change percentage:"
        )

        print(
            f"{result['change_percentage']:.6f}%"
        )


    if alert:

        print()

        print(
            "🚨🚨🚨 LIVE LANDSLIDE ALERT 🚨🚨🚨"
        )

        print()

        print(
            f"Risk: {risk}"
        )

        print()

        print(
            "Landslide coordinates are "
            "available in landslide_regions.geojson."
        )

    else:

        print()

        print(
            "No landslide detected."
        )


# ============================================================
# SAVE LIVE HISTORY
# ============================================================

def save_history(
    disaster,
    product,
    result
):

    timestamp = now_utc()


    filename = (
        timestamp.strftime(
            "%Y%m%d_%H%M%S"
        )
        + "_"
        + disaster.lower()
        + "_live.json"
    )


    data = {

        "live":
            True,

        "disaster":
            disaster,

        "alert_time":
            timestamp.isoformat(),

        "satellite":
            (
                "Sentinel-2 L2A"
                if disaster == "FLOOD"
                else
                "Sentinel-1 GRD"
            ),

        "sensor":
            (
                "Sentinel-2"
                if disaster == "FLOOD"
                else
                "Sentinel-1"
            ),

        "product":
            product_name(
                product
            ),

        "product_id":
            product_id(
                product
            ),

        "sensing_time":
            sensing_time(
                product
            ),

        "result":
            result
    }


    path = (
        HISTORY_DIR /
        filename
    )


    with open(
        path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=2,
            default=str
        )


    return path


# ============================================================
# PROCESS ONE LIVE PRODUCT
# ============================================================

def process_product(
    sensor,
    product,
    state
):

    disaster = (
        "FLOOD"
        if sensor == "S2"
        else
        "LANDSLIDE"
    )


    title(
        f"NEW {disaster} SATELLITE PRODUCT"
    )


    print(
        "Product:"
    )

    print(
        product_name(
            product
        )
    )

    print()

    print(
        "Product ID:"
    )

    print(
        product_id(
            product
        )
    )

    print()

    print(
        "Sensing time:"
    )

    print(
        sensing_time(
            product
        )
    )


    work_dir = None


    try:

        # ----------------------------------------------------
        # DOWNLOAD
        # ----------------------------------------------------

        safe_path, work_dir = (
            download_product(
                product
            )
        )


        # ----------------------------------------------------
        # VERIFY EXACT LIVE PRODUCT
        # ----------------------------------------------------

        if not safe_path.exists():

            raise RuntimeError(
                "Live SAFE does not exist."
            )


        title(
            "LIVE DATA -> MODEL"
        )


        print(
            "CDSE PRODUCT:"
        )

        print(
            product_name(
                product
            )
        )

        print()

        print(
            "EXACT DOWNLOADED SAFE:"
        )

        print(
            safe_path
        )

        print()

        print(
            "[OK] EXACT LIVE PRODUCT "
            "CONNECTED TO MODEL."
        )


        # ----------------------------------------------------
        # FLOOD
        # ----------------------------------------------------

        if sensor == "S2":

            result = run_flood_model(
                safe_path,
                product
            )


            show_flood_result(
                result,
                product
            )


            history = save_history(
                "FLOOD",
                product,
                result
            )


        # ----------------------------------------------------
        # LANDSLIDE
        # ----------------------------------------------------

        else:

            result = run_landslide_model(
                safe_path,
                product
            )


            show_landslide_result(
                result,
                product
            )


            history = save_history(
                "LANDSLIDE",
                product,
                result
            )


        print()

        print(
            "Live history:"
        )

        print(
            history
        )


        # ----------------------------------------------------
        # ONLY MARK SUCCESSFUL PRODUCTS
        # ----------------------------------------------------

        mark_processed(
            product,
            state
        )


        print()

        print(
            "[OK] LIVE PRODUCT PROCESSED "
            "AND MARKED AS SEEN."
        )


        return True


    except Exception as error:

        print()

        print(
            "❌ LIVE PRODUCT PROCESSING FAILED"
        )

        print()

        print(
            str(error)
        )

        print()

        traceback.print_exc()


        # IMPORTANT:
        #
        # Failed product is NOT marked processed.
        #
        # Therefore the monitor can retry it
        # on a future check.
        #

        return False


    finally:

        # ----------------------------------------------------
        # ALWAYS DELETE TEMPORARY SATELLITE DATA
        # ----------------------------------------------------

        if work_dir:

            print()

            print(
                "Deleting downloaded "
                "satellite data..."
            )


            shutil.rmtree(
                work_dir,
                ignore_errors=True
            )


            print(
                "Satellite product deleted."
            )


# ============================================================
# FIRST RUN HANDLING
# ============================================================

def initialize_first_run(
    state,
    s2,
    s1
):

    processed = state.get(
        "processed_ids",
        []
    )


    if processed:

        return False


    title(
        "FIRST MONITOR RUN"
    )


    print(
        "This is the first run."
    )

    print()

    print(
        "Only the newest Sentinel-2 "
        "and Sentinel-1 scenes will "
        "be processed."
    )

    print()

    print(
        "Older search results will be "
        "marked as already seen."
    )


    # --------------------------------------------------------
    # KEEP ONLY NEWEST PRODUCT
    # --------------------------------------------------------

    if s2:

        newest_s2 = s2[0]

        newest_id = product_id(
            newest_s2
        )

        if newest_id:

            processed.append(
                newest_id
            )


        print()

        print(
            "Newest Sentinel-2:"
        )

        print(
            product_name(
                newest_s2
            )
        )


        for product in s2[1:]:

            pid = product_id(
                product
            )

            if pid and pid not in processed:

                processed.append(
                    pid
                )


    if s1:

        newest_s1 = s1[0]

        newest_id = product_id(
            newest_s1
        )

        if newest_id:

            processed.append(
                newest_id
            )


        print()

        print(
            "Newest Sentinel-1:"
        )

        print(
            product_name(
                newest_s1
            )
        )


        for product in s1[1:]:

            pid = product_id(
                product
            )

            if pid and pid not in processed:

                processed.append(
                    pid
                )


    # --------------------------------------------------------
    # IMPORTANT
    #
    # We want the newest products to remain NEW
    # so remove them from processed list.
    # --------------------------------------------------------

    if s2:

        newest_id = product_id(
            s2[0]
        )

        if newest_id in processed:

            processed.remove(
                newest_id
            )


    if s1:

        newest_id = product_id(
            s1[0]
        )

        if newest_id in processed:

            processed.remove(
                newest_id
            )


    state[
        "processed_ids"
    ] = processed


    save_state(
        state
    )


    return True


# ============================================================
# CHECK ONCE
# ============================================================

def check_once(state):

    title(
        "NEW SATELLITE CHECK"
    )


    print(
        "UTC:"
    )

    print(
        now_utc().isoformat()
    )


    print()

    title(
        "LIVE SATELLITE SEARCH"
    )


    print(
        "Region:"
    )

    print(
        REGION_NAME
    )

    print()

    print(
        "Bounding box:"
    )

    print(
        f"[{WEST}, {SOUTH}, "
        f"{EAST}, {NORTH}]"
    )

    print()

    print(
        f"Last {SEARCH_HOURS} hours"
    )


    # ========================================================
    # SEARCH
    # ========================================================

    print()

    print(
        "Searching Sentinel-2 L2A..."
    )

    s2 = search_cdse(
        "S2"
    )


    print()

    print(
        "Searching Sentinel-1 GRD..."
    )

    s1 = search_cdse(
        "S1"
    )


    # ========================================================
    # FIRST RUN
    # ========================================================

    first_run = (
        len(
            state.get(
                "processed_ids",
                []
            )
        ) == 0
    )


    if first_run:

        initialize_first_run(
            state,
            s2,
            s1
        )


    # ========================================================
    # FIND NEWEST UNSEEN
    # ========================================================

    new_s2 = select_new_product(
        s2,
        state
    )


    new_s1 = select_new_product(
        s1,
        state
    )


    # ========================================================
    # SUMMARY
    # ========================================================

    title(
        "NEW PRODUCT SUMMARY"
    )


    print(
        f"Sentinel-2 available: "
        f"{len(s2)}"
    )


    print(
        "New Sentinel-2:",
        1 if new_s2 else 0
    )


    print()


    print(
        f"Sentinel-1 available: "
        f"{len(s1)}"
    )


    print(
        "New Sentinel-1:",
        1 if new_s1 else 0
    )


    # ========================================================
    # PROCESS NEWEST FLOOD
    # ========================================================

    if new_s2:

        process_product(
            "S2",
            new_s2,
            state
        )

    else:

        print()

        print(
            "[NO NEW SENTINEL-2 PRODUCT]"
        )

        print(
            "No newer Sentinel-2 L2A scene "
            "since the previous check."
        )


    # ========================================================
    # PROCESS NEWEST LANDSLIDE
    # ========================================================

    if new_s1:

        process_product(
            "S1",
            new_s1,
            state
        )

    else:

        print()

        print(
            "[NO NEW SENTINEL-1 PRODUCT]"
        )

        print(
            "No newer Sentinel-1 GRD scene "
            "since the previous check."
        )


    # ========================================================
    # SAVE CHECK TIME
    # ========================================================

    state[
        "last_check"
    ] = now_utc().isoformat()


    save_state(
        state
    )


# ============================================================
# CLEAN OLD TEMP DIRECTORIES
# ============================================================

def clean_old_live_directories():

    if not LIVE_DIR.exists():

        return


    for item in LIVE_DIR.iterdir():

        if not item.is_dir():

            continue


        try:

            shutil.rmtree(
                item,
                ignore_errors=True
            )

        except Exception:

            pass


# ============================================================
# MAIN
# ============================================================

def main():

    title(
        "NEAR-REAL-TIME DISASTER MONITOR"
    )


    print(
        "Region:"
    )

    print(
        "Pakistan, India, Nepal, Bhutan, "
        "Bangladesh, Myanmar, Sri Lanka"
    )


    print()

    print(
        "Bounding box:"
    )

    print(
        f"[{WEST}, {SOUTH}, "
        f"{EAST}, {NORTH}]"
    )


    print()

    print(
        "Detection:"
    )

    print(
        "Sentinel-2 L2A -> FLOOD"
    )

    print(
        "Sentinel-1 GRD -> LANDSLIDE"
    )


    print()

    print(
        "Check interval: 15 minutes"
    )

    print(
        "Search window: 72 hours"
    )


    print()

    separator()

    print(
        "LIVE DATA PIPELINE"
    )

    separator()


    print(
        "CDSE"
    )

    print(
        "↓"
    )

    print(
        "Latest satellite product"
    )

    print(
        "↓"
    )

    print(
        "Download exact product"
    )

    print(
        "↓"
    )

    print(
        "Extract SAFE"
    )

    print(
        "↓"
    )

    print(
        "Run detector on EXACT SAFE"
    )

    print(
        "↓"
    )

    print(
        "GeoJSON + prediction result"
    )

    print(
        "↓"
    )

    print(
        "API / Frontend Map"
    )


    print()

    # ========================================================
    # CHECK DETECTORS
    # ========================================================

    if flood_detector is None:

        print(
            "⚠ Flood detector unavailable."
        )

    else:

        print(
            "[OK] flood_detector.py loaded."
        )


    if landslide_detection is None:

        print(
            "⚠ Landslide detector unavailable."
        )

    else:

        print(
            "[OK] landslide_detection.py loaded."
        )


    # ========================================================
    # STATE
    # ========================================================

    state = load_state()


    print()

    print(
        "Previously processed products:"
    )

    print(
        len(
            state.get(
                "processed_ids",
                []
            )
        )
    )


    # ========================================================
    # AUTH
    # ========================================================

    print()

    print(
        "Creating CDSE client..."
    )

    authenticate()


    print()

    print(
        "🚀 LIVE MONITOR STARTED"
    )


    # ========================================================
    # LOOP
    # ========================================================

    try:

        while True:

            try:

                check_once(
                    state
                )


            except Exception as error:

                print()

                print(
                    "MONITOR CHECK ERROR"
                )

                print(
                    str(error)
                )

                traceback.print_exc()


            # ------------------------------------------------
            # NEXT CHECK
            # ------------------------------------------------

            next_check = (
                now_utc()
                +
                timedelta(
                    seconds=CHECK_INTERVAL
                )
            )


            title(
                "NEXT SATELLITE CHECK"
            )


            print(
                next_check.isoformat()
            )


            print()

            print(
                "Waiting 15 minutes..."
            )


            # ------------------------------------------------
            # INTERRUPTIBLE WAIT
            # ------------------------------------------------

            for _ in range(
                CHECK_INTERVAL
            ):

                time.sleep(
                    1
                )


    except KeyboardInterrupt:

        print()

        print(
            "Monitor stopped by user."
        )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    main()

