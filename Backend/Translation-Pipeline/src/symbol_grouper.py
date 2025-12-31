import json
import os
import re

def sentence_grouping(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        translation_data = json.load(f)

    bounding_box_data = []

    blocks = translation_data['fullTextAnnotation']['pages'][0]['blocks']
    for block in blocks:
        for paragraph in block['paragraphs']:
            for word in paragraph['words']:
                for symbol in word['symbols']:
                    box = symbol['boundingBox']['vertices']
                    text = symbol['text']
                    # print(box, text)
                    bounding_box_data.append({
                        "text": text,
                        "box": box
                    })


    grouped_sentences = []
    x_threshold = 3
    y_threshold = 50  

    grouped_sentences = []
    current_group = []

    for i, item in enumerate(bounding_box_data):
        box1 = item["box"]
        try:
            next_item = bounding_box_data[i + 1]
            box2 = next_item["box"]
        except IndexError:
            current_group.append(item)
            grouped_sentences.append(current_group)
            break

        x_close = all(abs(box1[j]['x'] - box2[j]['x']) <= x_threshold for j in range(4))

        
        y1_avg = sum(pt.get('y', 0) for pt in box1) / 4
        y2_avg = sum(pt.get('y', 0) for pt in box2) / 4
        y_close = abs(y2_avg - y1_avg) <= y_threshold

        if x_close and y_close:
            current_group.append(item)
        else:
            current_group.append(item)
            grouped_sentences.append(current_group)
            current_group = []

    if current_group:
        grouped_sentences.append(current_group)


    final_json_data = []
    
    for i, group in enumerate(grouped_sentences):
        json_data = {}

        sentence = "".join(symbol['text'] for symbol in group)
        boxes = [symbol['box'] for symbol in group]

        all_points = [pt for box in boxes for pt in box]
        xs = [pt.get('x', 0) for pt in all_points]
        ys = [pt.get('y', 0) for pt in all_points]

        minx, maxx = min(xs), max(xs)
        miny, maxy = min(ys), max(ys)

        final_box = [
            (minx, miny),
            (maxx, miny),
            (minx, maxy),
            (maxx, maxy)
        ]

        json_data['sentence'] = sentence
        json_data['grouped_boxes'] = boxes
        json_data['final_box'] = final_box

        final_json_data.append(json_data)

    os.makedirs("./processed/grouped sentence data/", exist_ok=True)

    match = re.findall(r"\d+", file_path)
    file_name = "sentence_data_" + (match[0] if match else "unknown")

    with open(f"./processed/grouped sentence data/{file_name}.json", "w", encoding="utf-8") as f:
        json.dump(final_json_data, f, ensure_ascii=False, indent=2)

def main():

    path = "./processed/json/"

    for file in os.listdir(path):
        print(file)
        sentence_grouping(file_path=f"{path}/{file}")
        print("Done.\n")
        

if __name__ == "__main__":
    main()




