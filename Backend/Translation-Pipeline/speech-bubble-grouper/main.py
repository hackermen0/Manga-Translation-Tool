import json
import os
import numpy as np
from sklearn.cluster import DBSCAN
import re

def cluster_sentences_by_bubble(input_json_path, output_path, eps=60, min_samples=1):
    with open(input_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    sentence_centers = []
    for entry in data:
        box = entry["final_box"]
        cx = (box[0][0] + box[3][0]) // 2
        cy = (box[0][1] + box[3][1]) // 2
        sentence_centers.append([cx, cy])

    X = np.array(sentence_centers)
    clustering = DBSCAN(eps=eps, min_samples=min_samples).fit(X)

    clustered = {}
    for idx, label in enumerate(clustering.labels_):
        if label not in clustered:
            clustered[label] = []
        clustered[label].append(data[idx])

    bubble_data = []
    for label, sentences in clustered.items():

        sorted_sentences = sorted(sentences, key=lambda s: s["final_box"][1][0], reverse=True)

        bubble_data.append({
            "bubble_id": int(label),
            "sentences": sorted_sentences
        })

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(bubble_data, f, ensure_ascii=False, indent=2)

    print(f"Clustered {len(data)} sentences into {len(bubble_data)} speech bubbles.")


if __name__ == "__main__":
    input_path = "./processed/grouped-sentence-data/"
    for file in os.listdir(input_path):
        match = re.findall(r"\d+", file)
        if not match:
            continue
        file_id = match[0]
        input_json = f"{input_path}/{file}"
        output_json = f"./processed/bubble-clusters/bubble_cluster_{file_id}.json"
        cluster_sentences_by_bubble(input_json, output_json)
