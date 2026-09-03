import os
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

# ============================================================
# BACKEND CHECK
# ============================================================
try:
    import cv2

    BACKEND = "cv2"
except ImportError:
    try:
        from scipy import ndimage

        BACKEND = "scipy"
    except ImportError:
        BACKEND = None


# ============================================================
# FILTERING HELPERS
# ============================================================


def remove_small_components(
    binary_mask: np.ndarray, min_area: int = 50
) -> np.ndarray:
    """Filters out tiny disconnected noise clusters below min_area."""
    if BACKEND == "cv2":
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
            (binary_mask * 255).astype(np.uint8), connectivity=8
        )
        cleaned = np.zeros_like(binary_mask, dtype=np.uint8)
        for i in range(1, num_labels):
            if stats[i, cv2.CC_STAT_AREA] >= min_area:
                cleaned[labels == i] = 1
        return cleaned

    elif BACKEND == "scipy":
        labeled, num_features = ndimage.label(
            binary_mask, structure=np.ones((3, 3))
        )
        if num_features == 0:
            return binary_mask
        sizes = ndimage.sum(binary_mask, labeled, range(1, num_features + 1))
        mask_sizes = sizes >= min_area
        cleaned = mask_sizes[labeled - 1]
        cleaned[labeled == 0] = 0
        return cleaned.astype(np.uint8)

    return binary_mask.astype(np.uint8)


def remove_linear_seam_artifacts(binary_mask: np.ndarray) -> np.ndarray:
    """Removes harsh 1-pixel wide vertical/horizontal grid lines caused by tile seams."""
    if BACKEND == "cv2":
        # Morphological opening with long thin kernels to detect seams, then subtract
        kernel_v = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 15))
        kernel_h = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 1))

        seams_v = cv2.morphologyEx(
            binary_mask * 255, cv2.MORPH_OPEN, kernel_v
        )  # vertical lines
        seams_h = cv2.morphologyEx(
            binary_mask * 255, cv2.MORPH_OPEN, kernel_h
        )  # horizontal lines

        # Only isolate very thin lines
        seam_mask = ((seams_v > 0) | (seams_h > 0)).astype(np.uint8)
        cleaned = np.where(seam_mask == 1, 0, binary_mask)
        return cleaned.astype(np.uint8)

    elif BACKEND == "scipy":
        seams_v = ndimage.binary_opening(
            binary_mask, structure=np.ones((15, 1))
        )
        seams_h = ndimage.binary_opening(
            binary_mask, structure=np.ones((1, 15))
        )
        seam_mask = seams_v | seams_h
        return np.where(seam_mask, 0, binary_mask).astype(np.uint8)

    return binary_mask


# ============================================================
# MAIN PIPELINEite
# ============================================================

BASE = Path(__file__).resolve().parent
OUT = BASE / "outputs"
OUT.mkdir(exist_ok=True)

prob_path = OUT / "stitched_probability.npy"

if not prob_path.exists():
    raise FileNotFoundError(f"Cannot find probability file at: {prob_path}")

print("=" * 60)
print("LANDSLIDE PREDICTION POST-PROCESSING")
print(f"Backend Engine: {BACKEND}")
print("=" * 60)

# 1. Load and Sanitize
prob = np.load(prob_path)
prob = np.nan_to_num(prob, nan=0.0, posinf=0.0, neginf=0.0)
prob = np.clip(prob, 0.0, 1.0)
total_pixels = int(prob.size)

print(f"Raster Dimensions: {prob.shape} | Total Pixels: {total_pixels:,}")

# 2. Summary Statistics
p_min = float(np.min(prob))
p_max = float(np.max(prob))
p_mean = float(np.mean(prob))
p_99_9 = float(np.percentile(prob, 99.9))
p_99_95 = float(np.percentile(prob, 99.95))

print("\nProbability Distribution")
print("-" * 40)
print(f"Min        : {p_min:.8f}")
print(f"Max        : {p_max:.8f}")
print(f"Mean       : {p_mean:.8f}")
print(f"99.90% Pct : {p_99_9:.8f}")
print(f"99.95% Pct : {p_99_95:.8f}")

# 3. Dynamic Thresholding
# Use the top 0.05% of extreme activations to avoid picking up zero-noise
THRESHOLD = max(p_99_95, 0.001)
MIN_AREA = 50  # Minimum cluster size (pixels)

print("\nProcessing Parameters")
print("-" * 40)
print(f"Active Threshold : {THRESHOLD:.8f}")
print(f"Min Component    : {MIN_AREA} pixels")

# 4. Generate Mask & Clean Noise
raw_mask = (prob >= THRESHOLD).astype(np.uint8)
seam_cleared = remove_linear_seam_artifacts(raw_mask)
clean_mask = remove_small_components(seam_cleared, min_area=MIN_AREA)

raw_pixels = int(np.count_nonzero(raw_mask))
final_pixels = int(np.count_nonzero(clean_mask))

print("\nDetection Summary")
print("-" * 40)
print(
    f"Raw Detections   : {raw_pixels:>10,} px ({raw_pixels / total_pixels * 100:.6f}%)"
)
print(
    f"Clean Detections : {final_pixels:>10,} px ({final_pixels / total_pixels * 100:.6f}%)"
)

# 5. Save Arrays and Images
final_mask_path = OUT / "final_landslide_mask.npy"
np.save(final_mask_path, clean_mask)

# Save Probability Heatmap
plt.figure(figsize=(12, 12))
plt.imshow(
    prob,
    cmap="inferno",
    vmin=float(np.percentile(prob, 5)),
    vmax=float(np.percentile(prob, 99.99)),
    interpolation="nearest",
)
plt.colorbar(label="Prediction Confidence", shrink=0.7)
plt.title("Calibrated Landslide Probability Heatmap")
plt.axis("off")
plt.savefig(
    OUT / "final_probability_map.png", dpi=200, bbox_inches="tight", pad_inches=0
)
plt.close()

# Save Clean Binary Detection Mask
plt.figure(figsize=(12, 12))
plt.imshow(
    clean_mask * 255, cmap="gray", vmin=0, vmax=255, interpolation="nearest"
)
plt.title(
    f"Final Landslide Detections (Cleaned)\nThreshold: {THRESHOLD:.6f} | Area: {final_pixels / total_pixels * 100:.4f}%"
)
plt.axis("off")
plt.savefig(
    OUT / "final_landslide_mask.png", dpi=200, bbox_inches="tight", pad_inches=0
)
plt.close()

print("\n" + "=" * 60)
print(f"Output files saved in: {OUT}")
print("1. final_landslide_mask.npy")
print("2. final_landslide_mask.png")
print("3. final_probability_map.png")
print("=" * 60)