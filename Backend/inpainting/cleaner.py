# cleaner.py
import cv2
import numpy as np
from .processors.programmatic import ProgrammaticProcessor
from .processors.generative import GenerativeProcessor


class HybridMangaCleaner:
    def __init__(
        self,
        variance_threshold: float = 8.0,
        programmatic_fill_color: tuple[int, int, int] | None = (255, 255, 255),
        generative_model_id_or_path: str | None = None,
        generative_device: str | None = None,
        generative_prompt: str | None = None,
        generative_negative_prompt: str | None = None,
        generative_guidance_scale: float = 7.5,
        generative_steps: int = 25,
        generative_seed: int | None = None,
        generative_padding: int = 16,
        generative_engine: GenerativeProcessor | None = None,
    ):
        self.programmatic_engine = ProgrammaticProcessor(
            variance_threshold=variance_threshold,
            fill_color=programmatic_fill_color,
        )

        # SD is now fully optional — None means white fill handles everything
        if generative_engine is not None:
            self.generative_engine = generative_engine
        elif (
            generative_model_id_or_path is not None
            and generative_model_id_or_path.lower() != "none"
        ):
            self.generative_engine = GenerativeProcessor(
                model_id_or_path=generative_model_id_or_path,
                device=generative_device,
                prompt=generative_prompt,
                negative_prompt=generative_negative_prompt,
                guidance_scale=generative_guidance_scale,
                num_inference_steps=generative_steps,
                seed=generative_seed,
                padding=generative_padding,
            )
        else:
            self.generative_engine = None

    def generate_clean_page(self, image_path: str, bubble_metadata: list):
        master_canvas = cv2.imread(image_path)
        if master_canvas is None:
            raise FileNotFoundError(f"Could not load image canvas at: {image_path}")

        stats = {"programmatic": 0, "generative": 0, "fallback_fill": 0}

        for bubble in bubble_metadata:
            bbox = bubble["bbox"]
            mask = bubble["mask"]
            x1, y1, x2, y2 = bbox["x1"], bbox["y1"], bbox["x2"], bbox["y2"]

            # Always try programmatic first
            clean_patch = self.programmatic_engine.clean_solid_bubble(
                master_canvas, mask, bbox
            )

            if clean_patch is not None:
                master_canvas[y1:y2, x1:x2] = clean_patch
                stats["programmatic"] += 1

            elif self.generative_engine is not None:
                # SD inpainting only if model is loaded
                clean_patch = self.generative_engine.clean_complex_bubble(
                    master_canvas, mask, bbox
                )
                master_canvas[y1:y2, x1:x2] = clean_patch
                stats["generative"] += 1

            else:
                # Hard fallback — white fill the masked region directly
                master_canvas[mask > 0] = (255, 255, 255)
                stats["fallback_fill"] += 1

        print(
            f"Erasure complete — "
            f"Programmatic: {stats['programmatic']} | "
            f"Generative: {stats['generative']} | "
            f"Fallback fill: {stats['fallback_fill']}"
        )
        return master_canvas
