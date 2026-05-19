import matplotlib.pyplot as plt
import torch
import numpy as np
from Model import UNet
from DatasetLoader import MangaBubbleDataset
from torchvision import transforms
from torch.utils.data import DataLoader

# ---------- Transform ----------
transform = transforms.Compose([
    transforms.Resize((512, 512)),
    transforms.ToTensor()
])

# ---------- Load Dataset ----------
dataset = MangaBubbleDataset("./Validation/Images", "./Validation/Masks", transform=transform)
dataloader = DataLoader(dataset, batch_size=1, shuffle=False)

# ---------- Load Model ----------
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = UNet().to(device)
model.load_state_dict(torch.load("./Models/model.pt", map_location=device))
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
        if i < 7:
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
