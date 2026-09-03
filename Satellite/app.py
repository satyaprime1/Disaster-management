
from pathlib import Path
import tempfile

import h5py
import numpy as np
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

from sattelite_model.inference import predict_tile
from fastapi.responses import FileResponse
import matplotlib.pyplot as plt

app = FastAPI(title="Disaster AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {
        "status": "running",
        "model": "Landslide U-Net",
        "version": "1.0"
    }


@app.post("/predict-landslide")
async def predict_landslide(file: UploadFile = File(...)):

    with tempfile.NamedTemporaryFile(suffix=".h5", delete=False) as tmp:
        tmp.write(await file.read())
        temp_path = Path(tmp.name)

    pred = predict_tile(temp_path)

    with h5py.File(temp_path, "r") as f:
        rgb = f["img"][:, :, :3]

    plt.figure(figsize=(6,6))
    plt.imshow(rgb / rgb.max())
    plt.imshow(pred.numpy(), cmap="Reds", alpha=0.5)
    plt.axis("off")

    out = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    plt.savefig(out.name, bbox_inches="tight", pad_inches=0)
    plt.close()

    return FileResponse(out.name, media_type="image/png")