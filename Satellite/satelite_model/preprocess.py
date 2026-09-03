from pathlib import Path
import cv2
import numpy as np

SIZE = 512

BASE = Path(__file__).resolve().parent.parent

RAW = BASE / "data" / "satellite" / "raw"
PROCESSED = BASE / "data" / "satellite" / "processed"

PROCESSED.mkdir(parents=True, exist_ok=True)

images = sorted(RAW.glob("*.png"), key=lambda p: p.stat().st_mtime)

if not images:
    raise FileNotFoundError("Run fetch_satellite.py first.")

img_path = images[-1]

img = cv2.imread(str(img_path))
img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

mask = np.all(img < 10, axis=2)
img[mask] = [30,30,30]

img = cv2.resize(img,(SIZE,SIZE))
img = img.astype(np.float32)/255

np.save(PROCESSED/"latest.npy",img)

print("Processed:",img_path.name)