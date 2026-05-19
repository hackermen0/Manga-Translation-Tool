#Evaluation Script

import matplotlib.pyplot as plt
import torch
import numpy as np
from torchvision import transforms
import torch.nn as nn
import torch.nn.functional as F
import segmentation_models_pytorch as smp
from torch.utils.data import DataLoader, Dataset
import os


class MangaBubbleDataset(Dataset):
    def __init__(self, image_dir, mask_dir, transform=None):
        self.image_dir = image_dir
        self.mask_dir = mask_dir
        self.images = sorted(os.listdir(image_dir))
        self.transform = transform

    def __getitem__(self, idx):
        image_filename = self.images[idx]
        image_path = os.path.join(self.image_dir, image_filename)

        index = image_filename.split('_')[1].split('.')[0]
        mask_filename = f"Mask_{index}.png"
        mask_path = os.path.join(self.mask_dir, mask_filename)

        image = Image.open(image_path).convert("RGB")
        mask = Image.open(mask_path).convert("L")

        if self.transform:
            image = self.transform(image)
            mask = self.transform(mask)
            mask = (mask > 0).float()

        return image, mask

    def __len__(self):
        return len(self.images)


class DoubleConv(nn.Module):
    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, 3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, 3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True)
        )

    def forward(self, x):
        return self.block(x)

class UNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.enc1 = DoubleConv(3, 64)
        self.enc2 = DoubleConv(64, 128)
        self.enc3 = DoubleConv(128, 256)
        self.enc4 = DoubleConv(256, 512)

        self.pool = nn.MaxPool2d(2)

        self.bottleneck = DoubleConv(512, 1024)

        self.up4 = nn.ConvTranspose2d(1024, 512, 2, stride=2)
        self.dec4 = DoubleConv(1024, 512)

        self.up3 = nn.ConvTranspose2d(512, 256, 2, stride=2)
        self.dec3 = DoubleConv(512, 256)

        self.up2 = nn.ConvTranspose2d(256, 128, 2, stride=2)
        self.dec2 = DoubleConv(256, 128)

        self.up1 = nn.ConvTranspose2d(128, 64, 2, stride=2)
        self.dec1 = DoubleConv(128, 64)

        self.out_conv = nn.Conv2d(64, 1, kernel_size=1)

    def forward(self, x):
        e1 = self.enc1(x)
        e2 = self.enc2(self.pool(e1))
        e3 = self.enc3(self.pool(e2))
        e4 = self.enc4(self.pool(e3))

        b = self.bottleneck(self.pool(e4))

        d4 = self.dec4(torch.cat([self.up4(b), e4], dim=1))
        d3 = self.dec3(torch.cat([self.up3(d4), e3], dim=1))
        d2 = self.dec2(torch.cat([self.up2(d3), e2], dim=1))
        d1 = self.dec1(torch.cat([self.up1(d2), e1], dim=1))

        return self.out_conv(d1)


# ---------- Transform ----------
transform = transforms.Compose([
    transforms.Resize((768, 768)),
    transforms.ToTensor()
])

# ---------- Load Dataset ----------
dataset_name = "Validation"
dataset = MangaBubbleDataset(f"/kaggle/input/speech-bubble-masks/Dataset/{dataset_name}/Images", f"/kaggle/input/speech-bubble-masks/Dataset/{dataset_name}/Masks", transform=transform)
dataloader = DataLoader(dataset, batch_size=1, shuffle=False)

# ---------- Load Model ----------
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = smp.Unet(
    encoder_name="resnet34",        
    encoder_weights="imagenet",
    in_channels=3,
    classes=1
).to(device)
model.load_state_dict(torch.load("/kaggle/working/unet_speech_bubbles.pth", map_location=device))
model.eval()

# ---------- Metric Functions ----------
def compute_iou(pred, target):
    pred = (pred > 0.5).float()
    target = (target > 0.5).float()
    intersection = (pred * target).sum()
    union = ((pred + target) > 0).float().sum()
    return (intersection / (union + 1e-6)).item()

def compute_dice(pred, target):
    pred = (pred > 0.5).float()
    target = (target > 0.5).float()
    intersection = (pred * target).sum()
    return (2 * intersection / (pred.sum() + target.sum() + 1e-6)).item()

# ---------- Evaluate ----------
ious = []
dices = []

with torch.no_grad():
    for i, (img, mask) in enumerate(dataloader):
        img, mask = img.to(device), mask.to(device)

        pred = model(img)
        pred_sigmoid = torch.sigmoid(pred)

        iou = compute_iou(pred_sigmoid, mask)
        dice = compute_dice(pred_sigmoid, mask)
        ious.append(iou)
        dices.append(dice)

        # Optional: Plot first 3 results
        if i < 12:
            plt.figure(figsize=(12, 4))

            plt.subplot(1, 3, 1)
            plt.imshow(img[0].permute(1, 2, 0).cpu())
            plt.title("Original Image")

            plt.subplot(1, 3, 2)
            plt.imshow(mask[0][0].cpu(), cmap="gray")
            plt.title("Ground Truth")

            plt.subplot(1, 3, 3)
            plt.imshow(pred_sigmoid[0][0].cpu() > 0.5, cmap="gray")
            plt.title("Prediction")

            plt.show()

# ---------- Final Scores ----------
print(f"\n📊 Evaluation Results on {len(dataset)} images:")
print(f"➡ Average IoU: {np.mean(ious):.4f}")
print(f"➡ Average Dice: {np.mean(dices):.4f}")