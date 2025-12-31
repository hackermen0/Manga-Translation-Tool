import json
from PIL import Image, ImageDraw, ImageFont
import os
import re


font = ImageFont.truetype(font="./assets/Roboto_Condensed-Black.ttf", size=16)

for file in os.listdir("./processed/bubble-clusters"):

    
    image = Image.open(f"./raw/{re.findall(r"\d+", file)[0]}.jpg")
    draw = ImageDraw.Draw(image)

    with open(f"./processed/bubble-clusters/{file}", "r", encoding="utf-8") as f:
        data = json.load(f)

    for bubble_data in data:
        bubble_id = bubble_data["bubble_id"]
        sentences = bubble_data['sentences']
        for sentence in sentences:
            final_box = sentence['final_box']
            coord1 = final_box[0]
            coord2 = final_box[3]
            draw.rectangle((tuple(coord1), tuple(coord2)), outline="red", width=2)
            draw.text(tuple(coord1), str(bubble_id), fill="blue", font=font)
    

    image.save(f"./processed/bubble-cluster-images/{os.path.splitext(file)[0]}.png")

