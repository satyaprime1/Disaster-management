from pathlib import Path
import random
import h5py
import numpy as np
import torch
from torch.utils.data import Dataset

# Global channel statistics for Landslide4Sense (14 channels)
DEFAULT_MEANS = np.array([
    0.9236, 0.9191, 0.9493, 0.9510, 1.0180, 1.0444, 1.0386, 
    1.0499, 1.1779, 1.1736, 1.0504, 1.0349, 1.2598, 1.6659
], dtype=np.float32)

DEFAULT_STDS = np.array([
    0.0600, 0.1296, 0.2197, 0.3908, 0.3348, 0.3294, 0.3390, 
    0.3742, 0.3434, 0.2057, 0.3930, 0.4859, 0.4438, 0.1616
], dtype=np.float32)


def normalize_channels(image, means=DEFAULT_MEANS, stds=DEFAULT_STDS):
    """
    Standardizes 14-channel satellite imagery using global dataset statistics.
    image shape: (14, H, W) or (C, H, W)
    """
    image = np.nan_to_num(image, nan=0.0, posinf=0.0, neginf=0.0)
    means_reshaped = means.reshape(-1, 1, 1)
    stds_reshaped = stds.reshape(-1, 1, 1)
    normalized = (image - means_reshaped) / (stds_reshaped + 1e-6)
    return np.clip(normalized, -5.0, 5.0).astype(np.float32)


class LandslideDataset(Dataset):
    def __init__(self, root, split="train", augment=False, preload=True, means=DEFAULT_MEANS, stds=DEFAULT_STDS):
        self.root = Path(root)
        self.split = split
        self.augment = augment
        self.means = means
        self.stds = stds
        self.preload = preload

        self.image_dir = self.root / "images" / split
        self.mask_dir = self.root / "annotations" / split

        if not self.image_dir.exists():
            raise FileNotFoundError(f"Image directory not found: {self.image_dir}")

        image_files = sorted(
            self.image_dir.glob("*.h5"),
            key=lambda p: self._number(p)
        )

        self.samples = []
        for img_path in image_files:
            num = self._number(img_path)
            mask_path = self.mask_dir / f"mask_{num}.h5"
            if mask_path.exists():
                self.samples.append((img_path, mask_path))

        print(f"[{split.upper()}] Found {len(self.samples)} sample pairs (preload={preload}, augment={augment}).", flush=True)

        if preload:
            print(f"[{split.upper()}] Preloading & standardizing samples into memory...", flush=True)
            img_list = []
            mask_list = []
            for img_p, mask_p in self.samples:
                img = self._read_h5(img_p, "img")
                mask = self._read_h5(mask_p, "mask")

                if img.ndim == 3 and img.shape[-1] <= 20:
                    img = np.transpose(img, (2, 0, 1))

                if mask.ndim == 3:
                    mask = mask[0] if mask.shape[0] == 1 else mask[..., 0]

                # Standardize immediately during preloading
                img_norm = normalize_channels(img, self.means, self.stds)
                img_list.append(torch.from_numpy(img_norm).float())
                mask_list.append(torch.from_numpy((mask > 0).astype(np.float32)).float().unsqueeze(0))

            self.images = torch.stack(img_list)
            self.masks = torch.stack(mask_list)
            print(f"[{split.upper()}] Memory cache ready: {self.images.shape[0]} tensors in RAM ({self.images.element_size() * self.images.nelement() / (1024**2):.1f} MB).", flush=True)

    @staticmethod
    def _number(path):
        try:
            return int(path.stem.split("_")[-1])
        except Exception:
            return 999999999

    def _read_h5(self, path, key_fallback=None):
        with h5py.File(path, "r") as f:
            keys = list(f.keys())
            if not keys:
                raise RuntimeError(f"No dataset in {path}")
            key = key_fallback if (key_fallback and key_fallback in f) else keys[0]
            data = f[key][:]
        return np.asarray(data, dtype=np.float32)

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, index):
        if self.preload:
            image = self.images[index]
            mask = self.masks[index]
        else:
            image_path, mask_path = self.samples[index]
            image = self._read_h5(image_path, "img")
            mask = self._read_h5(mask_path, "mask")

            if image.ndim == 3 and image.shape[-1] <= 20:
                image = np.transpose(image, (2, 0, 1))

            if mask.ndim == 3:
                mask = mask[0] if mask.shape[0] == 1 else mask[..., 0]

            image = torch.from_numpy(normalize_channels(image, self.means, self.stds)).float()
            mask = torch.from_numpy((mask > 0).astype(np.float32)).float().unsqueeze(0)

        # High-speed Torch tensor data augmentations
        if self.augment:
            if random.random() > 0.5:
                image = torch.flip(image, dims=[2])
                mask = torch.flip(mask, dims=[2])

            if random.random() > 0.5:
                image = torch.flip(image, dims=[1])
                mask = torch.flip(mask, dims=[1])

            k = random.randint(0, 3)
            if k > 0:
                image = torch.rot90(image, k=k, dims=[1, 2])
                mask = torch.rot90(mask, k=k, dims=[1, 2])

        return image, mask
