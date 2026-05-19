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
            use_median_color: If True, use the bubble's median color instead of fill_color.
        """
        self.variance_threshold = variance_threshold
        self.fill_color = fill_color
        self.use_median_color = use_median_color

    def clean_solid_bubble(
        self, original_image: np.ndarray, bubble_mask: np.ndarray, bbox: dict
    ):
        """
        Attempts to fill the bubble programmatically if its background is a uniform color.
        """
        x1, y1, x2, y2 = bbox["x1"], bbox["y1"], bbox["x2"], bbox["y2"]

        # Crop the localized area to evaluate inner properties
        crop_img = original_image[y1:y2, x1:x2]
        crop_mask = bubble_mask[y1:y2, x1:x2]

        # Extract pixels that sit strictly within the interior boundary
        bubble_pixels = crop_img[crop_mask > 0]

        if len(bubble_pixels) == 0:
            return None

        # Convert exclusively to grayscale to measure texture uniformity
        gray_pixels = cv2.cvtColor(bubble_pixels.reshape(-1, 1, 3), cv2.COLOR_BGR2GRAY)
        std_dev = np.std(gray_pixels)

        # If texture fluctuation is below threshold, it's a flat color
        if std_dev < self.variance_threshold:
            if self.use_median_color:
                fill_color = np.median(bubble_pixels, axis=0).astype(int).tolist()
            else:
                fill_color = list(self.fill_color)

            # Create a localized clean patch
            cleaned_patch = crop_img.copy()
            cleaned_patch[crop_mask > 0] = fill_color
            return cleaned_patch

        return None  # Too structurally complex, needs generative AI
