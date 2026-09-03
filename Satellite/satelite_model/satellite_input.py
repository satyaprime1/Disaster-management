from pathlib import Path
import json

import numpy as np
import rasterio
from rasterio.warp import reproject, Resampling


# ============================================================
# PATHS
# ============================================================

BACKEND_DIR = Path(__file__).resolve().parents[1]

DATA_DIR = BACKEND_DIR / "data"
SATELLITE_DIR = DATA_DIR / "satellite"

PRODUCTS_DIR = SATELLITE_DIR / "products"
TILES_DIR = SATELLITE_DIR / "tiles"
METADATA_DIR = SATELLITE_DIR / "metadata"

DEM_10M = SATELLITE_DIR / "dem" / "dem_10m.npy"
SLOPE_10M = SATELLITE_DIR / "dem" / "slope_10m.npy"

TILES_DIR.mkdir(parents=True, exist_ok=True)
METADATA_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# SETTINGS
# ============================================================

TILE_SIZE = 128

SENTINEL_BANDS = [
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

MODEL_CHANNELS = 14


# ============================================================
# LOAD TERRAIN
# ============================================================

print("Loading DEM...")

if not DEM_10M.exists():
    raise FileNotFoundError(
        f"DEM not found:\n{DEM_10M}"
    )

DEM_FULL = np.load(
    DEM_10M,
    mmap_mode="r"
)

print("Loading SLOPE...")

if not SLOPE_10M.exists():
    raise FileNotFoundError(
        f"SLOPE not found:\n{SLOPE_10M}"
    )

SLOPE_FULL = np.load(
    SLOPE_10M,
    mmap_mode="r"
)


# ============================================================
# FIND PRODUCT
# ============================================================

def find_product():

    print("\n" + "=" * 60)
    print("SEARCHING SENTINEL-2 PRODUCT")
    print("=" * 60)

    products = []

    if not PRODUCTS_DIR.exists():
        raise FileNotFoundError(
            f"Products directory not found:\n{PRODUCTS_DIR}"
        )

    for p in PRODUCTS_DIR.iterdir():

        if p.is_dir() and p.name.endswith(".SAFE"):
            products.append(p)

    if not products:

        for p in PRODUCTS_DIR.iterdir():

            if p.is_dir():

                products.extend(
                    list(p.glob("*.SAFE"))
                )

    if not products:

        raise FileNotFoundError(
            "No Sentinel-2 SAFE product found."
        )

    products.sort(
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )

    print("\nProduct found:")
    print(products[0])

    return products[0]


# ============================================================
# FIND BAND
# ============================================================

def find_band(product, band):

    matches = list(
        product.rglob(
            f"*_{band}_*.jp2"
        )
    )

    if not matches:

        raise FileNotFoundError(
            f"Band {band} not found."
        )

    for m in matches:

        if "R10m" in str(m):
            return m

    for m in matches:

        if "R20m" in str(m):
            return m

    return matches[0]


# ============================================================
# FIND ALL BANDS
# ============================================================

def find_all_bands(product):

    print("\n" + "=" * 60)
    print("FINDING SENTINEL-2 BANDS")
    print("=" * 60)

    band_paths = {}

    for band in SENTINEL_BANDS:

        path = find_band(
            product,
            band
        )

        band_paths[band] = path

        print(
            f"[FOUND] {band}: {path.name}"
        )

    return band_paths


# ============================================================
# REFERENCE
# ============================================================

def get_reference(band_paths):

    with rasterio.open(
        band_paths["B02"]
    ) as src:

        return {
            "width": src.width,
            "height": src.height,
            "transform": src.transform,
            "crs": src.crs
        }


# ============================================================
# NORMALIZATION
# ============================================================

def normalize_band(data):

    data = np.asarray(
        data,
        dtype=np.float32
    )

    data = np.nan_to_num(
        data,
        nan=0.0,
        posinf=0.0,
        neginf=0.0
    )

    data = data / 10000.0

    data = data * 6.0

    return data


# ============================================================
# READ BAND TILE
# ============================================================

def read_band_tile(
    band_path,
    reference,
    row,
    col
):

    destination = np.zeros(
        (
            TILE_SIZE,
            TILE_SIZE
        ),
        dtype=np.float32
    )

    window = rasterio.windows.Window(
        col,
        row,
        TILE_SIZE,
        TILE_SIZE
    )

    dst_transform = (
        rasterio.windows.transform(
            window,
            reference["transform"]
        )
    )

    with rasterio.open(
        band_path
    ) as src:

        reproject(

            source=rasterio.band(
                src,
                1
            ),

            destination=destination,

            src_transform=src.transform,

            src_crs=src.crs,

            dst_transform=dst_transform,

            dst_crs=reference["crs"],

            resampling=Resampling.bilinear,

            src_nodata=0,

            dst_nodata=0
        )

    return normalize_band(
        destination
    )


# ============================================================
# CREATE ONE TILE
# ============================================================

def create_one_tile(
    band_paths,
    reference,
    row,
    col
):

    bands = {}

    for band in SENTINEL_BANDS:

        bands[band] = read_band_tile(
            band_paths[band],
            reference,
            row,
            col
        )

    dem = DEM_FULL[
        row:row + TILE_SIZE,
        col:col + TILE_SIZE
    ].astype(np.float32)

    slope = SLOPE_FULL[
        row:row + TILE_SIZE,
        col:col + TILE_SIZE
    ].astype(np.float32)

    # B10 is not available at the required
    # resolution in this pipeline.
    b10 = np.zeros(
        (
            TILE_SIZE,
            TILE_SIZE
        ),
        dtype=np.float32
    )

    image = np.stack([

        bands["B01"],
        bands["B02"],
        bands["B03"],
        bands["B04"],
        bands["B05"],
        bands["B06"],
        bands["B07"],
        bands["B08"],
        bands["B09"],

        b10,

        bands["B11"],
        bands["B12"],

        dem,
        slope

    ], axis=0)

    return image.astype(
        np.float32
    )


# ============================================================
# CREATE TILES
# ============================================================

def create_tiles(product):

    band_paths = find_all_bands(
        product
    )

    reference = get_reference(
        band_paths
    )

    width = reference["width"]
    height = reference["height"]

    cols = width // TILE_SIZE
    rows = height // TILE_SIZE

    total_tiles = rows * cols

    print("\n" + "=" * 60)
    print("TILE GENERATION")
    print("=" * 60)

    print(
        f"Scene: {width} x {height}"
    )

    print(
        f"Tile:  {TILE_SIZE} x {TILE_SIZE}"
    )

    print(
        f"Grid:  {rows} x {cols}"
    )

    print(
        f"Complete tiles: {total_tiles}"
    )

    # --------------------------------------------------------
    # Scene centre
    # --------------------------------------------------------

    center_x = width / 2
    center_y = height / 2

    center_lon, center_lat = (
        rasterio.transform.xy(
            reference["transform"],
            center_y,
            center_x,
            offset="center"
        )
    )

    # --------------------------------------------------------
    # Bounds
    # --------------------------------------------------------

    bounds = rasterio.transform.array_bounds(
        height,
        width,
        reference["transform"]
    )

    bottom, top = bounds[1], bounds[3]
    left, right = bounds[0], bounds[2]

    # --------------------------------------------------------
    # Metadata
    # --------------------------------------------------------

    metadata = {

        "product_name":
            product.name,

        "product_path":
            str(product),

        "scene_width":
            width,

        "scene_height":
            height,

        "rows":
            rows,

        "cols":
            cols,

        "tile_size":
            TILE_SIZE,

        "total_tiles":
            total_tiles,

        "channel_order": [

            "B01",
            "B02",
            "B03",
            "B04",
            "B05",
            "B06",
            "B07",
            "B08",
            "B09",
            "B10",
            "B11",
            "B12",
            "DEM",
            "SLOPE"

        ],

        "crs":
            str(reference["crs"]),

        "transform":
            list(reference["transform"]),

        "center": {

            "latitude":
                float(center_lat),

            "longitude":
                float(center_lon)

        },

        "bounds": {

            "left":
                float(left),

            "bottom":
                float(bottom),

            "right":
                float(right),

            "top":
                float(top)

        }

    }

    metadata_path = (
        METADATA_DIR /
        "tile_metadata.json"
    )

    with open(
        metadata_path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            metadata,
            f,
            indent=4
        )

    # --------------------------------------------------------
    # Scene metadata
    # --------------------------------------------------------

    scene_metadata_path = (
        METADATA_DIR /
        "scene_metadata.json"
    )

    with open(
        scene_metadata_path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            metadata,
            f,
            indent=4
        )

    # --------------------------------------------------------
    # Generate tiles
    # --------------------------------------------------------

    processed = 0

    for r in range(rows):

        for c in range(cols):

            processed += 1

            tile = create_one_tile(

                band_paths,

                reference,

                r * TILE_SIZE,

                c * TILE_SIZE

            )

            np.save(

                TILES_DIR /
                f"tile_{r:03d}_{c:03d}.npy",

                tile

            )

            if (
                processed % 50 == 0
                or processed == total_tiles
            ):

                print(

                    f"\rProcessing tile "
                    f"{processed}/{total_tiles}",

                    end=""

                )

    print()

    print("\n" + "=" * 60)
    print("TILE GENERATION COMPLETE")
    print("=" * 60)

    print(
        f"Tiles written: {total_tiles}"
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print("\n" + "=" * 60)
    print("SATELLITE INPUT PIPELINE")
    print("=" * 60)

    product = find_product()

    create_tiles(
        product
    )

    print("\n" + "=" * 60)
    print("SUCCESS")
    print("=" * 60)

    print(
        "\n14-channel tiles generated."
    )

    print(
        "Channel order:"
    )

    print(
        "B01 B02 B03 B04 B05 B06 "
        "B07 B08 B09 B10 B11 B12 DEM SLOPE"
    )