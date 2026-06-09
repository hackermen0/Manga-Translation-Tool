from __future__ import annotations

from typing import Any

from PIL import Image

try:
    from manga_ocr import MangaOcr
except ImportError:
    MangaOcr = None


class MangaOCRProcessor:
    def __init__(self):
        if MangaOcr is None:
            raise ImportError(
                "manga_ocr is required to use MangaOCRProcessor. Install the 'manga-ocr' package first."
            )

        self.mocr = MangaOcr()

    def extract_page_text(self, image: Image.Image, bubble_id: int):
        """
        Args:
            image: cropped speech bubble image
            bubble_id: detected bubble identifier

        Returns:
            Dictionary containing the bubble id and OCR text.
        """

        original_text = self.mocr(image)

        return {"bubble_id": bubble_id, "original_text": original_text}

    def extract_page_texts(self, image_path: str, bubbles: list[dict[str, Any]]):
        """
        Run OCR for every detected bubble on a page.

        Args:
            image_path: path to the original manga page.
            bubbles: list of bubble payloads with bubble_id and bbox data.

        Returns:
            List of serializable OCR result dictionaries.
        """

        original_image = Image.open(image_path).convert("RGB")
        results = []

        for bubble in bubbles:
            bubble_id = bubble["bubble_id"]
            cropped_image = self._crop_bubble(original_image, bubble)
            ocr_result = self.extract_page_text(cropped_image, bubble_id)

            result = {"bubble_id": bubble_id, "bbox": bubble["bbox"], **ocr_result}
            if "area_px" in bubble:
                result["area_px"] = bubble["area_px"]
            if "mask_path" in bubble:
                result["mask_path"] = bubble["mask_path"]

            results.append(result)

        return results

    def _crop_bubble(self, original_image: Image.Image, bubble: dict[str, Any]):
        """
        Crop + mask bubble region for clean OCR input.

        Args:
            original_image: original manga page image.
            bubble: detected speech bubble payload.

        Returns:
            Cropped bubble image.
        """

        bbox_data = bubble["bbox"]
        x1 = bbox_data["x1"]
        x2 = bbox_data["x2"]
        y1 = bbox_data["y1"]
        y2 = bbox_data["y2"]

        return original_image.crop((x1, y1, x2, y2))
