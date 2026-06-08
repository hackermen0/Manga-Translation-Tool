# manga_ocr_processor.py skeleton
from manga_ocr import MangaOcr
from PIL import Image
import cv2
import numpy as np


class MangaOCRProcessor:
    def __init__(self):
        self.mocr = MangaOcr()

    def extract_page_text(self, image_path, bubbles):
        """
        Args:
            image_path: original pre-inpainted page
            bubbles: bubble list from detector payload

        Returns:
            list of {bubble_id, bbox, text}
        """

        self.mocr
        ...

    def _crop_bubble(self, image, mask, bbox):
        """Crop + mask bubble region for clean OCR input."""
        ...
