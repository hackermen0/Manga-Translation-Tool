#!/usr/bin/env python3
"""
Test script to demonstrate the crop_bubble functionality.
This script shows how to use the MangaOCRProcessor to crop bubbles from a manga page.
"""

from PIL import Image
from manga_ocr import MangaOcr
import cv2
import json


def main():
    processor = MangaOcr()

    with open(
        r"C:\Users\KIIT\Documents\Coding Projects\Python projects\On-going Projects\Manga Translation Tool\Backend\output\069_bubble_metadata.json",
        "r",
        encoding="utf-8",
    ) as f:
        bubble_metadata = json.load(f)

    print(bubble_metadata)

    original_image = Image.open(
        r"C:\Users\KIIT\Documents\Coding Projects\Python projects\On-going Projects\Manga Translation Tool\Backend\translation-pipeline\raw\069.jpg"
    )

    updated_data = []

    for data in bubble_metadata:
        bbox_data = data["bbox"]

        x1 = bbox_data["x1"]
        x2 = bbox_data["x2"]
        y1 = bbox_data["y1"]
        y2 = bbox_data["y2"]

        cropped_image = original_image.crop((x1, y1, x2, y2))

        ocr_string = processor(cropped_image)

        data["original_text"] = ocr_string

        print(data)

        updated_data.append(data)

    with open(
        r"C:\Users\KIIT\Documents\Coding Projects\Python projects\On-going Projects\Manga Translation Tool\Backend\output\069_bubble_metadata_new.json",
        "w",
        # encoding="utf-8",
    ) as f:
        json.dump(updated_data, f)


if __name__ == "__main__":
    main()
