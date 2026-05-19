import os
import json
import numpy as np
import cv2
import pycocotools.mask as maskUtils


def generate_manga_mask_ground_truths(json_path, images_dir, output_masks_dir):
    """
    Generates binary mask ground truths (black background, white speech bubbles)
    from MangaSeg COCO JSON annotations, filtering for locally available Manga109-s images.
    """
    os.makedirs(output_masks_dir, exist_ok=True)

    print("Loading MangaSeg JSON annotations...")
    with open(json_path, "r") as f:
        coco_data = json.load(f)

    balloon_cat_ids = [
        cat["id"] for cat in coco_data["categories"] if cat["name"].lower() == "balloon"
    ]
    if not balloon_cat_ids:
        print("Error: 'balloon' category not found in the JSON annotations.")
        return
    balloon_cat_id = balloon_cat_ids[0]

    image_map = {img["id"]: img for img in coco_data["images"]}

    img_annotations = {}
    for ann in coco_data["annotations"]:
        if ann["category_id"] == balloon_cat_id:
            img_id = ann["image_id"]
            img_annotations.setdefault(img_id, []).append(ann)

    print("Processing pages and generating binary masks...")
    processed_count = 0
    skipped_count = 0

    for img_id, anns in img_annotations.items():
        img_meta = image_map.get(img_id)
        if not img_meta:
            continue

        file_name = img_meta["file_name"]

        # Pull just the clean image filename (e.g., '001.jpg') to map directly to the folder
        pure_file_name = os.path.basename(file_name)
        local_img_path = os.path.join(images_dir, pure_file_name)

        if not os.path.exists(local_img_path):
            skipped_count += 1
            continue

        img_w = img_meta["width"]
        img_h = img_meta["height"]

        binary_mask = np.zeros((img_h, img_w), dtype=np.uint8)

        for ann in anns:
            seg = ann["segmentation"]

            if isinstance(seg, dict):
                if isinstance(seg["counts"], list):
                    rle = maskUtils.frPyObjects(seg, img_h, img_w)
                else:
                    rle = seg

                decoded_mask = maskUtils.decode(rle)

                binary_mask = cv2.bitwise_or(
                    binary_mask, (decoded_mask * 255).astype(np.uint8)
                )

            else:
                for polygon in seg:
                    poly_points = np.array(polygon, dtype=np.int32).reshape((-1, 1, 2))
                    cv2.fillPoly(binary_mask, [poly_points], 255)

        base_name = os.path.splitext(pure_file_name)[0]
        output_file_name = f"{base_name}_mask.png"

        output_file_path = os.path.join(output_masks_dir, output_file_name)

        cv2.imwrite(output_file_path, binary_mask)
        processed_count += 1

    print("\n Mask Generation Complete!")
    print(f"Successfully generated masks: {processed_count}")
    print(f"Skipped missing books (non-s subset): {skipped_count}")


if __name__ == "__main__":
    JSON_PATH = r"C:\Users\KIIT\Documents\Coding Projects\Python projects\On-going Projects\Manga Translation Tool\Backend\New Speech Bubble Detection\JSON Datasets\UnbalanceTokyo.json"
    IMAGES_DIR = r"C:\Users\KIIT\Documents\Coding Projects\Python projects\On-going Projects\Manga Translation Tool\Backend\New Speech Bubble Detection\Manga\UnbalanceTokyo"
    OUTPUT_DIR = r"C:\Users\KIIT\Documents\Coding Projects\Python projects\On-going Projects\Manga Translation Tool\Backend\New Speech Bubble Detection\Masks\UnbalanceTokyo"

    generate_manga_mask_ground_truths(JSON_PATH, IMAGES_DIR, OUTPUT_DIR)
