# manga_ocr_processor.py skeleton
from manga_ocr import MangaOcr
from PIL import Image
import cv2
import numpy as np


class MangaOCRProcessor:
    def __init__(self):
        self.mocr = MangaOcr()

    def extract_page_text(self, image: Image, bubble_id: int):
        """
        Args:
            image: original pre-inpainted page
            bubbles: bubble list from detector payload

        Returns:
            {bubble_id, text}
        """

        original_text = self.mocr(image)

        return bubble_id, original_text

    def _crop_bubble(self, image_path: str, bbox: list):
        """
        Crop + mask bubble region for clean OCR input.

        Args:
            image_path: original pre-inpainted page
            bbox: list of bounding box data of detected speech bubbles

        Returns:
            {bubble_id, cropped_image}


        """

        original_image = Image.open(image_path)

        for data in bbox:

            bubble_id = data["bubble_id"]
            bbox_data = data["bbox"]

            x1 = bbox_data["x1"]
            x2 = bbox_data["x2"]
            y1 = bbox_data["y1"]
            y2 = bbox_data["y2"]

            cropped_image = original_image.crop((x1, y1, x2, y2))

            return (bubble_id, cropped_image)
