import dotenv
import os
from google.cloud import translate_v3
import json
import re

dotenv.load_dotenv()

path = "./processed/arranged-sentences"
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")

client = translate_v3.TranslationServiceClient()
parent = f"projects/{GCP_PROJECT_ID}/locations/global"
mime_type = "text/plain"


for file in os.listdir(path):

    translation_list = []

    print(f"========={file}==========")

    with open(f"{path}/{file}", "r", encoding="utf-8") as f:
        data = json.load(f)
        for bubble_data in data:
            sentence = bubble_data['sentence']
            translation_list.append(sentence)

    response = client.translate_text(
        contents=translation_list,
        parent=parent,
        mime_type=mime_type,
        source_language_code="ja",
        target_language_code="en-GB"
    )

    final_output = []

    print(response.translations)

    for translated_obj, bubble_data in zip(response.translations, data):

        final_output.append({
            "bubble_id": bubble_data['bubble_id'],
            "original_sentence": bubble_data['sentence'],
            "translated_text": translated_obj.translated_text,
            "final_box": bubble_data['final_box']
        })

    file_id = re.findall(r"\d+", file)[0]
    output_path = f"./processed/translated-text-with-gcp/translated_text_{file_id}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_output, f, ensure_ascii=False, indent=2)

    print(f"Translation complete. Saved to: {output_path}")
