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
            bubble_id = bubble.get("bubble_id") if bubble.get("bubble_id") is not None else bubble.get("id")
            cropped_image = self._crop_bubble(original_image, bubble)
            ocr_result = self.extract_page_text(cropped_image, bubble_id)

            result = {"bubble_id": bubble_id, "bbox": bubble.get("bbox"), **ocr_result}
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
        from PIL import ImageDraw

        if "points" in bubble and len(bubble["points"]) >= 3:
            points = bubble["points"]
            x_coords = [p["x"] for p in points]
            y_coords = [p["y"] for p in points]

            mask = Image.new("L", original_image.size, 0)
            draw = ImageDraw.Draw(mask)
            polygon_pts = [(p["x"], p["y"]) for p in points]
            draw.polygon(polygon_pts, fill=255)

            white_bg = Image.new("RGB", original_image.size, (255, 255, 255))
            masked_image = Image.composite(original_image, white_bg, mask)

            padding = 5
            min_x = max(0, int(min(x_coords)) - padding)
            min_y = max(0, int(min(y_coords)) - padding)
            max_x = min(original_image.width, int(max(x_coords)) + padding)
            max_y = min(original_image.height, int(max(y_coords)) + padding)

            return masked_image.crop((min_x, min_y, max_x, max_y))

        bbox_data = bubble.get("bbox")
        if bbox_data:
            x1 = bbox_data["x1"]
            x2 = bbox_data["x2"]
            y1 = bbox_data["y1"]
            y2 = bbox_data["y2"]
            return original_image.crop((x1, y1, x2, y2))

        raise ValueError("Bubble payload does not contain 'points' or 'bbox' keys.")
