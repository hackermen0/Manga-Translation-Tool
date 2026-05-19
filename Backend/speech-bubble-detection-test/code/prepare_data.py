import os
import json
import numpy as np
import cv2
import pycocotools.mask as maskUtils


def process_single_manga_dataset(json_path, images_dir, masks_dir, labels_dir):
    """
    Processes a single manga dataset: parses the COCO JSON, checks local images,
    generates black-and-white mask files, and extracts normalized YOLO segmentation labels.
    """
    os.makedirs(masks_dir, exist_ok=True)
    os.makedirs(labels_dir, exist_ok=True)

    print(f"Reading configuration boundaries from: {os.path.basename(json_path)}")
    with open(json_path, "r") as f:
        coco_data = json.load(f)

    balloon_cat_ids = [
        cat["id"] for cat in coco_data["categories"] if cat["name"].lower() == "balloon"
    ]
    if not balloon_cat_ids:
        print(
            f"Skipping: 'balloon' category missing from {os.path.basename(json_path)}"
        )
        return
    balloon_cat_id = balloon_cat_ids[0]

    image_map = {img["id"]: img for img in coco_data["images"]}

    img_annotations = {}
    for ann in coco_data["annotations"]:
        if ann["category_id"] == balloon_cat_id:
            img_id = ann["image_id"]
            img_annotations.setdefault(img_id, []).append(ann)

    processed_count = 0
    skipped_count = 0

    for img_id, anns in img_annotations.items():
        img_meta = image_map.get(img_id)
        if not img_meta:
            continue

        file_name = img_meta["file_name"]
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

        mask_file_name = f"{base_name}_mask.png"
        mask_output_path = os.path.join(masks_dir, mask_file_name)
        cv2.imwrite(mask_output_path, binary_mask)

        contours, _ = cv2.findContours(
            binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        yolo_lines = []
        for contour in contours:
            if len(contour) < 3:
                continue

            normalized_coords = []
            for point in contour:
                pt_x, pt_y = point[0]
                nx = pt_x / img_w
                ny = pt_y / img_h
                normalized_coords.append(f"{nx:.6f} {ny:.6f}")

            yolo_lines.append(f"0 {' '.join(normalized_coords)}")

        if yolo_lines:
            txt_file_name = f"{base_name}.txt"
            txt_output_path = os.path.join(labels_dir, txt_file_name)
            with open(txt_output_path, "w") as label_file:
                label_file.write("\n".join(yolo_lines))

        processed_count += 1

    print(
        f"Successfully processed pages: {processed_count} | Skipped missing: {skipped_count}\n"
    )


def run_main_pipeline(base_workspace_dir):
    """
    Dispatches mapping routines across all available dataset json indexes detected.
    """
    json_datasets_dir = os.path.normpath(
        os.path.join(base_workspace_dir, "JSON Datasets")
    )
    manga_base_dir = os.path.normpath(os.path.join(base_workspace_dir, "Manga"))
    masks_base_dir = os.path.normpath(os.path.join(base_workspace_dir, "Masks"))
    labels_base_dir = os.path.normpath(os.path.join(base_workspace_dir, "Labels"))

    if not os.path.exists(json_datasets_dir):
        print(
            f"Error: Dataset configuration root folder not found at: {json_datasets_dir}"
        )
        print(
            "Please ensure your WORKSPACE_ROOT points directly to the 'New Speech Bubble Detection' folder."
        )
        return

    json_files = [f for f in os.listdir(json_datasets_dir) if f.endswith(".json")]
    print(
        f"Discovered {len(json_files)} distinct volume configurations to map out...\n"
    )

    for json_file in json_files:
        manga_name = os.path.splitext(json_file)[0]

        # Define target path for the specific manga label output folder
        target_labels_dir = os.path.join(labels_base_dir, manga_name)

        # Check if the folder already exists in the Labels directory
        if os.path.exists(target_labels_dir):
            print(
                f"Skipping complete folder generation: '{manga_name}' labels already exist."
            )
            continue

        print(f"=== Beginning Aggregation for: {manga_name} ===")

        target_json_path = os.path.join(json_datasets_dir, json_file)
        target_images_dir = os.path.join(manga_base_dir, manga_name)
        target_masks_dir = os.path.join(masks_base_dir, manga_name)

        if not os.path.exists(target_images_dir):
            print(
                f"Warning: Raw image subfolder missing for '{manga_name}'. Skipping bundle verification.\n"
            )
            continue

        process_single_manga_dataset(
            json_path=target_json_path,
            images_dir=target_images_dir,
            masks_dir=target_masks_dir,
            labels_dir=target_labels_dir,
        )

    print("=== Master Data Generation Pipeline Complete ===")


if __name__ == "__main__":

    CURRENT_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

    WORKSPACE_ROOT = r"C:\Users\KIIT\Documents\Coding Projects\Python projects\On-going Projects\Manga Translation Tool\Backend\New Speech Bubble Detection"

    run_main_pipeline(os.path.normpath(WORKSPACE_ROOT))
