import os
import cv2
import numpy as np
from ultralytics import YOLO


class SpeechBubbleDetector:
    def __init__(self, model_path: str):
        """
        Initializes the YOLOv8 segmentation model.
        Loading it inside the constructor ensures the weights are only loaded into memory
        ONCE when your FastAPI server starts, rather than on every single image request.
        """
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model weights not found at: {model_path}")

        print(f"Loading Speech Bubble Segmenter from {model_path}...")
        self.model = YOLO(model_path)

    def extract_bubble_masks(self, image_path: str, confidence_threshold: float = 0.25):
        """
        Processes a raw manga page and returns a binary mask image where
        speech bubbles are pure white (255) and everything else is black (0).
        """
        # Run YOLO inference
        # We keep confidence slightly lower (0.25) by default to catch those jagged/weird bubbles
        results = self.model.predict(
            source=image_path, conf=confidence_threshold, save=False
        )
        result = results[0]  # Grab the first result since we process one page at a time

        # Extract the original image dimensions (Height, Width)
        img_h, img_w = result.orig_img.shape[:2]

        # Initialize a pitch-black canvas matching the manga page size
        binary_mask = np.zeros((img_h, img_w), dtype=np.uint8)

        # If the model detected bubbles, draw them onto the blank canvas
        if result.masks is not None:
            # result.masks.xy contains the raw polygon coordinate loops
            for polygon_coords in result.masks.xy:
                # Format the coordinates into OpenCV's required integer array shape
                poly_points = np.array(polygon_coords, dtype=np.int32).reshape(
                    (-1, 1, 2)
                )

                # Fill the polygon shape with pure white (255)
                cv2.fillPoly(binary_mask, [poly_points], 255)

        return binary_mask


# ==========================================
# Quick Local Test Execution
# ==========================================
if __name__ == "__main__":
    # Point this to wherever you saved your downloaded Kaggle weights
    MODEL_WEIGHTS = r"C:\Users\KIIT\Documents\Coding Projects\Python projects\On-going Projects\Manga Translation Tool\Backend\models\bubble_segmenter_best.pt"
    TEST_IMAGE = (
        r"C:\Users\KIIT\Downloads\archive\Dataset\Validation\Images\Image_024.png"
    )

    # Initialize the detector
    detector = SpeechBubbleDetector(MODEL_WEIGHTS)

    # Generate the mask
    final_mask = detector.extract_bubble_masks(TEST_IMAGE)

    # Save the output to your local folder to visually verify it worked
    cv2.imwrite("test_output_mask.png", final_mask)
    print("Mask successfully generated and saved as 'test_output_mask.png'")
