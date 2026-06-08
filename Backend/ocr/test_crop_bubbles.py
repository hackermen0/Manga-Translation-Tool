#!/usr/bin/env python3
"""
Test script to demonstrate the crop_bubble functionality.
This script shows how to use the MangaOCRProcessor to crop bubbles from a manga page.
"""

from pathlib import Path
from ocr.processor import MangaOCRProcessor
import cv2


def main():
    processor = MangaOCRProcessor()

    output_dir = Path("output")

    image_files = list(output_dir.glob("*_inpainted.png"))

    if not image_files:
        print("No inpainted images found in output directory.")
        print("First, run the inpainting pipeline to generate images and metadata.")
        return

    original_images = list(output_dir.glob("*.png"))
    original_images = [
        img
        for img in original_images
        if "_inpainted" not in img.name
        and "_annotated" not in img.name
        and "_combined_mask" not in img.name
    ]

    if not original_images:
        print("No original manga page images found.")
        return

    original_image = original_images[0]
    metadata_files = list(output_dir.glob("*_bubble_metadata.json"))

    if not metadata_files:
        print("No bubble metadata found.")
        return

    metadata_file = metadata_files[0]

    print(f"Processing image: {original_image}")
    print(f"Using metadata: {metadata_file}")
    print()

    saved_paths = processor.crop_and_save_bubbles(
        image_path=str(original_image),
        metadata_path=str(metadata_file),
        output_dir="output/cropped_bubbles",
    )

    print(f"\n✓ Cropped {len(saved_paths)} bubbles successfully!")
    print("Saved to: output/cropped_bubbles/")
    print("\nCropped bubble files:")
    for path in saved_paths:
        print(f"  - {path.name}")


if __name__ == "__main__":
    main()
