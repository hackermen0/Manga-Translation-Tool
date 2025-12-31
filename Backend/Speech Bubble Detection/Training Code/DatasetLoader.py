from torch.utils.data import Dataset
from torchvision import transforms
from PIL import Image
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
