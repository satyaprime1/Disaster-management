import torch
import torch.nn as nn
import torch.nn.functional as F


class FocalLoss(nn.Module):
    def __init__(self, alpha=0.75, gamma=2.0, reduction='mean'):
        super().__init__()
        self.alpha = alpha
        self.gamma = gamma
        self.reduction = reduction

    def forward(self, inputs, targets):
        bce_loss = F.binary_cross_entropy_with_logits(inputs, targets, reduction='none')
        pt = torch.exp(-bce_loss)
        alpha_t = self.alpha * targets + (1.0 - self.alpha) * (1.0 - targets)
        focal_loss = alpha_t * ((1.0 - pt) ** self.gamma) * bce_loss

        if self.reduction == 'mean':
            return focal_loss.mean()
        elif self.reduction == 'sum':
            return focal_loss.sum()
        return focal_loss


class TverskyLoss(nn.Module):
    def __init__(self, alpha=0.3, beta=0.7, smooth=1.0):
        super().__init__()
        self.alpha = alpha
        self.beta = beta
        self.smooth = smooth

    def forward(self, inputs, targets):
        probs = torch.sigmoid(inputs)
        
        probs = probs.view(-1)
        targets = targets.view(-1)
        
        tp = (probs * targets).sum()
        fp = (probs * (1.0 - targets)).sum()
        fn = ((1.0 - probs) * targets).sum()
        
        tversky = (tp + self.smooth) / (tp + self.alpha * fp + self.beta * fn + self.smooth)
        return 1.0 - tversky


class DiceBCELoss(nn.Module):
    def __init__(self, focal_weight=1.0, tversky_weight=1.5, alpha=0.3, beta=0.7, gamma=2.0):
        super().__init__()
        self.focal_weight = focal_weight
        self.tversky_weight = tversky_weight
        self.focal = FocalLoss(alpha=0.75, gamma=gamma)
        self.tversky = TverskyLoss(alpha=alpha, beta=beta)

    def forward(self, inputs, targets):
        focal_l = self.focal(inputs, targets)
        tversky_l = self.tversky(inputs, targets)
        return self.focal_weight * focal_l + self.tversky_weight * tversky_l
