import argparse
import importlib.util
from pathlib import Path

import cv2

from .cleaner import HybridMangaCleaner


def _load_detector_class():
    detector_path = (
        Path(__file__).resolve().parents[1] / "speech-bubble-detection" / "detector.py"
    )
    if not detector_path.exists():
        raise FileNotFoundError(
            f"Speech bubble detector not found at: {detector_path}"
        )

    spec = importlib.util.spec_from_file_location(
        "speech_bubble_detector", str(detector_path)
    )
    if spec is None or spec.loader is None:
        raise ImportError("Unable to load speech bubble detector module.")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.SpeechBubbleDetector


def run_pipeline(
    image_path: str,
    model_path: str,
    output_path: str | None = None,
    output_dir: str = "output",
    conf: float = 0.2,
    imgsz: int = 1024,
    variance_threshold: float = 8.0,
    fill_color: tuple[int, int, int] = (255, 255, 255),
    use_median_color: bool = False,
    generative_mode: str = "opencv",
    sd_model_id: str | None = None,
    device: str | None = None,
    prompt: str = "clean empty speech bubble, manga panel, no text",
    negative_prompt: str = "text, watermark, letters, logo",
    guidance_scale: float = 7.5,
    num_inference_steps: int = 30,
    save_debug: bool = False,
):
    image_path_obj = Path(image_path)
    if not image_path_obj.exists():
        raise FileNotFoundError(f"Input image not found at: {image_path}")

    Detector = _load_detector_class()
    detector = Detector(model_path)

    payload = detector.process_page(str(image_path_obj), conf=conf, imgsz=imgsz)

    cleaner = HybridMangaCleaner(
        variance_threshold=variance_threshold,
        fill_color=fill_color,
        use_median_color=use_median_color,
        generative_mode=generative_mode,
        sd_model_id=sd_model_id,
        device=device,
        prompt=prompt,
        negative_prompt=negative_prompt,
        guidance_scale=guidance_scale,
        num_inference_steps=num_inference_steps,
    )

    cleaned = cleaner.generate_clean_page(str(image_path_obj), payload["bubbles"])

    if output_path is None:
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)
        output_path = str(output_dir_path / f"{image_path_obj.stem}_cleaned.png")
    else:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    cv2.imwrite(output_path, cleaned)

    if save_debug:
        debug_dir = Path(output_path).parent
        cv2.imwrite(
            str(debug_dir / f"{image_path_obj.stem}_combined_mask.png"),
            payload["combined_mask"],
        )
        cv2.imwrite(
            str(debug_dir / f"{image_path_obj.stem}_annotated.png"),
            payload["annotated_img"],
        )

    return cleaned, payload, output_path


def _parse_color(value: str):
    parts = [int(part.strip()) for part in value.split(",") if part.strip()]
    if len(parts) != 3 or any(part < 0 or part > 255 for part in parts):
        raise argparse.ArgumentTypeError(
            "fill-color must be three comma-separated integers between 0 and 255."
        )
    return tuple(parts)


def _build_arg_parser():
    parser = argparse.ArgumentParser(
        description="Detect speech bubbles and inpaint text regions."
    )
    parser.add_argument("--image", required=True, help="Path to the input image.")
    parser.add_argument(
        "--model", required=True, help="Path to the YOLO bubble detector weights."
    )
    parser.add_argument("--output", help="Optional output path for the cleaned image.")
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Directory for outputs when --output is not provided.",
    )
    parser.add_argument("--conf", type=float, default=0.2, help="YOLO confidence.")
    parser.add_argument("--imgsz", type=int, default=1024, help="YOLO image size.")
    parser.add_argument(
        "--generative-mode",
        choices=["opencv", "stable_diffusion"],
        default="opencv",
        help="Inpainting backend for complex bubbles.",
    )
    parser.add_argument(
        "--sd-model-id",
        help="Stable Diffusion inpainting model ID or path.",
    )
    parser.add_argument(
        "--device", help="Device override for Stable Diffusion (e.g., cuda or cpu)."
    )
    parser.add_argument(
        "--fill-color",
        type=_parse_color,
        default=(255, 255, 255),
        help="RGB fill color for simple bubbles, e.g., 255,255,255.",
    )
    parser.add_argument(
        "--use-median-color",
        action="store_true",
        help="Use the bubble's median color instead of the fill color.",
    )
    parser.add_argument(
        "--save-debug",
        action="store_true",
        help="Save combined mask and annotated image.",
    )
    return parser


if __name__ == "__main__":
    args = _build_arg_parser().parse_args()
    run_pipeline(
        image_path=args.image,
        model_path=args.model,
        output_path=args.output,
        output_dir=args.output_dir,
        conf=args.conf,
        imgsz=args.imgsz,
        fill_color=args.fill_color,
        use_median_color=args.use_median_color,
        generative_mode=args.generative_mode,
        sd_model_id=args.sd_model_id,
        device=args.device,
        save_debug=args.save_debug,
    )
