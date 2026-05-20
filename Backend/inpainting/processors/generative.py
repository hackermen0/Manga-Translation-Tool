import cv2
import numpy as np
from PIL import Image


class GenerativeProcessor:
    def __init__(
        self,
        model_id_or_path: str,
        device: str | None = None,
        prompt: str | None = None,
        negative_prompt: str | None = None,
        guidance_scale: float = 7.5,
        num_inference_steps: int = 25,
        seed: int | None = None,
        padding: int = 16,
    ):
        """
        Initializes the Stable Diffusion inpainting pipeline with DirectML support.
        """
        if not model_id_or_path:
            raise ValueError(
                "model_id_or_path is required for Stable Diffusion inpainting."
            )

        import torch
        from diffusers import StableDiffusionInpaintPipeline

        self.torch = torch

        # Parse and prioritize the DirectML device string mapping
        requested_device = device or ("cuda" if torch.cuda.is_available() else "cpu")

        if requested_device == "dml":
            import torch_directml

            self.device = torch_directml.device()
            self.is_dml = True
            # DirectML requires float32 precision for model execution stability
            self.torch_dtype = torch.float32
            print(
                "Generative Inpainter running on AMD Hardware via DirectML Acceleration."
            )
        else:
            self.device = requested_device
            self.is_dml = False
            self.torch_dtype = torch.float16 if self.device == "cuda" else torch.float32
            print(f"Generative Inpainter running on device backend: {self.device}")

        self.pipe = StableDiffusionInpaintPipeline.from_pretrained(
            model_id_or_path, torch_dtype=self.torch_dtype
        )
        self.pipe = self.pipe.to(self.device)
        self.pipe.set_progress_bar_config(disable=True)

        if requested_device == "cpu":
            self.pipe.enable_attention_slicing()

        self.prompt = (
            prompt or "clean empty speech bubble, flat white background, no text"
        )
        self.negative_prompt = (
            negative_prompt or "text, letters, words, watermark, logo"
        )
        self.guidance_scale = guidance_scale
        self.num_inference_steps = num_inference_steps
        self.seed = seed
        self.padding = padding

    @staticmethod
    def _pad_to_multiple_of_eight(image: np.ndarray, mask: np.ndarray):
        height, width = image.shape[:2]
        pad_h = (8 - height % 8) % 8
        pad_w = (8 - width % 8) % 8
        if pad_h == 0 and pad_w == 0:
            return image, mask, height, width

        padded_image = cv2.copyMakeBorder(image, 0, pad_h, 0, pad_w, cv2.BORDER_REFLECT)
        padded_mask = cv2.copyMakeBorder(
            mask, 0, pad_h, 0, pad_w, cv2.BORDER_CONSTANT, value=0
        )
        return padded_image, padded_mask, height, width

    def _expand_bbox(self, bbox: dict, height: int, width: int):
        x1, y1, x2, y2 = bbox["x1"], bbox["y1"], bbox["x2"], bbox["y2"]
        pad = self.padding
        x1 = max(0, x1 - pad)
        y1 = max(0, y1 - pad)
        x2 = min(width, x2 + pad)
        y2 = min(height, y2 + pad)
        return x1, y1, x2, y2

    def clean_complex_bubble(
        self, original_image: np.ndarray, bubble_mask: np.ndarray, bbox: dict
    ):
        """
        Uses Stable Diffusion to rebuild intricate artwork patterns underneath text.
        """
        image_h, image_w = original_image.shape[:2]
        pad_x1, pad_y1, pad_x2, pad_y2 = self._expand_bbox(bbox, image_h, image_w)
        crop_img = original_image[pad_y1:pad_y2, pad_x1:pad_x2]
        crop_mask = bubble_mask[pad_y1:pad_y2, pad_x1:pad_x2]

        if crop_mask.max() == 0:
            x1, y1, x2, y2 = (
                bbox["x1"],
                bbox["y1"],
                bbox["x2"],
                bbox["y2"],
            )
            return original_image[y1:y2, x1:x2].copy()

        rgb_crop = cv2.cvtColor(crop_img, cv2.COLOR_BGR2RGB)
        mask_crop = (crop_mask > 0).astype(np.uint8) * 255
        rgb_crop, mask_crop, target_h, target_w = self._pad_to_multiple_of_eight(
            rgb_crop, mask_crop
        )

        pil_image = Image.fromarray(rgb_crop)
        pil_mask = Image.fromarray(mask_crop).convert("L")

        generator = None
        if self.seed is not None:
            # DirectML cannot declare random generation tensors directly inside its tracking spaces.
            # We explicitly target the CPU to compute seeds, which remains fully compatible with DML.
            gen_device = "cpu" if self.is_dml else self.device
            generator = self.torch.Generator(device=gen_device).manual_seed(self.seed)

        with self.torch.no_grad():
            result = self.pipe(
                prompt=self.prompt,
                negative_prompt=self.negative_prompt,
                image=pil_image,
                mask_image=pil_mask,
                guidance_scale=self.guidance_scale,
                num_inference_steps=self.num_inference_steps,
                generator=generator,
            ).images[0]

        result_np = cv2.cvtColor(np.array(result), cv2.COLOR_RGB2BGR)
        result_np = result_np[:target_h, :target_w]

        x1, y1, x2, y2 = bbox["x1"], bbox["y1"], bbox["x2"], bbox["y2"]
        offset_x = x1 - pad_x1
        offset_y = y1 - pad_y1
        target_h = y2 - y1
        target_w = x2 - x1
        return result_np[
            offset_y : offset_y + target_h, offset_x : offset_x + target_w
        ].copy()
