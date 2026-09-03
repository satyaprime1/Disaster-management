from pathlib import Path
import numpy as np
import torch
import torch.nn as nn
from torchvision import models


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR.parent / "data" / "satellite"
PROCESSED_DIR = DATA_DIR / "processed"

IMAGE_PATH = PROCESSED_DIR / "latest.npy"


# ============================================================
# DEVICE
# ============================================================

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

print("Device:", device)


# ============================================================
# LOAD PROCESSED SATELLITE IMAGE
# ============================================================

if not IMAGE_PATH.exists():
    raise FileNotFoundError(
        f"Satellite data not found:\n{IMAGE_PATH}"
    )

img = np.load(IMAGE_PATH)

print("Loaded:", IMAGE_PATH)
print("Shape:", img.shape)
print("Data type:", img.dtype)


# ============================================================
# CONVERT NUMPY → PYTORCH TENSOR
# ============================================================

img = img.astype(np.float32)

# If image values are 0–255, normalize to 0–1
if img.max() > 1:
    img = img / 255.0


# Handle different possible image formats
if img.ndim == 2:
    # Grayscale → RGB
    img = np.stack([img, img, img], axis=-1)

elif img.ndim == 3:

    # HWC format
    if img.shape[-1] == 1:
        img = np.repeat(img, 3, axis=-1)

    elif img.shape[-1] >= 3:
        img = img[:, :, :3]

    # CHW format
    elif img.shape[0] in [1, 3]:
        img = np.transpose(img, (1, 2, 0))

    else:
        raise ValueError(
            f"Unsupported image shape: {img.shape}"
        )

else:
    raise ValueError(
        f"Unsupported image dimensions: {img.ndim}"
    )


# HWC → CHW
img = np.transpose(img, (2, 0, 1))

# Add batch dimension
img = torch.tensor(img, dtype=torch.float32).unsqueeze(0)

print("Tensor shape:", img.shape)


# ============================================================
# LOAD RESNET18
# ============================================================

print("Loading ResNet18...")

model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)


# ============================================================
# MODEL CONFIGURATION
# ============================================================

# IMPORTANT:
# Change this when your own trained model is available.

NUM_CLASSES = 3

model.fc = nn.Linear(
    model.fc.in_features,
    NUM_CLASSES
)

model = model.to(device)


# ============================================================
# INFERENCE
# ============================================================

model.eval()

img = img.to(device)

with torch.no_grad():
    output = model(img)

    probabilities = torch.softmax(output, dim=1)

    predicted_class = torch.argmax(
        probabilities,
        dim=1
    ).item()


# ============================================================
# CLASS NAMES
# ============================================================

classes = [
    "Normal",
    "Flood Risk",
    "Landslide Risk"
]


# ============================================================
# RESULT
# ============================================================

prediction = classes[predicted_class]

confidence = probabilities[0][predicted_class].item() * 100

print()
print("=" * 50)
print("SATELLITE AI ANALYSIS")
print("=" * 50)

print(f"Prediction : {prediction}")
print(f"Confidence : {confidence:.2f}%")

print()
print("Class probabilities:")

for class_name, probability in zip(
    classes,
    probabilities[0]
):
    print(
        f"{class_name:<20} "
        f"{probability.item() * 100:.2f}%"
    )

print("=" * 50)