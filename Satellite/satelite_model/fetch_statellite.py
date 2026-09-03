from pathlib import Path
from datetime import datetime, UTC, timedelta
import requests

BASE = Path(__file__).resolve().parent.parent
RAW = BASE / "data" / "satellite" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

DATE = (datetime.now(UTC) - timedelta(days=1)).strftime("%Y-%m-%d")

URL = "https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi"

params = {
    "SERVICE": "WMS",
    "REQUEST": "GetMap",
    "VERSION": "1.1.1",
    "LAYERS": "MODIS_Terra_CorrectedReflectance_TrueColor",
    "STYLES": "",
    "FORMAT": "image/png",
    "SRS": "EPSG:4326",
    "BBOX": "60,-5,100,40",
    "WIDTH": 2048,
    "HEIGHT": 2048,
    "TIME": DATE,
}

r = requests.get(URL, params=params, timeout=60)
r.raise_for_status()

filename = RAW / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

filename.write_bytes(r.content)

print("Saved:", filename)