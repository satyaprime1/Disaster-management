from pathlib import Path
from datetime import datetime, timezone
import json

import numpy as np
import torch
from tqdm import tqdm

from model import UNet
from dataset import normalize_channels
from geo_detector import probability_map_to_geojson


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR.parent
DATA_DIR = BACKEND_DIR / "data"
SATELLITE_DIR = DATA_DIR / "satellite"
TILES_DIR = SATELLITE_DIR / "tiles"
OUTPUT_DIR = BASE_DIR / "outputs"
HISTORY_DIR = OUTPUT_DIR / "history"

CHECKPOINT = BASE_DIR / "checkpoints" / "best_model.pth"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
HISTORY_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# SETTINGS
# ============================================================

TILE_SIZE = 128
MODEL_CHANNELS = 14
THRESHOLD = 0.5
MIN_REGION_PIXELS = 15
MAX_REGIONS = 100


# ============================================================
# DEVICE
# ============================================================

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

print()
print("=" * 70)
print("LANDSLIDE PREDICTION PIPELINE (ATTENTION-RESUNET)")
print("=" * 70)
print(f"Device: {device}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")


# ============================================================
# FIND TILES
# ============================================================

tile_files = sorted(TILES_DIR.glob("tile_*.npy"))

if not tile_files:
    raise RuntimeError(f"No tiles found in {TILES_DIR}")

total_tiles = len(tile_files)
print(f"Tiles found: {total_tiles}")


# ============================================================
# DETERMINE GRID
# ============================================================

rows = 0
cols = 0

for tile_path in tile_files:
    parts = tile_path.stem.split("_")
    try:
        r = int(parts[1])
        c = int(parts[2])
        rows = max(rows, r + 1)
        cols = max(cols, c + 1)
    except Exception:
        pass

if rows == 0 or cols == 0:
    rows = 85
    cols = 85

prediction_height = rows * TILE_SIZE
prediction_width = cols * TILE_SIZE

print(f"Scene: {prediction_height} x {prediction_width} (Grid: {rows} x {cols})")


# ============================================================
# LOAD MODEL
# ============================================================

print()
print("=" * 70)
print("LOADING ATTENTION-RESUNET MODEL")
print("=" * 70)

model = UNet(in_channels=MODEL_CHANNELS, out_channels=1)
state_dict = torch.load(CHECKPOINT, map_location=device)
model.load_state_dict(state_dict)
model.to(device)
model.eval()

print("Model loaded successfully.")


# ============================================================
# PREDICTION
# ============================================================

probability_map = np.zeros((prediction_height, prediction_width), dtype=np.float32)

print()
print("=" * 70)
print("RUNNING PREDICTION ON TILES")
print("=" * 70)

successful = 0
failed = 0

with torch.no_grad():
    for tile_path in tqdm(tile_files, desc="Predicting"):
        try:
            tile = np.load(tile_path)

            if tile.shape != (MODEL_CHANNELS, TILE_SIZE, TILE_SIZE):
                raise ValueError(f"Invalid tile shape: {tile.shape}")

            # Apply identical global channel normalization
            tile_norm = normalize_channels(tile)

            tensor = torch.from_numpy(tile_norm).float().unsqueeze(0).to(device)
            output = model(tensor)
            probability = torch.sigmoid(output).squeeze().detach().cpu().numpy()

            parts = tile_path.stem.split("_")
            tile_row = int(parts[1])
            tile_col = int(parts[2])

            r0 = tile_row * TILE_SIZE
            r1 = r0 + TILE_SIZE
            c0 = tile_col * TILE_SIZE
            c1 = c0 + TILE_SIZE

            probability_map[r0:r1, c0:c1] = probability
            successful += 1

        except Exception as e:
            failed += 1
            print(f"\nFailed tile: {tile_path.name} -> {e}")


# ============================================================
# STATISTICS & DETECTION
# ============================================================

max_probability = float(np.max(probability_map))
mean_probability = float(np.mean(probability_map))
median_probability = float(np.median(probability_map))

binary_mask = probability_map >= THRESHOLD
affected_pixels = int(np.sum(binary_mask))
total_pixels = probability_map.size
affected_area_percent = (affected_pixels / total_pixels) * 100.0

print()
print("=" * 70)
print("PREDICTION STATISTICS")
print("=" * 70)
print(f"Max Probability:      {max_probability:.4f}")
print(f"Mean Probability:     {mean_probability:.6f}")
print(f"Median Probability:   {median_probability:.8f}")
print(f"Affected Pixels:      {affected_pixels:,} ({affected_area_percent:.4f}%)")
print(f"Successful Tiles:     {successful}/{total_tiles}")


# ============================================================
# GEOJSON GENERATION
# ============================================================

try:
    geojson, regions = probability_map_to_geojson(
        probability_map,
        threshold=THRESHOLD,
        min_pixels=MIN_REGION_PIXELS,
        max_regions=MAX_REGIONS
    )
except Exception as e:
    print(f"\nGeoJSON conversion fallback: {e}")
    geojson = {"type": "FeatureCollection", "features": []}
    regions = []

if affected_area_percent >= 0.10:
    risk = "HIGH"
elif affected_area_percent >= 0.01:
    risk = "MEDIUM"
elif affected_area_percent > 0:
    risk = "LOW"
else:
    risk = "NONE"

alert = (risk in ["HIGH", "MEDIUM"] and len(regions) > 0)


# ============================================================
# SAVE OUTPUTS
# ============================================================

stitched_prob_path = OUTPUT_DIR / "stitched_probability.npy"
stitched_mask_path = OUTPUT_DIR / "stitched_landslide_mask.npy"
geojson_path = OUTPUT_DIR / "landslide_regions.geojson"
results_path = OUTPUT_DIR / "prediction_results.json"

np.save(stitched_prob_path, probability_map.astype(np.float32))
np.save(stitched_mask_path, binary_mask.astype(np.uint8))

with open(geojson_path, "w", encoding="utf-8") as f:
    json.dump(geojson, f, indent=2)

timestamp = datetime.now(timezone.utc).isoformat()

result_payload = {
    "disaster": "landslide",
    "timestamp": timestamp,
    "model": "Attention-ResUNet",
    "threshold": THRESHOLD,
    "maximum_probability": max_probability,
    "mean_probability": mean_probability,
    "median_probability": median_probability,
    "affected_pixels": affected_pixels,
    "affected_area_percent": affected_area_percent,
    "risk": risk,
    "alert": alert,
    "total_tiles": total_tiles,
    "successful_tiles": successful,
    "failed_tiles": failed,
    "prediction_height": prediction_height,
    "prediction_width": prediction_width,
    "affected_regions": regions,
    "geojson": geojson
}

with open(results_path, "w", encoding="utf-8") as f:
    json.dump(result_payload, f, indent=2)

print()
print("=" * 70)
print("PREDICTION PIPELINE COMPLETED")
print("=" * 70)
print(f"Probability map saved: {stitched_prob_path}")
print(f"Results summary saved: {results_path}")
print(f"GeoJSON regions saved: {geojson_path}")
