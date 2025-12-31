import easyocr
import os
from PIL import Image, ImageDraw, ImageFont
import numpy as np

processed_image_folders = "./processed/grayscale"
reader = easyocr.Reader(['ja'])

for image_file in os.listdir(processed_image_folders):
    print(image_file)
    image_path = os.path.join(processed_image_folders, image_file)
    image = Image.open(image_path).convert("RGB")

    results = reader.readtext(
        np.array(image),
        paragraph=True,
    )

    draw = ImageDraw.Draw(image)

    for i, result in enumerate(results):
        box_coordinates, text = result[0], result[1]
        polygon = [tuple(point) for point in box_coordinates]
        draw.polygon(polygon, outline="red")

        x, y = polygon[0]
        font = ImageFont.truetype("./assets/Roboto_Condensed-Black.ttf", 24)
        draw.text((x - 10, y - 15), str(i), fill="green", font=font)

        print(f"[{i}] {text.upper()}")

    image.show()