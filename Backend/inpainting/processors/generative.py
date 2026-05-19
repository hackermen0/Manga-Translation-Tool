import cv2
import numpy as np
from PIL import Image


class GenerativeProcessor:
    def __init__(
        self,
        mode: str = "opencv",
        model_id: str | None = None,
        device: str | None = None,
        prompt: str = "clean empty speech bubble, manga panel, no text",
        negative_prompt: str = "text, watermark, letters, logo",
        guidance_scale: float = 7.5,
        num_inference_steps: int = 30,
    ):
        """
        Initializes the AI inpainting model.
        mode:
            - "opencv": Fast Navier-Stokes fallback for development.
            - "stable_diffusion": Stable Diffusion inpainting via diffusers.
        """
        self.mode = mode
        self.model_id = model_id
        self.prompt = prompt
        self.negative_prompt = negative_prompt
        self.guidance_scale = guidance_scale
        self.num_inference_steps = num_inference_steps
        self.pipeline = None

        if self.mode == "stable_diffusion":
            if not self.model_id:
                raise ValueError(
                    "model_id is required when mode is set to 'stable_diffusion'."
                )
            import torch
            from diffusers import StableDiffusionInpaintPipeline

            resolved_device = (
                device if device is not None else ("cuda" if torch.cuda.is_available() else "cpu")
            )
            dtype = torch.float16 if resolved_device != "cpu" else torch.float32
            self.pipeline = StableDiffusionInpaintPipeline.from_pretrained(
                self.model_id, torch_dtype=dtype
            )
            self.pipeline = self.pipeline.to(resolved_device)
            self.pipeline.enable_attention_slicing()

    @staticmethod
    def _pad_to_multiple(image: np.ndarray, mask: np.ndarray, multiple: int = 8):
        height, width = image.shape[:2]
        padded_width = ((width + multiple - 1) // multiple) * multiple
        padded_height = ((height + multiple - 1) // multiple) * multiple
        if padded_width == width and padded_height == height:
            return image, mask, (width, height)

        pad_right = padded_width - width
        pad_bottom = padded_height - height
        padded_image = cv2.copyMakeBorder(
            image, 0, pad_bottom, 0, pad_right, cv2.BORDER_REFLECT_101
        )
        padded_mask = cv2.copyMakeBorder(
            mask, 0, pad_bottom, 0, pad_right, cv2.BORDER_CONSTANT, value=0
        )
        return padded_image, padded_mask, (width, height)

    def clean_complex_bubble(
        self, original_image: np.ndarray, bubble_mask: np.ndarray, bbox: dict
    ):
        """
        Uses AI to rebuild intricate artwork patterns underneath text footprints.
        """
        x1, y1, x2, y2 = bbox["x1"], bbox["y1"], bbox["x2"], bbox["y2"]

        crop_img = original_image[y1:y2, x1:x2]
        crop_mask = bubble_mask[y1:y2, x1:x2]

        if self.mode == "stable_diffusion":
            crop_mask = (crop_mask > 0).astype(np.uint8) * 255
            crop_rgb = cv2.cvtColor(crop_img, cv2.COLOR_BGR2RGB)
            padded_img, padded_mask, original_size = self._pad_to_multiple(
                crop_rgb, crop_mask
            )

            image_pil = Image.fromarray(padded_img)
            mask_pil = Image.fromarray(padded_mask).convert("L")

            result = self.pipeline(
                prompt=self.prompt,
                negative_prompt=self.negative_prompt,
                image=image_pil,
                mask_image=mask_pil,
                guidance_scale=self.guidance_scale,
                num_inference_steps=self.num_inference_steps,
            ).images[0]

            result_np = cv2.cvtColor(np.array(result), cv2.COLOR_RGB2BGR)
            target_w, target_h = original_size
            return result_np[:target_h, :target_w]

        # Fast Navier-Stokes fallback
        return cv2.inpaint(crop_img, crop_mask, 3, cv2.INPAINT_NS)
