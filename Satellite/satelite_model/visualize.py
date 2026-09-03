from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt


BASE_DIR = Path(__file__).resolve().parent

prediction_path = (
    BASE_DIR
    / "outputs"
    / "stitched_prediction.npy"
)

output_path = (
    BASE_DIR
    / "outputs"
    / "prediction_map.png"
)


# Load prediction
prediction = np.load(prediction_path)

print("Prediction shape:", prediction.shape)
print("Min probability:", prediction.min())
print("Max probability:", prediction.max())


# Create binary landslide mask
mask = prediction >= 0.5


# Plot probability map
plt.figure(figsize=(8, 8))

plt.imshow(
    prediction,
    cmap="RdYlGn_r",
    vmin=0,
    vmax=1
)

plt.colorbar(
    label="Landslide Probability"
)

plt.title("Landslide Prediction Map")

plt.axis("off")

plt.tight_layout()

plt.savefig(
    output_path,
    dpi=200,
    bbox_inches="tight"
)

plt.close()


print()
print("Prediction map saved:")
print(output_path)


# ---------------------------------------------------------
# Binary mask
# ---------------------------------------------------------

mask_path = (
    BASE_DIR
    / "outputs"
    / "landslide_mask.png"
)

plt.figure(figsize=(8, 8))

plt.imshow(
    mask,
    cmap="gray"
)

plt.title("Detected Landslide Areas")

plt.axis("off")

plt.tight_layout()

plt.savefig(
    mask_path,
    dpi=200,
    bbox_inches="tight"
)

plt.close()

print("Landslide mask saved:")
print(mask_path)