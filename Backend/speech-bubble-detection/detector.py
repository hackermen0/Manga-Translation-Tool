import os
import cv2
import numpy as np
from ultralytics import YOLO
import json


class SpeechBubbleDetector:
    def __init__(self, model_path: str):
        """
        Initializes the YOLOv8 instance segmentation model once on boot to save VRAM.
        """
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model weights not found at: {model_path}")

        print(f"Initializing Production Speech Bubble Detector from {model_path}...")
        self.model = YOLO(model_path)

    def process_page(
        self, image_path: str, conf: float = 0.2, imgsz: int = 1024, erosion: int = 2
    ):
        """
        Runs bubble segmentation on a manga page and extracts structured mask tensors.

        Args:
            image_path: Absolute string path to the raw input page layout.
            conf: Prediction threshold (0.2 recommended to capture jagged action bubbles).
            imgsz: Network downscale training resolution.

        Returns:
            dict: Structured data dictionary containing:
                - "combined_mask": A flat 2D numpy array layout for global context inpainting.
                - "bubbles": A list of dicts for each bubble containing its 'id', 'bbox', 'mask', and 'area'.
                - "annotated_img": Debugging preview canvas.
        """
        image = cv2.imread(image_path)
        if image is None:
            raise FileNotFoundError(
                f"Could not read asset profile path at: {image_path}"
            )

        h, w = image.shape[:2]

        # Execute network feed-forward inference pass safely
        results = self.model.predict(
            source=image, imgsz=imgsz, conf=conf, verbose=False
        )[0]

        combined_mask = np.zeros((h, w), dtype=np.uint8)
        bubble_list = []
        bubble_boxes = []

        if results.masks is not None:
            # Step through matched bounding tracking segments simultaneously
            for i, (mask, box) in enumerate(zip(results.masks.data, results.boxes)):
                # Cast the low-res mask array back to full resolution scale
                mask_np = mask.cpu().numpy()
                mask_resized = cv2.resize(
                    mask_np, (w, h), interpolation=cv2.INTER_LINEAR
                )

                # Binarize floating point mask values into sharp pixel selections
                binary_mask = (mask_resized > 0.5).astype(np.uint8) * 255

                # Apply structural closure to fuse minor holes inside typography lines
                kernel = np.ones((5, 5), np.uint8)
                binary_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_CLOSE, kernel)
                binary_mask = cv2.erode(binary_mask, kernel, iterations=erosion)

                # Append clean frame array boundaries
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                bubble_boxes.append((x1, y1, x2, y2))

                # Fuse tracking element selection layers into a single reference matrix
                combined_mask = cv2.bitwise_or(combined_mask, binary_mask)

                bubble_list.append(
                    {
                        "bubble_id": i,
                        "bbox": {
                            "x1": int(x1),
                            "y1": int(y1),
                            "x2": int(x2),
                            "y2": int(y2),
                        },
                        "mask": binary_mask,
                        "area_px": int(np.sum(binary_mask > 0)),
                    }
                )

        # Generate a colored overlay canvas for system verification
        annotated_image = image.copy()
        overlay = image.copy()
        overlay[combined_mask > 0] = [
            0,
            120,
            255,
        ]  # Apply system default signature tint
        annotated_image = cv2.addWeighted(overlay, 0.4, annotated_image, 0.6, 0)

        # Draw debugging boundary rectangles
        for i, (x1, y1, x2, y2) in enumerate(bubble_boxes):
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

        return {
            "combined_mask": combined_mask,
            "bubbles": bubble_list,
            "annotated_img": annotated_image,
        }


# ==============================================================================
# Local Sandbox Execution Loop (Equivalent to script run logic)
# ==============================================================================
if __name__ == "__main__":
    from pathlib import Path

    MODEL_PATH = r"C:\Users\KIIT\Documents\Coding Projects\Python projects\On-going Projects\Manga Translation Tool\Backend\models\bubble_segmenter_best.pt"
    IMAGE_PATH = r"C:\Users\KIIT\Documents\Coding Projects\Python projects\On-going Projects\Manga Translation Tool\Backend\translation-pipeline\raw\103.jpg"
    OUTPUT_DIR = Path("output")
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Initialize the class system once
    detector = SpeechBubbleDetector(MODEL_PATH)

    # Process page logic using the verified 0.2 confidence baseline
    payload = detector.process_page(IMAGE_PATH, conf=0.2)

    # Extract structural components
    stem = Path(IMAGE_PATH).stem
    cv2.imwrite(str(OUTPUT_DIR / f"{stem}_combined_mask.png"), payload["combined_mask"])
    cv2.imwrite(str(OUTPUT_DIR / f"{stem}_annotated.png"), payload["annotated_img"])

    print(f"Processed {len(payload['bubbles'])} bubble segments successfully.")
    bubble_payload = [
        {key: val for key, val in bubble.items() if key != "mask"}
        for bubble in payload["bubbles"]
    ]

    print(bubble_payload)

    with open(rf"{OUTPUT_DIR}/bb_box_data.json", "w") as f:
        json.dump(bubble_payload, f)
