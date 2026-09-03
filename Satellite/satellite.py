from pathlib import Path
from datetime import datetime, timedelta, UTC
import json
import zipfile

import requests


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

SATELLITE_DIR = (
    BASE_DIR
    / "data"
    / "satellite"
)

RAW_DIR = SATELLITE_DIR / "raw"
PRODUCT_DIR = SATELLITE_DIR / "products"
BANDS_DIR = SATELLITE_DIR / "bands"

RAW_DIR.mkdir(parents=True, exist_ok=True)
PRODUCT_DIR.mkdir(parents=True, exist_ok=True)
BANDS_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# COPERNICUS
# ============================================================

STAC_URL = (
    "https://stac.dataspace.copernicus.eu/v1/search"
)

TOKEN_URL = (
    "https://identity.dataspace.copernicus.eu/"
    "auth/realms/CDSE/protocol/openid-connect/token"
)

DOWNLOAD_URL = (
    "https://download.dataspace.copernicus.eu/"
    "odata/v1"
)


# ============================================================
# SENTINEL-2 BANDS
# ============================================================

S2_BANDS = [
    "B01",
    "B02",
    "B03",
    "B04",
    "B05",
    "B06",
    "B07",
    "B08",
    "B09",
    "B11",
    "B12",
]


# ============================================================
# SEARCH SENTINEL-2
# ============================================================

def search_sentinel2(
    latitude,
    longitude,
    days_back=30,
    max_cloud_cover=30,
):

    end_date = datetime.now(UTC)

    start_date = (
        end_date
        - timedelta(days=days_back)
    )

    delta = 0.05

    bbox = [
        longitude - delta,
        latitude - delta,
        longitude + delta,
        latitude + delta,
    ]

    payload = {

        "collections": [
            "sentinel-2-l2a"
        ],

        "bbox": bbox,

        "datetime": (
            start_date.strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
            + "/"
            +
            end_date.strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
        ),

        "limit": 20,

        "query": {
            "eo:cloud_cover": {
                "lte": max_cloud_cover
            }
        },

        "sortby": [
            {
                "field": "properties.eo:cloud_cover",
                "direction": "asc",
            }
        ],
    }

    print()
    print("=" * 60)
    print("SEARCHING SENTINEL-2")
    print("=" * 60)

    print(
        f"Location: {latitude}, {longitude}"
    )

    response = requests.post(
        STAC_URL,
        json=payload,
        timeout=60,
    )

    response.raise_for_status()

    data = response.json()

    features = data.get(
        "features",
        []
    )

    if not features:

        raise RuntimeError(
            "No Sentinel-2 scenes found."
        )

    scene = features[0]

    print()
    print("Scene found:")
    print(
        "ID:",
        scene.get("id")
    )

    print(
        "Date:",
        scene.get(
            "properties",
            {}
        ).get("datetime")
    )

    print(
        "Cloud:",
        scene.get(
            "properties",
            {}
        ).get(
            "eo:cloud_cover"
        ),
        "%"
    )

    return scene


# ============================================================
# AUTHENTICATE
# ============================================================

def get_access_token(username, password):

    print()
    print("=" * 60)
    print("AUTHENTICATING WITH COPERNICUS")
    print("=" * 60)

    data = {
        "grant_type": "password",
        "username": username,
        "password": password,
        "client_id": "cdse-public",
    }

    response = requests.post(
        TOKEN_URL,
        data=data,
        timeout=60,
    )

    response.raise_for_status()

    token_data = response.json()

    access_token = token_data.get(
        "access_token"
    )

    if not access_token:

        raise RuntimeError(
            "Copernicus authentication "
            "did not return an access token."
        )

    print(
        "Authentication successful."
    )

    return access_token


# ============================================================
# FIND PRODUCT ID
# ============================================================

def get_product_id(scene):

    properties = scene.get(
        "properties",
        {}
    )

    # STAC may expose the product ID
    # through several fields.

    product_id = (
        properties.get("cdse:product_id")
        or properties.get("productIdentifier")
    )

    if product_id:
        return product_id

    scene_id = scene.get("id")

    if scene_id:
        return scene_id

    raise RuntimeError(
        "Could not determine Sentinel-2 product ID."
    )


# ============================================================
# SEARCH PRODUCT THROUGH ODATA
# ============================================================

def find_product_odata(scene):

    scene_id = scene.get("id")

    if not scene_id:
        raise RuntimeError(
            "Scene has no product name."
        )

    url = (
        "https://catalogue.dataspace.copernicus.eu/"
        "odata/v1/Products"
    )

    # Use startswith instead of exact equality.
    # This is more robust because the STAC identifier
    # and OData product Name can differ slightly.
    params = {
        "$filter": f"startswith(Name,'{scene_id}')",
        "$top": 10,
    }

    print()
    print("=" * 60)
    print("SEARCHING ODATA PRODUCT")
    print("=" * 60)

    print(
        "Searching for:",
        scene_id
    )

    response = requests.get(
        url,
        params=params,
        timeout=60,
    )

    response.raise_for_status()

    data = response.json()

    products = data.get(
        "value",
        []
    )

    if not products:

        # Try a broader search using the unique
        # beginning of the product name.
        short_id = scene_id[:40]

        params = {
            "$filter": (
                f"startswith(Name,'{short_id}')"
            ),
            "$top": 10,
        }

        response = requests.get(
            url,
            params=params,
            timeout=60,
        )

        response.raise_for_status()

        data = response.json()

        products = data.get(
            "value",
            []
        )

    if not products:

        raise RuntimeError(
            "Product was not found in "
            "Copernicus OData catalogue.\n\n"
            f"STAC scene: {scene_id}"
        )

    # Show what OData found
    print()
    print(
        f"Products found: {len(products)}"
    )

    for product in products:

        print(
            " -",
            product.get("Name")
        )

    # Select first matching product
    product = products[0]

    product_id = product.get(
        "Id"
    )

    product_name = product.get(
        "Name"
    )

    if not product_id:

        raise RuntimeError(
            "OData product has no Id."
        )

    print()
    print(
        "Selected product:"
    )

    print(
        "Name:",
        product_name
    )

    print(
        "ID:",
        product_id
    )

    return product_id


# ============================================================
# DOWNLOAD PRODUCT
# ============================================================

def download_product(
    product_id,
    access_token,
    product_name,
):

    output_path = (
        PRODUCT_DIR
        / f"{product_name}.zip"
    )

    if output_path.exists():

        print()
        print(
            "Product already downloaded:"
        )

        print(output_path)

        return output_path

    url = (
        f"{DOWNLOAD_URL}/"
        f"Products({product_id})/"
        "$value"
    )

    headers = {
        "Authorization":
            f"Bearer {access_token}"
    }

    print()
    print("=" * 60)
    print("DOWNLOADING SENTINEL-2 PRODUCT")
    print("=" * 60)

    print(
        "Product:",
        product_name
    )

    print(
        "Destination:",
        output_path
    )

    with requests.get(
        url,
        headers=headers,
        stream=True,
        timeout=300,
    ) as response:

        response.raise_for_status()

        total = 0

        with open(
            output_path,
            "wb"
        ) as file:

            for chunk in response.iter_content(
                chunk_size=1024 * 1024
            ):

                if chunk:

                    file.write(chunk)

                    total += len(chunk)

                    print(
                        f"\rDownloaded: "
                        f"{total / (1024 * 1024):.1f} MB",
                        end="",
                    )

    print()
    print()
    print(
        "Download complete:"
    )

    print(output_path)

    return output_path


# ============================================================
# EXTRACT PRODUCT
# ============================================================

def extract_product(zip_path):

    extract_dir = (
        PRODUCT_DIR
        / zip_path.stem
    )

    if extract_dir.exists():

        print()
        print(
            "Product already extracted:"
        )

        print(extract_dir)

        return extract_dir

    print()
    print("=" * 60)
    print("EXTRACTING PRODUCT")
    print("=" * 60)

    print(zip_path)

    with zipfile.ZipFile(
        zip_path,
        "r"
    ) as zip_ref:

        zip_ref.extractall(
            extract_dir
        )

    print(
        "Extraction complete."
    )

    return extract_dir


# ============================================================
# FIND BAND FILES
# ============================================================

def find_band_files(product_dir):

    print()
    print("=" * 60)
    print("SEARCHING FOR SENTINEL-2 BANDS")
    print("=" * 60)

    found = {}

    jp2_files = list(
        product_dir.rglob(
            "*.jp2"
        )
    )

    for band in S2_BANDS:

        matches = [
            p
            for p in jp2_files
            if f"_{band}_"
            in p.name
        ]

        if not matches:

            print(
                f"[MISSING] {band}"
            )

            continue

        # Prefer 20m where available,
        # except bands that are naturally 10m.
        preferred = sorted(
            matches,
            key=lambda p:
                (
                    "10m" not in p.name,
                    "20m" not in p.name,
                    str(p),
                )
        )

        selected = preferred[0]

        found[
            band
        ] = selected

        print(
            f"[FOUND] {band}: "
            f"{selected}"
        )

    return found


# ============================================================
# SAVE METADATA
# ============================================================

def save_scene_metadata(scene):

    output = (
        SATELLITE_DIR
        / "selected_scene.json"
    )

    with open(
        output,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            scene,
            f,
            indent=2
        )

    print()
    print(
        "Scene metadata saved:"
    )

    print(output)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    # --------------------------------------------------------
    # DEMO LOCATION
    # --------------------------------------------------------

    LATITUDE = 17.3850
    LONGITUDE = 78.4867

    # --------------------------------------------------------
    # COPERNICUS LOGIN
    # --------------------------------------------------------
    #
    # Enter your account here locally.
    #
    # DO NOT commit this file to GitHub
    # with your password inside it.
    #
    # --------------------------------------------------------

    USERNAME = input(
        "Copernicus email: "
    )

    import getpass

    PASSWORD = getpass.getpass(
        "Copernicus password: "
    )

    # --------------------------------------------------------
    # Search
    # --------------------------------------------------------

    scene = search_sentinel2(
        latitude=LATITUDE,
        longitude=LONGITUDE,
        days_back=30,
        max_cloud_cover=30,
    )

    save_scene_metadata(
        scene
    )

    # --------------------------------------------------------
    # OData product
    # --------------------------------------------------------

    product_id = find_product_odata(
        scene
    )

    # --------------------------------------------------------
    # Authentication
    # --------------------------------------------------------

    access_token = get_access_token(
        USERNAME,
        PASSWORD
    )

    # --------------------------------------------------------
    # Download
    # --------------------------------------------------------

    product_name = scene["id"]

    zip_path = download_product(
        product_id,
        access_token,
        product_name
    )

    # --------------------------------------------------------
    # Extract
    # --------------------------------------------------------

    product_dir = extract_product(
        zip_path
    )

    # --------------------------------------------------------
    # Find bands
    # --------------------------------------------------------

    bands = find_band_files(
        product_dir
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("SATELLITE DOWNLOAD COMPLETE")
    print("=" * 60)

    print(
        f"Bands found: "
        f"{len(bands)} / {len(S2_BANDS)}"
    )

    for band, path in bands.items():

        print(
            f"{band}: {path}"
        )

    if len(bands) == len(S2_BANDS):

        print()
        print(
            "SUCCESS: All required "
            "Sentinel-2 bands found."
        )

        print()
        print(
            "Next step:"
        )

        print(
            "Resample bands → "
            "construct model input."
        )

    else:

        print()
        print(
            "WARNING: Some bands are missing."
        )

        print(
            "Do NOT run the UNet yet."
        )