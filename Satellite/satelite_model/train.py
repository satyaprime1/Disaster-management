from pathlib import Path
import time
import json
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torch.amp import autocast, GradScaler

from dataset import LandslideDataset
from model import UNet
from losses import DiceBCELoss


def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    print()
    print("=" * 70, flush=True)
    print("HIGH-PERFORMANCE LANDSLIDE MODEL TRAINING (ATTENTION-RESUNET)", flush=True)
    print("=" * 70, flush=True)
    print(f"Device: {device}", flush=True)
    if device.type == "cuda":
        print(f"GPU: {torch.cuda.get_device_name(0)}", flush=True)

    dataset_root = Path(r"D:\DisasterData\landslide4sense")

    # Load Train and Validation sets with RAM preloading
    train_ds = LandslideDataset(dataset_root, split="train", augment=True, preload=True)
    val_ds = LandslideDataset(dataset_root, split="validation", augment=False, preload=True)

    batch_size = 32
    train_loader = DataLoader(
        train_ds,
        batch_size=batch_size,
        shuffle=True,
        num_workers=0,
        pin_memory=(device.type == "cuda")
    )

    val_loader = DataLoader(
        val_ds,
        batch_size=batch_size,
        shuffle=False,
        num_workers=0,
        pin_memory=(device.type == "cuda")
    )

    # Initialize Attention-ResUNet (14 channels)
    model = UNet(in_channels=14, out_channels=1).to(device)
    param_count = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Model parameters: {param_count:,}", flush=True)

    # Loss function & Optimizer
    criterion = DiceBCELoss(focal_weight=1.0, tversky_weight=1.5, alpha=0.3, beta=0.7)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)

    epochs = 35
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-5)

    use_amp = (device.type == "cuda")
    scaler = GradScaler("cuda", enabled=use_amp)

    checkpoint_dir = Path(__file__).parent / "checkpoints"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    best_model_path = checkpoint_dir / "best_model.pth"

    best_val_f1 = 0.0
    best_val_iou = 0.0

    print()
    print("=" * 70, flush=True)
    print(f"STARTING TRAINING ({epochs} EPOCHS)", flush=True)
    print("=" * 70, flush=True)

    for epoch in range(epochs):
        t0 = time.time()

        # Training Phase
        model.train()
        train_loss = 0.0
        train_tp, train_fp, train_fn = 0, 0, 0

        for images, masks in train_loader:
            images = images.to(device, non_blocking=True)
            masks = masks.to(device, non_blocking=True)

            optimizer.zero_grad(set_to_none=True)

            with autocast(device_type=device.type, enabled=use_amp):
                outputs = model(images)
                loss = criterion(outputs, masks)

            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()

            train_loss += loss.item()

            with torch.no_grad():
                probs = torch.sigmoid(outputs)
                preds = (probs > 0.5).float()
                train_tp += (preds * masks).sum().item()
                train_fp += (preds * (1.0 - masks)).sum().item()
                train_fn += ((1.0 - preds) * masks).sum().item()

        scheduler.step()
        train_loss /= len(train_loader)
        train_prec = (train_tp + 1e-6) / (train_tp + train_fp + 1e-6)
        train_rec = (train_tp + 1e-6) / (train_tp + train_fn + 1e-6)
        train_f1 = (2.0 * train_prec * train_rec) / (train_prec + train_rec + 1e-6)

        # Validation Phase
        model.eval()
        val_loss = 0.0
        val_tp, val_fp, val_fn, val_tn = 0, 0, 0, 0

        with torch.no_grad():
            for images, masks in val_loader:
                images = images.to(device, non_blocking=True)
                masks = masks.to(device, non_blocking=True)

                with autocast(device_type=device.type, enabled=use_amp):
                    outputs = model(images)
                    loss = criterion(outputs, masks)

                val_loss += loss.item()

                probs = torch.sigmoid(outputs)
                preds = (probs > 0.5).float()
                val_tp += (preds * masks).sum().item()
                val_fp += (preds * (1.0 - masks)).sum().item()
                val_fn += ((1.0 - preds) * masks).sum().item()
                val_tn += ((1.0 - preds) * (1.0 - masks)).sum().item()

        val_loss /= len(val_loader)
        val_prec = (val_tp + 1e-6) / (val_tp + val_fp + 1e-6)
        val_rec = (val_tp + 1e-6) / (val_tp + val_fn + 1e-6)
        val_f1 = (2.0 * val_prec * val_rec) / (val_prec + val_rec + 1e-6)
        val_iou = (val_tp + 1e-6) / (val_tp + val_fp + val_fn + 1e-6)

        elapsed = time.time() - t0
        lr = optimizer.param_groups[0]["lr"]

        print(
            f"Epoch [{epoch + 1:02d}/{epochs:02d}] ({elapsed:.1f}s, lr={lr:.1e}) | "
            f"Train Loss: {train_loss:.4f}, F1: {train_f1:.4f} | "
            f"Val Loss: {val_loss:.4f}, F1: {val_f1:.4f}, IoU: {val_iou:.4f}, Prec: {val_prec:.4f}, Rec: {val_rec:.4f}",
            flush=True
        )

        # Save Best Model Checkpoint
        if val_f1 > best_val_f1 or epoch == 0:
            if val_f1 > best_val_f1:
                best_val_f1 = val_f1
                best_val_iou = val_iou
                print(f"  [BEST MODEL] New Best Val F1: {best_val_f1:.4f} (IoU: {val_iou:.4f})", flush=True)
            torch.save(model.state_dict(), best_model_path)

    print()
    print("=" * 70, flush=True)
    print("TRAINING COMPLETED SUCCESSFULLY", flush=True)
    print("=" * 70, flush=True)
    print(f"Best Validation F1:  {best_val_f1:.4f}", flush=True)
    print(f"Best Validation IoU: {best_val_iou:.4f}", flush=True)
    print(f"Model Checkpoint:    {best_model_path}", flush=True)


if __name__ == "__main__":
    main()
