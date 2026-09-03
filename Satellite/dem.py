from pathlib import Path
import elevation

OUT = Path(r"D:\Disaster-management\Backend\data\satellite\dem")
OUT.mkdir(parents=True, exist_ok=True)

dem_file = OUT / "hyderabad_dem.tif"

# Hyderabad area (same as Sentinel scene)
bounds = (78.30, 17.25, 78.60, 17.50)

print("Downloading DEM...")

elevation.clip(bounds=bounds, output=str(dem_file))

print("Saved:", dem_file)