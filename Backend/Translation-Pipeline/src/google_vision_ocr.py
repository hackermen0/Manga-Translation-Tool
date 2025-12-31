from google.cloud import vision
from PIL import Image, ImageDraw
import io
import os
from google.protobuf.json_format import MessageToDict
import json



def draw_boxes(image_path, image_name, results):
    image  = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(image)

    os.makedirs("./processed/countours", exist_ok=True)

    for i, (box, text) in enumerate(results):
        with open(f"./processed/countours/final_{image_name}.txt", "a", encoding="utf-8") as f:
            f.write(f"[{i+1}] -------> {box}  ({text})")
        print(f"[{i+1}] -------> {box}  ({text})")
        draw.polygon(box, outline='red')
        draw.text(box[0], f"{i+1}", fill="blue")

    os.makedirs("./processed/final", exist_ok=True)
    image.show()
    image.save(f"./processed/final/final_{image_name}.jpg")


def ocr(image_path, json_output_path=None):
    client = vision.ImageAnnotatorClient()

    with io.open(image_path, "rb") as image_file:
        content = image_file.read()
    
    image = vision.Image(content=content)
    response = client.document_text_detection(image=image)

    if json_output_path:
        os.makedirs(os.path.dirname(json_output_path), exist_ok=True)
        dict_response = MessageToDict(response._pb) 
        with open(json_output_path, "w", encoding="utf-8") as f:
            json.dump(dict_response, f, ensure_ascii=False, indent=2)

    texts = response.text_annotations
    if not texts:
        return []

    results = []
    for text in texts[1:]:
        box = [(v.x, v.y) for v in text.bounding_poly.vertices]
        results.append((box, text.description))

    return results

def main():
    file_path = "./processed/grayscale"
    for file in os.listdir(file_path):
        print(file)
        image_name = os.path.splitext(file)[0] 

        results = ocr(f"{file_path}/{file}", json_output_path=f"./processed/json/{image_name}.json")
        draw_boxes(f"{file_path}/{file}", image_name, results)

if __name__ == "__main__":
    main()