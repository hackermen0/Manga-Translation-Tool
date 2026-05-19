import json
import os
from PIL import Image
from collections import defaultdict
import numpy as np
from pycocotools import mask as maskUtils

# === Paths ===
json_path = "./Mangas/HinagikuKenzan/HinagikuKenzan.json"
image_dir = "./Mangas/HinagikuKenzan/Manga Pages"
output_mask_dir = "./Mangas/HinagikuKenzan/masks"

os.makedirs(output_mask_dir, exist_ok=True)

# === Load JSON ===
with open(json_path, "r") as f:
    data = json.load(f)

# Map image_id → image info
image_info = {img["id"]: img for img in data["images"]}

# Collect all balloon RLE segmentations per image
balloon_rles = defaultdict(list)

for ann in data["annotations"]:
    if ann["category_id"] == 5 and "segmentation" in ann:
        balloon_rles[ann["image_id"]].append(ann["segmentation"])

# Process each image
for image_id, rle_list in balloon_rles.items():
    info = image_info[image_id]
    file_name = info["file_name"]
    print(f"Processing: {file_name}")
    img_path = os.path.join(image_dir, os.path.basename(file_name))

    if not os.path.exists(img_path):
        print(f"❌ Missing image: {img_path}")
        continue

    # Load and save original image
    img = Image.open(img_path).convert("RGB")

    # Decode and merge RLE masks
    masks = [maskUtils.decode(rle) for rle in rle_list]
    if masks:
        combined = np.any(masks, axis=0).astype(np.uint8) * 255
        mask = Image.fromarray(combined)
        mask_name = file_name.replace('/', '__').replace('.jpg', '.png')
        mask.save(os.path.join(output_mask_dir, f"Mask_{mask_name}"))

print("✅ Done generating RLE-decoded balloon masks.")
