
from pathlib import Path
from dataset import LandslideDataset

dataset_root = Path(__file__).resolve().parents[1] / "data" / "landslide4sense"

print("Dataset root:", dataset_root)

ds = LandslideDataset(dataset_root)

print("Samples:", len(ds))

img, mask = ds[0]

print("Image shape:", img.shape)
print("Mask shape:", mask.shape)
print("Image dtype:", img.dtype)
print("Mask dtype:", mask.dtype)