from PIL import Image, ImageDraw
import json
import os

for file in os.listdir("./raw"):

    image_path = f"./raw/{file}"
    image = Image.open(image_path)
    draw = ImageDraw.Draw(image)


    json_path = f"./processed/bubble-clusters/bubble_cluster_{os.path.splitext(file)[0]}.json"
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)


    for bubble in data:
        for sentence in bubble['sentences']:
            final_box = sentence['final_box']
            padding = 11

            top_left = (final_box[0][0] - padding, final_box[0][1] - padding)
            bottom_right = (final_box[3][0] + padding, final_box[3][1] + padding)

            draw.rectangle([top_left, bottom_right], fill="white")


    # image.show()
    image.save(f"./processed/redrawn/redrawn_{os.path.splitext(file)[0]}.jpg")
