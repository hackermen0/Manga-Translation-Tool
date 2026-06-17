from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any

import cv2
from PIL import Image, ImageDraw, ImageFont

from .processor import MangaOCRProcessor

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


def _load_bubble_metadata(metadata_path: str | Path):
    metadata_path = Path(metadata_path)
    if not metadata_path.exists():
        raise FileNotFoundError(f"Bubble metadata not found at: {metadata_path}")

    with open(metadata_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    bubbles = []
    for bubble in data:
        bubble_id = bubble["bubble_id"]
        bbox = bubble["bbox"]
        area_px = bubble.get("area_px")
        mask_path_value = bubble.get("mask_path")

        if mask_path_value:
            mask_path = Path(mask_path_value)
            if not mask_path.is_absolute():
                mask_path = metadata_path.parent / mask_path
            if not mask_path.exists():
                raise FileNotFoundError(f"Bubble mask not found at: {mask_path}")
            mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
            if mask is None:
                raise FileNotFoundError(f"Unable to read bubble mask at: {mask_path}")
            area_px = area_px if area_px is not None else int((mask > 0).sum())

        bubble_payload = {"bubble_id": bubble_id, "bbox": bbox}
        if area_px is not None:
            bubble_payload["area_px"] = area_px
        if mask_path_value:
            bubble_payload["mask_path"] = str(mask_path)

        bubbles.append(bubble_payload)

    return bubbles


def _save_ocr_results(output_dir: Path, stem: str, results: list[dict[str, Any]]):
    ocr_path = output_dir / f"{stem}_ocr_results.json"
    with open(ocr_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    return ocr_path


def _save_annotated_page(
    image_path: str, output_path: Path, results: list[dict[str, Any]]
):
    image = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()

    for bubble in results:
        bbox = bubble["bbox"]
        x1 = bbox["x1"]
        x2 = bbox["x2"]
        y1 = bbox["y1"]
        y2 = bbox["y2"]

        draw.rectangle((x1, y1, x2, y2), outline=(255, 0, 0), width=3)
        label = str(bubble["bubble_id"])
        text_position = (x1 + 4, max(0, y1 - 12))
        draw.rectangle(
            (
                text_position[0] - 2,
                text_position[1] - 2,
                text_position[0] + 18,
                text_position[1] + 10,
            ),
            fill=(255, 255, 255),
        )
        draw.text(text_position, label, fill=(0, 0, 0), font=font)

    image.save(output_path)
    return output_path


class MangaOCRPipeline:
    def __init__(
        self,
        detector_model_path: str,
        conf: float = 0.2,
        border_erosion: int = 2,
        imgsz: int = 1024,
        row_tolerance: int = 200,
        detector: Any | None = None,
        processor: MangaOCRProcessor | None = None,
    ):
        if detector is None:
            detector_class = _get_detector_class()
            detector = detector_class(detector_model_path)

        if processor is None:
            processor = MangaOCRProcessor()

        self.detector = detector
        self.processor = processor
        self.conf = conf
        self.imgsz = imgsz
        self.border_erosion = border_erosion
        self.row_tolerance = row_tolerance

    def _sort_by_reading_order(
        self, bubbles: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Sorts bubbles using a robust row-stratified algorithm and
        re-indexes the bubble_ids sequentially to match reading order.
        """
        if not bubbles:
            return []

        from functools import cmp_to_key

        def compare_bubbles(b1, b2):
            box1, box2 = b1["bbox"], b2["bbox"]
            y_diff = box1["y1"] - box2["y1"]

            if abs(y_diff) > self.row_tolerance:
                return -1 if y_diff < 0 else 1
            else:
                x_diff = box2["x2"] - box1["x2"]
                return -1 if x_diff < 0 else 1

        # Step 1: Run your row-stratified coordinate sorting engine
        sorted_list = sorted(bubbles, key=cmp_to_key(compare_bubbles))

        # Step 2: Overwrite the bubble_id values to match their new list positions
        for sequential_index, bubble in enumerate(sorted_list):
            bubble["bubble_id"] = sequential_index

        return sorted_list

    def run(
        self,
        image_path: str,
        output_dir: str | Path | None = "output",
        save_artifacts: bool = True,
        save_annotated: bool = True,
    ):
        payload = self.detector.process_page(
            image_path=image_path,
            conf=self.conf,
            imgsz=self.imgsz,
            border_erosion=self.border_erosion,
        )

        sorted_bubbles = self._sort_by_reading_order(payload["bubbles"])
        results = self.processor.extract_page_texts(image_path, sorted_bubbles)

        stem = Path(image_path).stem
        saved_paths = {}
        output_dir = _ensure_dir(output_dir)
        if output_dir and save_artifacts:
            saved_paths["ocr_results"] = _save_ocr_results(output_dir, stem, results)
        if output_dir and save_annotated:
            annotated_path = output_dir / f"{stem}_ocr_annotated.png"
            saved_paths["annotated"] = _save_annotated_page(
                image_path, annotated_path, results
            )

        return {
            "ocr_results": results,
            "detector_payload": payload,
            "saved_paths": saved_paths,
        }

    def run_from_metadata(
        self,
        image_path: str,
        metadata_path: str | Path,
        output_dir: str | Path | None = "output",
        save_annotated: bool = True,
    ):
        bubbles = _load_bubble_metadata(metadata_path)

        sorted_bubbles = self._sort_by_reading_order(bubbles)
        results = self.processor.extract_page_texts(image_path, sorted_bubbles)

        stem = Path(image_path).stem
        saved_paths = {}
        output_dir = _ensure_dir(output_dir)
        if output_dir:
            saved_paths["ocr_results"] = _save_ocr_results(output_dir, stem, results)
        if output_dir and save_annotated:
            annotated_path = output_dir / f"{stem}_ocr_annotated.png"
            saved_paths["annotated"] = _save_annotated_page(
                image_path, annotated_path, results
            )

        return {"ocr_results": results, "saved_paths": saved_paths}


def _build_arg_parser():
    parser = argparse.ArgumentParser(
        description="Run speech bubble detection -> OCR pipeline."
    )
    parser.add_argument("--image", required=True, help="Path to input manga page image")
    parser.add_argument(
        "--detector-model",
        default=str(
            Path(__file__).resolve().parents[1] / "models" / "speech_bubble_detector.pt"
        ),
        help="Path to speech bubble detector weights",
    )
    parser.add_argument("--output-dir", default="output")
    parser.add_argument("--conf", type=float, default=0.2)
    parser.add_argument("--border-erosion", type=int, default=2)
    parser.add_argument("--imgsz", type=int, default=1024)
    parser.add_argument(
        "--row-tolerance",
        type=int,
        default=200,
        help="Vertical pixel tier boundary separation",
    )
    parser.add_argument(
        "--metadata",
        default=None,
        help="Optional bubble metadata JSON file to skip detection and OCR existing bubbles.",
    )
    parser.add_argument(
        "--no-annotated",
        action="store_true",
        help="Do not save an annotated output image.",
    )
    return parser


if __name__ == "__main__":
    args = _build_arg_parser().parse_args()

    pipeline = MangaOCRPipeline(
        detector_model_path=args.detector_model,
        conf=args.conf,
        border_erosion=args.border_erosion,
        imgsz=args.imgsz,
        row_tolerance=args.row_tolerance,
    )

    if args.metadata:
        result = pipeline.run_from_metadata(
            image_path=args.image,
            metadata_path=args.metadata,
            output_dir=args.output_dir,
            save_annotated=not args.no_annotated,
        )
    else:
        result = pipeline.run(
            image_path=args.image,
            output_dir=args.output_dir,
            save_artifacts=True,
            save_annotated=not args.no_annotated,
        )

    ocr_results = result["ocr_results"]
    print(f"OCR results generated for {len(ocr_results)} bubbles.")
    for path_name, saved_path in result["saved_paths"].items():
        print(f"Saved {path_name}: {saved_path}")
