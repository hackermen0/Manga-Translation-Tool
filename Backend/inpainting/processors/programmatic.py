import cv2
import numpy as np


class ProgrammaticProcessor:
    def __init__(
        self,
        variance_threshold: float = 8.0,
        fill_color: tuple[int, int, int] = (255, 255, 255),
        use_median_color: bool = False,
    ):
        """
        Args:
            variance_threshold: Sensitivity to texture. Lower values mean
                                stricter enforcement of pure solid colors.
            fill_color: Solid RGB color used when filling uniform bubbles.
            use_median_color: If True, use the bubble's detected background color instead of fill_color.
        """
        self.variance_threshold = variance_threshold
        self.fill_color = fill_color
        self.use_median_color = use_median_color

    def _detect_bubble_bg_color(
        self, crop_img: np.ndarray, crop_mask: np.ndarray
    ) -> tuple[int, int, int]:
        """
        Detect the background color of a bubble by sampling pixels near
        the inner edge of the mask boundary. This avoids text pixels that
        sit in the center and gives us the actual bubble fill color.
        """
        kernel = np.ones((7, 7), np.uint8)
        eroded = cv2.erode(crop_mask, kernel, iterations=3)
        border_ring = crop_mask.copy()
        border_ring[eroded > 0] = 0  

        border_pixels = crop_img[border_ring > 0]

        if len(border_pixels) > 10:
            color = np.median(border_pixels, axis=0).astype(int)
            return (int(color[0]), int(color[1]), int(color[2]))

        all_pixels = crop_img[crop_mask > 0]
        if len(all_pixels) > 0:
            color = np.median(all_pixels, axis=0).astype(int)
            return (int(color[0]), int(color[1]), int(color[2]))

        return self.fill_color

    def clean_solid_bubble(
        self, original_image: np.ndarray, bubble_mask: np.ndarray, bbox: dict
    ):
        """
        Attempts to fill the bubble programmatically if its background is a uniform color.
        Uses the border ring of the mask to evaluate uniformity (avoids text pixels).
        """
        x1, y1, x2, y2 = bbox["x1"], bbox["y1"], bbox["x2"], bbox["y2"]

        crop_img = original_image[y1:y2, x1:x2]
        crop_mask = bubble_mask[y1:y2, x1:x2]

        if crop_mask.sum() == 0:
            return None

        kernel = np.ones((7, 7), np.uint8)
        eroded = cv2.erode(crop_mask, kernel, iterations=3)
        border_ring = crop_mask.copy()
        border_ring[eroded > 0] = 0

        border_pixels = crop_img[border_ring > 0]

        if len(border_pixels) < 10:
            border_pixels = crop_img[crop_mask > 0]

        if len(border_pixels) == 0:
            return None

        gray_pixels = cv2.cvtColor(border_pixels.reshape(-1, 1, 3), cv2.COLOR_BGR2GRAY)
        std_dev = np.std(gray_pixels)

        if std_dev < self.variance_threshold:
            if self.use_median_color:
                fill_color = list(self._detect_bubble_bg_color(crop_img, crop_mask))
            else:
                fill_color = list(self.fill_color)

            cleaned_patch = crop_img.copy()
            cleaned_patch[crop_mask > 0] = fill_color
            return cleaned_patch

        return None
