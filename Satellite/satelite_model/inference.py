from pathlib import Path
import json
import numpy as np
import torch

from model import UNet
from dataset import normalize_channels

BASE_DIR = Path(__file__).resolve().parent
CHECKPOINT = BASE_DIR / "checkpoints" / "best_model.pth"

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

_model = None

def get_model():
    global _model
    if _model is None:
        model = UNet(in_channels=14, out_channels=1)
        state_dict = torch.load(CHECKPOINT, map_location=device)
        model.load_state_dict(state_dict)
        model.to(device)
        model.eval()
        _model = model
    return _model


def predict_tile(tile, threshold=0.5):
    """
    Runs landslide inference on a 14-channel tile.
    Input tile: numpy array of shape (14, 128, 128) or (128, 128, 14)
    Returns: binary prediction mask as torch tensor (128, 128) and probability map (128, 128)
    """
    model = get_model()

    if tile.ndim == 3 and tile.shape[-1] <= 20:
        tile = np.transpose(tile, (2, 0, 1))

    tile_norm = normalize_channels(tile)
    tensor = torch.from_numpy(tile_norm).float().unsqueeze(0).to(device)

    with torch.no_grad():
        output = model(tensor)
        prob = torch.sigmoid(output).squeeze().cpu().numpy()
        pred = (prob >= threshold).astype(np.float32)

    return torch.from_numpy(pred), prob
