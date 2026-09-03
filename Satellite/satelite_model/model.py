import torch
import torch.nn as nn
import torch.nn.functional as F


# ============================================================
# RESIDUAL CONVOLUTION BLOCK
# ============================================================

class ResidualConv(nn.Module):
    def __init__(self, in_channels, out_channels, dropout=0.1):
        super().__init__()
        self.conv_block = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Dropout2d(dropout) if dropout > 0 else nn.Identity(),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
        )
        self.shortcut = nn.Sequential()
        if in_channels != out_channels:
            self.shortcut = nn.Sequential(
                nn.Conv2d(in_channels, out_channels, kernel_size=1, bias=False),
                nn.BatchNorm2d(out_channels),
            )
        self.relu = nn.ReLU(inplace=True)

    def forward(self, x):
        return self.relu(self.conv_block(x) + self.shortcut(x))


# ============================================================
# ATTENTION GATE
# ============================================================

class AttentionGate(nn.Module):
    def __init__(self, f_g, f_l, f_int):
        super().__init__()
        self.w_g = nn.Sequential(
            nn.Conv2d(f_g, f_int, kernel_size=1, stride=1, padding=0, bias=True),
            nn.BatchNorm2d(f_int)
        )
        self.w_x = nn.Sequential(
            nn.Conv2d(f_l, f_int, kernel_size=1, stride=1, padding=0, bias=True),
            nn.BatchNorm2d(f_int)
        )
        self.psi = nn.Sequential(
            nn.Conv2d(f_int, 1, kernel_size=1, stride=1, padding=0, bias=True),
            nn.BatchNorm2d(1),
            nn.Sigmoid()
        )
        self.relu = nn.ReLU(inplace=True)

    def forward(self, g, x):
        g1 = self.w_g(g)
        x1 = self.w_x(x)
        psi = self.relu(g1 + x1)
        psi = self.psi(psi)
        return x * psi


# ============================================================
# ATTENTION RES-UNET
# ============================================================

class UNet(nn.Module):
    def __init__(self, in_channels=14, out_channels=1, features=[32, 64, 128, 256]):
        super().__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels

        # Encoder
        self.e1 = ResidualConv(in_channels, features[0], dropout=0.05)
        self.p1 = nn.MaxPool2d(2, 2)

        self.e2 = ResidualConv(features[0], features[1], dropout=0.1)
        self.p2 = nn.MaxPool2d(2, 2)

        self.e3 = ResidualConv(features[1], features[2], dropout=0.1)
        self.p3 = nn.MaxPool2d(2, 2)

        self.e4 = ResidualConv(features[2], features[3], dropout=0.15)
        self.p4 = nn.MaxPool2d(2, 2)

        # Bottleneck
        self.bottleneck = ResidualConv(features[3], features[3] * 2, dropout=0.2)

        # Decoder & Attention Gates
        # Level 4
        self.up4 = nn.ConvTranspose2d(features[3] * 2, features[3], kernel_size=2, stride=2)
        self.att4 = AttentionGate(f_g=features[3], f_l=features[3], f_int=features[2])
        self.d4 = ResidualConv(features[3] * 2, features[3], dropout=0.15)

        # Level 3
        self.up3 = nn.ConvTranspose2d(features[3], features[2], kernel_size=2, stride=2)
        self.att3 = AttentionGate(f_g=features[2], f_l=features[2], f_int=features[1])
        self.d3 = ResidualConv(features[2] * 2, features[2], dropout=0.1)

        # Level 2
        self.up2 = nn.ConvTranspose2d(features[2], features[1], kernel_size=2, stride=2)
        self.att2 = AttentionGate(f_g=features[1], f_l=features[1], f_int=features[0])
        self.d2 = ResidualConv(features[1] * 2, features[1], dropout=0.1)

        # Level 1
        self.up1 = nn.ConvTranspose2d(features[1], features[0], kernel_size=2, stride=2)
        self.att1 = AttentionGate(f_g=features[0], f_l=features[0], f_int=features[0] // 2)
        self.d1 = ResidualConv(features[0] * 2, features[0], dropout=0.05)

        # Final Classifier
        self.final_conv = nn.Conv2d(features[0], out_channels, kernel_size=1)

    def forward(self, x):
        # Encoder
        s1 = self.e1(x)
        p1 = self.p1(s1)

        s2 = self.e2(p1)
        p2 = self.p2(s2)

        s3 = self.e3(p2)
        p3 = self.p3(s3)

        s4 = self.e4(p3)
        p4 = self.p4(s4)

        # Bottleneck
        b = self.bottleneck(p4)

        # Decoder
        d4 = self.up4(b)
        x4 = self.att4(g=d4, x=s4)
        d4 = torch.cat([x4, d4], dim=1)
        d4 = self.d4(d4)

        d3 = self.up3(d4)
        x3 = self.att3(g=d3, x=s3)
        d3 = torch.cat([x3, d3], dim=1)
        d3 = self.d3(d3)

        d2 = self.up2(d3)
        x2 = self.att2(g=d2, x=s2)
        d2 = torch.cat([x2, d2], dim=1)
        d2 = self.d2(d2)

        d1 = self.up1(d2)
        x1 = self.att1(g=d1, x=s1)
        d1 = torch.cat([x1, d1], dim=1)
        d1 = self.d1(d1)

        return self.final_conv(d1)


# Backwards compatibility alias
AttentionResUNet = UNet
