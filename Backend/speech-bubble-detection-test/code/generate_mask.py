import cv2
import numpy as np
from ultralytics import YOLO
from pathlib import Path


def get_binary_masks(
    image_path: str, model_path: str, conf: float = 0.5, imgsz: int = 1024
):
    """
    Run bubble detection on a manga page and return binary masks.

    Args:
        image_path: Path to manga page image
        model_path: Path to your best.pt
        conf: Confidence threshold (0.5 recommended)
        imgsz: Inference image size (match training size)

    Returns:
        combined_mask: Single binary mask of all bubbles merged
        individual_masks: List of binary masks, one per detected bubble
        annotated_image: Original image with masks overlaid for visualization
    """

    model = YOLO(model_path)
    image = cv2.imread(image_path)
    h, w = image.shape[:2]

    # Run inference
    results = model.predict(source=image_path, imgsz=imgsz, conf=conf, verbose=False)[0]

    # Combined mask — all bubbles merged into one
    combined_mask = np.zeros((h, w), dtype=np.uint8)

    # Individual masks — one per bubble
    individual_masks = []
    bubble_boxes = []

    if results.masks is not None:
        for i, (mask, box) in enumerate(zip(results.masks.data, results.boxes)):
            # Resize mask from model output size back to original image size
            mask_np = mask.cpu().numpy()
            mask_resized = cv2.resize(mask_np, (w, h), interpolation=cv2.INTER_LINEAR)

            # Threshold to binary
            binary_mask = (mask_resized > 0.5).astype(np.uint8) * 255

            # Optional: morphological closing to fill small holes
            kernel = np.ones((5, 5), np.uint8)
            binary_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_CLOSE, kernel)

            individual_masks.append(binary_mask)
            bubble_boxes.append(box.xyxy[0].cpu().numpy().astype(int))

            # Add to combined mask
            combined_mask = cv2.bitwise_or(combined_mask, binary_mask)

    # Visualization — overlay masks on original image
    annotated_image = image.copy()
    overlay = image.copy()
    overlay[combined_mask > 0] = [0, 120, 255]  # orange tint on bubbles
    annotated_image = cv2.addWeighted(overlay, 0.4, annotated_image, 0.6, 0)

    # Draw bounding boxes
    for i, box in enumerate(bubble_boxes):
        x1, y1, x2, y2 = box
        cv2.rectangle(annotated_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(
            annotated_image,
            f"bubble_{i}",
            (x1, y1 - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            1,
        )

    return combined_mask, individual_masks, annotated_image, bubble_boxes


def save_masks(
    image_path: str, model_path: str, output_dir: str = "output", conf: float = 0.5
):
    """
    Run detection and save all mask outputs to disk.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)

    stem = Path(image_path).stem

    combined_mask, individual_masks, annotated_image, boxes = get_binary_masks(
        image_path, model_path, conf
    )

    combined_path = output_dir / f"{stem}_combined_mask.png"
    cv2.imwrite(str(combined_path), combined_mask)

    for i, mask in enumerate(individual_masks):
        mask_path = output_dir / f"{stem}_bubble_{i:03d}_mask.png"
        cv2.imwrite(str(mask_path), mask)

    viz_path = output_dir / f"{stem}_annotated.png"
    cv2.imwrite(str(viz_path), annotated_image)

    print(f"Detected {len(individual_masks)} bubbles")
    print(f"Combined mask  → {combined_path}")
    print(f"Individual masks → {output_dir}/{stem}_bubble_XXX_mask.png")
    print(f"Visualization  → {viz_path}")

    metadata = []
    for i, (mask, box) in enumerate(zip(individual_masks, boxes)):
        x1, y1, x2, y2 = box
        metadata.append(
            {
                "bubble_id": i,
                "bbox": {"x1": int(x1), "y1": int(y1), "x2": int(x2), "y2": int(y2)},
                "mask_path": str(output_dir / f"{stem}_bubble_{i:03d}_mask.png"),
                "area_px": int(np.sum(mask > 0)),
            }
        )

    return combined_mask, individual_masks, metadata


if __name__ == "__main__":
    MODEL_PATH = r"C:\Users\KIIT\Documents\Coding Projects\Python projects\On-going Projects\Manga Translation Tool\Backend\New Speech Bubble Detection\Models\best.pt"  # path to your trained model
    IMAGE_PATH = r"C:\Users\KIIT\Documents\Coding Projects\Python projects\On-going Projects\Manga Translation Tool\Backend\Translation-Pipeline\raw\112.jpg"  # any manga page

    combined, individuals, metadata = save_masks(
        image_path=IMAGE_PATH, model_path=MODEL_PATH, output_dir="output", conf=0.2
    )

    print("\nBubble metadata:")
    for b in metadata:
        print(f"  Bubble {b['bubble_id']}: bbox={b['bbox']}, area={b['area_px']}px")
