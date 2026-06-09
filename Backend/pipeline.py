from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence

import cv2
from PIL import Image, ImageDraw, ImageFont

BACKEND_ROOT = Path(__file__).resolve().parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from inpainting.cleaner import HybridMangaCleaner
from ocr.processor import MangaOCRProcessor

_DETECTOR_CLASS: type | None = None


def _get_detector_class():
    global _DETECTOR_CLASS
    if _DETECTOR_CLASS is not None:
        return _DETECTOR_CLASS

    detector_path = BACKEND_ROOT / "speech-bubble-detection" / "detector.py"
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


def _save_inpainted_page(output_dir: Path, stem: str, cleaned_image):
    cleaned_path = output_dir / f"{stem}_inpainted.png"
    cv2.imwrite(str(cleaned_path), cleaned_image)
    return cleaned_path


def _save_ocr_results(output_dir: Path, stem: str, results: list[dict[str, Any]]):
    ocr_path = output_dir / f"{stem}_ocr_results.json"
    with open(ocr_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    return ocr_path


def _save_ocr_annotated_page(
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


@dataclass(slots=True)
class PipelineContext:
    image_path: Path
    output_dir: Path | None
    metadata_path: Path | None = None
    detector_payload: dict[str, Any] | None = None
    cleaned_image: Any | None = None
    ocr_results: list[dict[str, Any]] = field(default_factory=list)
    translation_results: Any | None = None
    saved_paths: dict[str, Path] = field(default_factory=dict)
    stage_results: dict[str, Any] = field(default_factory=dict)


class PipelineStage(ABC):
    name: str

    @abstractmethod
    def run(self, context: PipelineContext) -> None:
        raise NotImplementedError


class BubbleDetectionStage(PipelineStage):
    name = "detection"

    def __init__(
        self,
        detector_model_path: str,
        conf: float = 0.2,
        border_erosion: int = 2,
        imgsz: int = 1024,
        save_artifacts: bool = True,
        detector: Any | None = None,
    ):
        self.detector_model_path = detector_model_path
        self.conf = conf
        self.border_erosion = border_erosion
        self.imgsz = imgsz
        self.save_artifacts = save_artifacts
        self._detector = detector

    def _get_detector(self):
        if self._detector is None:
            detector_class = _get_detector_class()
            self._detector = detector_class(self.detector_model_path)
        return self._detector

    def run(self, context: PipelineContext) -> None:
        if context.metadata_path is not None:
            bubbles = _load_bubble_metadata(context.metadata_path)
            payload = {"bubbles": bubbles, "metadata_path": context.metadata_path}
            context.detector_payload = payload
            context.stage_results[self.name] = payload
            context.saved_paths.setdefault("metadata", context.metadata_path)
            return

        detector = self._get_detector()
        payload = detector.process_page(
            image_path=str(context.image_path),
            conf=self.conf,
            imgsz=self.imgsz,
            border_erosion=self.border_erosion,
        )
        context.detector_payload = payload
        context.stage_results[self.name] = payload

        if context.output_dir and self.save_artifacts:
            stem = context.image_path.stem
            saved = _save_detection_artifacts(context.output_dir, stem, payload)
            for key, value in saved.items():
                context.saved_paths[key] = value
            context.metadata_path = saved["metadata"]


class InpaintingStage(PipelineStage):
    name = "inpainting"

    def __init__(
        self,
        inpaint_model_id_or_path: str,
        variance_threshold: float = 8.0,
        programmatic_fill_color: tuple[int, int, int] | None = (255, 255, 255),
        generative_device: str | None = None,
        generative_prompt: str | None = None,
        generative_negative_prompt: str | None = None,
        generative_guidance_scale: float = 7.5,
        generative_steps: int = 25,
        generative_seed: int | None = None,
        generative_padding: int = 16,
        save_cleaned: bool = True,
        cleaner: HybridMangaCleaner | None = None,
    ):
        self.save_cleaned = save_cleaned
        self._cleaner = cleaner
        if self._cleaner is None:
            self._cleaner = HybridMangaCleaner(
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

    def run(self, context: PipelineContext) -> None:
        if context.detector_payload is None:
            raise RuntimeError(
                "Inpainting stage requires detector output before it runs."
            )

        bubbles = context.detector_payload["bubbles"]
        cleaned_image = self._cleaner.generate_clean_page(
            str(context.image_path), bubbles
        )
        context.cleaned_image = cleaned_image
        context.stage_results[self.name] = cleaned_image

        if context.output_dir and self.save_cleaned:
            stem = context.image_path.stem
            context.saved_paths["cleaned"] = _save_inpainted_page(
                context.output_dir, stem, cleaned_image
            )


class OCRStage(PipelineStage):
    name = "ocr"

    def __init__(
        self,
        save_results: bool = True,
        save_annotated: bool = True,
        processor: MangaOCRProcessor | None = None,
    ):
        self.save_results = save_results
        self.save_annotated = save_annotated
        self._processor = processor

    def _get_processor(self):
        if self._processor is None:
            self._processor = MangaOCRProcessor()
        return self._processor

    def run(self, context: PipelineContext) -> None:
        if context.detector_payload is None:
            raise RuntimeError("OCR stage requires detector output before it runs.")

        processor = self._get_processor()
        bubbles = context.detector_payload["bubbles"]
        results = processor.extract_page_texts(str(context.image_path), bubbles)
        context.ocr_results = results
        context.stage_results[self.name] = results

        if context.output_dir and self.save_results:
            stem = context.image_path.stem
            context.saved_paths["ocr_results"] = _save_ocr_results(
                context.output_dir, stem, results
            )
        if context.output_dir and self.save_annotated:
            stem = context.image_path.stem
            context.saved_paths["ocr_annotated"] = _save_ocr_annotated_page(
                str(context.image_path),
                context.output_dir / f"{stem}_ocr_annotated.png",
                results,
            )


class TranslationStage(PipelineStage):
    name = "translation"

    def __init__(self, translator: Any | None = None, enabled: bool = False):
        self.translator = translator
        self.enabled = enabled

    def run(self, context: PipelineContext) -> None:
        if not self.enabled:
            context.stage_results[self.name] = None
            return

        if self.translator is None:
            context.stage_results[self.name] = None
            return

        if context.ocr_results is None:
            raise RuntimeError("Translation stage requires OCR results before it runs.")

        translated = self.translator(context.ocr_results, context=context)
        context.translation_results = translated
        context.stage_results[self.name] = translated


@dataclass(slots=True)
class PipelineConfig:
    detector_model_path: str
    inpaint_model_id_or_path: str | None = None
    output_dir: str | Path | None = "output"
    conf: float = 0.2
    border_erosion: int = 2
    imgsz: int = 1024
    variance_threshold: float = 8.0
    programmatic_fill_color: tuple[int, int, int] | None = (255, 255, 255)
    generative_device: str | None = None
    generative_prompt: str | None = None
    generative_negative_prompt: str | None = None
    generative_guidance_scale: float = 7.5
    generative_steps: int = 25
    generative_seed: int | None = None
    generative_padding: int = 16
    save_detection_artifacts: bool = True
    save_inpainted: bool = True
    save_ocr_results: bool = True
    save_ocr_annotated: bool = True
    enable_translation: bool = False
    metadata_path: str | Path | None = None


class MangaTranslationPipeline:
    def __init__(
        self,
        config: PipelineConfig,
        stages: Sequence[PipelineStage] | None = None,
        detector: Any | None = None,
        cleaner: HybridMangaCleaner | None = None,
        processor: MangaOCRProcessor | None = None,
    ):
        self.config = config
        self._stages = (
            list(stages)
            if stages is not None
            else self._build_default_stages(
                detector=detector,
                cleaner=cleaner,
                processor=processor,
            )
        )

    def _build_default_stages(
        self,
        detector: Any | None = None,
        cleaner: HybridMangaCleaner | None = None,
        processor: MangaOCRProcessor | None = None,
    ):
        stages: list[PipelineStage] = [
            BubbleDetectionStage(
                detector_model_path=self.config.detector_model_path,
                conf=self.config.conf,
                border_erosion=self.config.border_erosion,
                imgsz=self.config.imgsz,
                save_artifacts=self.config.save_detection_artifacts,
                detector=detector,
            ),
        ]

        if self.config.inpaint_model_id_or_path is not None:
            stages.append(
                InpaintingStage(
                    inpaint_model_id_or_path=self.config.inpaint_model_id_or_path,
                    variance_threshold=self.config.variance_threshold,
                    programmatic_fill_color=self.config.programmatic_fill_color,
                    generative_device=self.config.generative_device,
                    generative_prompt=self.config.generative_prompt,
                    generative_negative_prompt=self.config.generative_negative_prompt,
                    generative_guidance_scale=self.config.generative_guidance_scale,
                    generative_steps=self.config.generative_steps,
                    generative_seed=self.config.generative_seed,
                    generative_padding=self.config.generative_padding,
                    save_cleaned=self.config.save_inpainted,
                    cleaner=cleaner,
                )
            )

        stages.append(
            OCRStage(
                save_results=self.config.save_ocr_results,
                save_annotated=self.config.save_ocr_annotated,
                processor=processor,
            )
        )

        stages.append(TranslationStage(enabled=self.config.enable_translation))
        return stages

    def run(self, image_path: str, output_dir: str | Path | None = None):
        resolved_output_dir = _ensure_dir(
            output_dir if output_dir is not None else self.config.output_dir
        )
        context = PipelineContext(
            image_path=Path(image_path),
            output_dir=resolved_output_dir,
            metadata_path=(
                Path(self.config.metadata_path)
                if self.config.metadata_path is not None
                else None
            ),
        )

        for stage in self._stages:
            stage.run(context)

        return {
            "image_path": context.image_path,
            "output_dir": context.output_dir,
            "detector_payload": context.detector_payload,
            "cleaned_image": context.cleaned_image,
            "ocr_results": context.ocr_results,
            "translation_results": context.translation_results,
            "saved_paths": context.saved_paths,
            "stage_results": context.stage_results,
        }


def _build_programmatic_fill_color(values: Sequence[int] | None):
    if values is None:
        return None
    if len(values) != 3:
        raise ValueError("programmatic fill color requires exactly 3 values.")
    return tuple(int(value) for value in values)


def _build_arg_parser():
    parser = argparse.ArgumentParser(
        description="Run the modular manga pipeline: detection -> inpainting -> OCR -> translation."
    )
    parser.add_argument("--image", required=True, help="Path to input manga page image")
    parser.add_argument(
        "--detector-model",
        default=str(BACKEND_ROOT / "models" / "bubble_segmenter_best.pt"),
        help="Path to speech bubble detector weights",
    )
    parser.add_argument(
        "--inpaint-model",
        default=None,
        help="Stable Diffusion inpainting model id or local path",
    )
    parser.add_argument("--output-dir", default="output")
    parser.add_argument("--conf", type=float, default=0.2)
    parser.add_argument("--border-erosion", type=int, default=2)
    parser.add_argument("--imgsz", type=int, default=1024)
    parser.add_argument("--variance-threshold", type=float, default=8.0)
    parser.add_argument(
        "--programmatic-fill-color",
        nargs=3,
        type=int,
        metavar=("R", "G", "B"),
        default=(255, 255, 255),
        help="Programmatic fill color used by the inpainting stage.",
    )
    parser.add_argument("--device", default=None)
    parser.add_argument("--prompt", default=None)
    parser.add_argument("--negative-prompt", default=None)
    parser.add_argument("--guidance-scale", type=float, default=7.5)
    parser.add_argument("--steps", type=int, default=25)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--padding", type=int, default=16)
    parser.add_argument(
        "--metadata",
        default=None,
        help="Optional bubble metadata JSON file to skip bubble detection and reuse existing masks.",
    )
    parser.add_argument(
        "--no-detection-artifacts",
        action="store_true",
        help="Do not save detection outputs such as masks, metadata, or annotated previews.",
    )
    parser.add_argument(
        "--no-inpainted",
        action="store_true",
        help="Do not save the inpainted page output.",
    )
    parser.add_argument(
        "--no-ocr-results",
        action="store_true",
        help="Do not save OCR results as JSON.",
    )
    parser.add_argument(
        "--no-ocr-annotated",
        action="store_true",
        help="Do not save the OCR annotated preview image.",
    )
    parser.add_argument(
        "--enable-translation",
        action="store_true",
        help="Enable the translation stage placeholder for future integration.",
    )
    return parser


if __name__ == "__main__":
    args = _build_arg_parser().parse_args()

    config = PipelineConfig(
        detector_model_path=args.detector_model,
        inpaint_model_id_or_path=args.inpaint_model,
        output_dir=args.output_dir,
        conf=args.conf,
        border_erosion=args.border_erosion,
        imgsz=args.imgsz,
        variance_threshold=args.variance_threshold,
        programmatic_fill_color=_build_programmatic_fill_color(
            args.programmatic_fill_color
        ),
        generative_device=args.device,
        generative_prompt=args.prompt,
        generative_negative_prompt=args.negative_prompt,
        generative_guidance_scale=args.guidance_scale,
        generative_steps=args.steps,
        generative_seed=args.seed,
        generative_padding=args.padding,
        save_detection_artifacts=not args.no_detection_artifacts,
        save_inpainted=not args.no_inpainted,
        save_ocr_results=not args.no_ocr_results,
        save_ocr_annotated=not args.no_ocr_annotated,
        enable_translation=args.enable_translation,
        metadata_path=args.metadata,
    )

    pipeline = MangaTranslationPipeline(config)
    result = pipeline.run(args.image)

    print(f"Processed image: {result['image_path']}")
    for name, saved_path in result["saved_paths"].items():
        print(f"Saved {name}: {saved_path}")

    if result["ocr_results"] is not None:
        print(f"OCR results generated for {len(result['ocr_results'])} bubbles.")
