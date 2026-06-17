from __future__ import annotations

import argparse
from pathlib import Path

if __package__ is None or __package__ == "":
    import sys

    sys.path.append(str(Path(__file__).resolve().parent))
    from pipeline import MangaOCRPipeline
else:
    from .pipeline import MangaOCRPipeline


def _build_arg_parser():
    parser = argparse.ArgumentParser(
        description="Quick CLI test for the Manga OCR pipeline."
    )
    parser.add_argument("--image", required=True, help="Path to the manga page image")
    parser.add_argument(
        "--detector-model",
        default=str(
            Path(__file__).resolve().parents[1] / "models" / "speech_bubble_detector.pt"
        ),
        help="Path to the speech bubble detector weights",
    )
    parser.add_argument("--output-dir", default="output")
    parser.add_argument("--conf", type=float, default=0.2)
    parser.add_argument("--border-erosion", type=int, default=2)
    parser.add_argument("--imgsz", type=int, default=1024)
    parser.add_argument(
        "--metadata",
        default=None,
        help="Optional bubble metadata JSON file to skip detection and reuse existing bubbles.",
    )
    parser.add_argument(
        "--no-annotated",
        action="store_true",
        help="Skip saving the annotated preview image.",
    )
    return parser


def main():
    args = _build_arg_parser().parse_args()

    pipeline = MangaOCRPipeline(
        detector_model_path=args.detector_model,
        conf=args.conf,
        border_erosion=args.border_erosion,
        imgsz=args.imgsz,
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
    for item in ocr_results:
        print(f"[{item['bubble_id']}] {item.get('original_text', '')}")

    for name, saved_path in result["saved_paths"].items():
        print(f"Saved {name}: {saved_path}")


if __name__ == "__main__":
    main()
