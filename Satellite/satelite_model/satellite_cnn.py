import torch
import torch.nn as nn
import torchvision.models as models

class SatelliteVision(nn.Module):

    def __init__(self):

        super().__init__()

        backbone=models.resnet18(weights=models.ResNet18_Weights.DEFAULT)

        self.encoder=nn.Sequential(*list(backbone.children())[:-1])

    def forward(self,x):

        x=self.encoder(x)

        return x.flatten(1)