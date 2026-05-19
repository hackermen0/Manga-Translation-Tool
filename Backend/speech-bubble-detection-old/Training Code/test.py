from ultralytics import YOLO
import cv2
import numpy as np
import os

model = YOLO("./Models/model.pt")

path = "./Mangas/YumeNoKayoiji"
output_path = f"{path}/Rough Masks"
os.makedirs(output_path, exist_ok=True)

for file in os.listdir(f"{path}/Manga Pages"):
    image_path = f"{path}/Manga Pages/{file}"
    img = cv2.imread(image_path)
    h, w = img.shape[:2]

    results = model(image_path, save=False, show=False)

    masks_obj = results[0].masks
    if masks_obj is None:
        print(f"⚠️ No detections in {file}, skipping.")
        continue

    # Combine masks
    masks = masks_obj.data.cpu().numpy()  # shape: (N, H', W') e.g. (640, 640)
    combined_mask = np.any(masks, axis=0).astype(np.uint8) * 255

    # Resize to original image size
    resized_mask = cv2.resize(combined_mask, (w, h), interpolation=cv2.INTER_NEAREST)

    # Save
    cv2.imwrite(f"{output_path}/{file}", resized_mask)
    print(f"✅ Saved resized mask for {file}")