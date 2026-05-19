from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any

import cv2

from cleaner import HybridMangaCleaner

_DETECTOR_CLASS: type | None = None


def _get_detector_class():
    global _DETECTOR_CLASS
    if _DETECTOR_CLASS is not None:
        return _DETECTOR_CLASS

    backend_dir = Path(__file__).resolve().parents[1]
    detector_path = backend_dir / "speech-bubble-detection" / "detector.py"
    if not detector_path.exists():
        raise FileNotFoundError(f"Speech bubble detector not found at: {detector_path}")

    spec = importlib.util.spec_from_file_location(
        "speech_bubble_detector", detector_path
    )
    if spec is None or spec.loader is None:
        raise ImportError("Unable to load the speech bubble detector module.")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if not hasattr(module, "SpeechBubbleDetector"):
        raise ImportError("SpeechBubbleDetector class not found in detector module.")

    _DETECTOR_CLASS = module.SpeechBubbleDetector
    return _DETECTOR_CLASS


def _ensure_dir(path: str | Path | None):
    if path is None:
        return None
    output_dir = Path(path)
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def _save_detection_artifacts(output_dir: Path, stem: str, payload: dict[str, Any]):
    combined_mask_path = output_dir / f"{stem}_combined_mask.png"
    annotated_path = output_dir / f"{stem}_annotated.png"
    mask_dir = output_dir / "bubble_masks"
    mask_dir.mkdir(parents=True, exist_ok=True)

    cv2.imwrite(str(combined_mask_path), payload["combined_mask"])
    cv2.imwrite(str(annotated_path), payload["annotated_img"])

    mask_paths: dict[int, Path] = {}
    for bubble in payload["bubbles"]:
        bubble_id = bubble["bubble_id"]
        mask_path = mask_dir / f"{stem}_bubble_{bubble_id:03d}_mask.png"
        cv2.imwrite(str(mask_path), bubble["mask"])
        mask_paths[bubble_id] = mask_path

    metadata = []
    for bubble in payload["bubbles"]:
        bubble_id = bubble["bubble_id"]
        metadata.append(
            {
                "bubble_id": bubble_id,
                "bbox": bubble["bbox"],
                "mask_path": str(mask_paths.get(bubble_id, "")),
                "area_px": bubble.get("area_px", 0),
            }
        )

    metadata_path = output_dir / f"{stem}_bubble_metadata.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    return {
        "combined_mask": combined_mask_path,
        "annotated": annotated_path,
        "metadata": metadata_path,
        "mask_dir": mask_dir,
    }


def load_bubble_metadata(metadata_path: str | Path):
    metadata_path = Path(metadata_path)
    if not metadata_path.exists():
        raise FileNotFoundError(f"Bubble metadata not found at: {metadata_path}")

    with open(metadata_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    bubbles = []
    for bubble in data:
        mask_path = Path(bubble["mask_path"])
        if not mask_path.is_absolute():
            mask_path = metadata_path.parent / mask_path
        if not mask_path.exists():
            raise FileNotFoundError(f"Bubble mask not found at: {mask_path}")
        mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
        if mask is None:
            raise FileNotFoundError(f"Unable to read bubble mask at: {mask_path}")

        bubble_payload = {
            "bubble_id": bubble["bubble_id"],
            "bbox": bubble["bbox"],
            "mask": mask,
            "area_px": bubble.get("area_px", int((mask > 0).sum())),
        }
        bubbles.append(bubble_payload)

    return bubbles


class SpeechBubbleInpaintingPipeline:
    def __init__(
        self,
        detector_model_path: str,
        inpaint_model_id_or_path: str,
        conf: float = 0.2,
        imgsz: int = 1024,
        variance_threshold: float = 8.0,
        programmatic_fill_color: tuple[int, int, int] | None = (255, 255, 255),
        generative_device: str | None = None,
        generative_prompt: str | None = None,
        generative_negative_prompt: str | None = None,
        generative_guidance_scale: float = 7.5,
        generative_steps: int = 25,
        generative_seed: int | None = None,
        generative_padding: int = 16,
        detector: Any | None = None,
        cleaner: HybridMangaCleaner | None = None,
    ):
        if detector is None:
            detector_class = _get_detector_class()
            detector = detector_class(detector_model_path)

        if cleaner is None:
            cleaner = HybridMangaCleaner(
                variance_threshold=variance_threshold,
                programmatic_fill_color=programmatic_fill_color,
                generative_model_id_or_path=inpaint_model_id_or_path,
                generative_device=generative_device,
                generative_prompt=generative_prompt,
                generative_negative_prompt=generative_negative_prompt,
                generative_guidance_scale=generative_guidance_scale,
                generative_steps=generative_steps,
                generative_seed=generative_seed,
                generative_padding=generative_padding,
            )

        self.detector = detector
        self.cleaner = cleaner
        self.conf = conf
        self.imgsz = imgsz

    def run(
        self,
        image_path: str,
        output_dir: str | Path | None = "output",
        save_artifacts: bool = True,
        save_cleaned: bool = True,
    ):
        payload = self.detector.process_page(
            image_path=image_path, conf=self.conf, imgsz=self.imgsz
        )

        stem = Path(image_path).stem
        saved_paths = {}
        output_dir = _ensure_dir(output_dir)
        if output_dir and save_artifacts:
            saved_paths.update(_save_detection_artifacts(output_dir, stem, payload))

        cleaned = self.cleaner.generate_clean_page(image_path, payload["bubbles"])

        cleaned_path = None
        if output_dir and save_cleaned:
            cleaned_path = output_dir / f"{stem}_inpainted.png"
            cv2.imwrite(str(cleaned_path), cleaned)

        return {
            "cleaned_image": cleaned,
            "cleaned_path": cleaned_path,
            "detector_payload": payload,
            "saved_paths": saved_paths,
        }

    def run_from_metadata(
        self,
        image_path: str,
        metadata_path: str | Path,
        output_dir: str | Path | None = "output",
        save_cleaned: bool = True,
    ):
        bubbles = load_bubble_metadata(metadata_path)
        cleaned = self.cleaner.generate_clean_page(image_path, bubbles)

        output_dir = _ensure_dir(output_dir)
        cleaned_path = None
        if output_dir and save_cleaned:
            stem = Path(image_path).stem
            cleaned_path = output_dir / f"{stem}_inpainted.png"
            cv2.imwrite(str(cleaned_path), cleaned)

        return {"cleaned_image": cleaned, "cleaned_path": cleaned_path}


def _build_arg_parser():
    parser = argparse.ArgumentParser(
        description="Run speech bubble detection -> mask -> inpainting pipeline."
    )
    parser.add_argument("--image", required=True, help="Path to input manga page image")
    parser.add_argument(
        "--detector-model",
        default=str(
            Path(__file__).resolve().parents[1] / "models" / "bubble_segmenter_best.pt"
        ),
        help="Path to speech bubble detector weights",
    )
    parser.add_argument(
        "--inpaint-model",
        required=True,
        help="Stable Diffusion inpainting model id or local path",
    )
    parser.add_argument("--output-dir", default="output")
    parser.add_argument("--conf", type=float, default=0.2)
    parser.add_argument("--imgsz", type=int, default=1024)
    parser.add_argument("--device", default=None)
    parser.add_argument("--prompt", default=None)
    parser.add_argument("--negative-prompt", default=None)
    parser.add_argument("--guidance-scale", type=float, default=7.5)
    parser.add_argument("--steps", type=int, default=25)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--padding", type=int, default=16)
    parser.add_argument("--variance-threshold", type=float, default=8.0)
    return parser


if __name__ == "__main__":
    args = _build_arg_parser().parse_args()

    pipeline = SpeechBubbleInpaintingPipeline(
        detector_model_path=args.detector_model,
        inpaint_model_id_or_path=args.inpaint_model,
        conf=args.conf,
        imgsz=args.imgsz,
        variance_threshold=args.variance_threshold,
        generative_device=args.device,
        generative_prompt=args.prompt,
        generative_negative_prompt=args.negative_prompt,
        generative_guidance_scale=args.guidance_scale,
        generative_steps=args.steps,
        generative_seed=args.seed,
        generative_padding=args.padding,
    )

    result = pipeline.run(
        image_path=args.image,
        output_dir=args.output_dir,
        save_artifacts=True,
        save_cleaned=True,
    )

    cleaned_path = result["cleaned_path"]
    if cleaned_path:
        print(f"Saved inpainted page to: {cleaned_path}")
