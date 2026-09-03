from pathlib import Path
import numpy as np
import rasterio
from rasterio.warp import reproject, Resampling

# ============================================================
# PATHS
# ============================================================

BACKEND = Path(__file__).resolve().parents[1]

DEM_PATH = BACKEND / "data" / "satellite" / "dem" / "hyderabad_dem.tif"
PRODUCTS = BACKEND / "data" / "satellite" / "products"

OUT_DEM = BACKEND / "data" / "satellite" / "dem" / "dem_10m.npy"
OUT_SLOPE = BACKEND / "data" / "satellite" / "dem" / "slope_10m.npy"

# ============================================================
# FIND SENTINEL REFERENCE (B02 10 m)
# ============================================================

b02_files = list(PRODUCTS.rglob("*_B02_10m.jp2"))

if not b02_files:
    raise FileNotFoundError("Could not find Sentinel-2 B02_10m.jp2")

REFERENCE = b02_files[0]

with rasterio.open(REFERENCE) as ref:
    width = ref.width
    height = ref.height
    transform = ref.transform
    crs = ref.crs

print("=" * 60)
print("BUILDING TERRAIN LAYERS")
print("=" * 60)
print("Reference:", REFERENCE.name)
print(f"Resolution: 10 m")
print(f"Output size: {width} x {height}")

# ============================================================
# RESAMPLE DEM TO 10 m GRID
# ============================================================

with rasterio.open(DEM_PATH) as src:

    dem = np.zeros((height, width), dtype=np.float32)

    reproject(
        source=rasterio.band(src, 1),
        destination=dem,
        src_transform=src.transform,
        src_crs=src.crs,
        dst_transform=transform,
        dst_crs=crs,
        resampling=Resampling.bilinear,
    )

# ============================================================
# CLEAN + NORMALIZE DEM
# Match Landslide4Sense scale (~0–6)
# ============================================================

dem = np.nan_to_num(dem)

dem = (dem - dem.min()) / (dem.max() - dem.min() + 1e-8)
dem = dem * 6.0

# ============================================================
# COMPUTE SLOPE
# ============================================================

gy, gx = np.gradient(dem)

slope = np.sqrt(gx**2 + gy**2)

slope = (slope - slope.min()) / (slope.max() - slope.min() + 1e-8)
slope = slope * 6.0

# ============================================================
# SAVE
# ============================================================

OUT_DEM.parent.mkdir(parents=True, exist_ok=True)

np.save(OUT_DEM, dem.astype(np.float32))
np.save(OUT_SLOPE, slope.astype(np.float32))

# ============================================================
# SUMMARY
# ============================================================

print()
print("=" * 60)
print("TERRAIN CREATED")
print("=" * 60)

print("DEM   :", OUT_DEM)
print("Slope :", OUT_SLOPE)

print()
print("DEM stats")
print(f"  Shape: {dem.shape}")
print(f"  Min:   {dem.min():.4f}")
print(f"  Max:   {dem.max():.4f}")

print()
print("Slope stats")
print(f"  Shape: {slope.shape}")
print(f"  Min:   {slope.min():.4f}")
print(f"  Max:   {slope.max():.4f}")

print()
print("DONE")