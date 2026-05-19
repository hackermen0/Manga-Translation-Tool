import os
import cv2


def convert_bw_masks_to_yolo_labels(masks_dir, output_labels_dir):
    """
    Scans the newly generated black-and-white mask images, finds their contours,
    and writes them out as normalized YOLOv8-seg polygon text files.
    """
    os.makedirs(output_labels_dir, exist_ok=True)

    # List all the generated mask files
    mask_files = [f for f in os.listdir(masks_dir) if f.endswith("_mask.png")]

    print(f"Converting {len(mask_files)} black-and-white masks to YOLOv8 segments...")

    for mask_file in mask_files:
        mask_path = os.path.join(masks_dir, mask_file)

        # Load the mask in grayscale
        mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
        img_h, img_w = mask.shape[:2]

        # Find structural contours of the white bubbles
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        yolo_lines = []
        for contour in contours:
            # Filter out tiny noise artifacts (less than 5 pixels)
            if len(contour) < 3:
                continue

            normalized_coords = []
            for point in contour:
                x, y = point[0]
                # Normalize values between 0.0 and 1.0
                nx = x / img_w
                ny = y / img_h
                normalized_coords.append(f"{nx:.6f} {ny:.6f}")

            # Class 0 represents 'balloon'
            yolo_lines.append(f"0 {' '.join(normalized_coords)}")

        # Match the text file name exactly to the original image base name
        # e.g., '001_mask.png' -> '001.txt'
        base_name = mask_file.replace("_mask.png", "")
        txt_output_path = os.path.join(output_labels_dir, f"{base_name}.txt")

        if yolo_lines:
            with open(txt_output_path, "w") as f:
                f.write("\n".join(yolo_lines))


if __name__ == "__main__":
    MASKS_DIR = r"C:\Users\KIIT\Documents\Coding Projects\Python projects\On-going Projects\Manga Translation Tool\Backend\New Speech Bubble Detection\Masks\UnbalanceTokyo"
    LABELS_DIR = r"C:\Users\KIIT\Documents\Coding Projects\Python projects\On-going Projects\Manga Translation Tool\Backend\New Speech Bubble Detection\Labels\UnbalanceTokyo"

    convert_bw_masks_to_yolo_labels(MASKS_DIR, LABELS_DIR)
