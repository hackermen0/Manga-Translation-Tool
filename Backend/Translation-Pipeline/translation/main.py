import os
import json
import deepl
import dotenv
import re

dotenv.load_dotenv()
deepL_api_key = os.getenv("DEEPL_API_KEY")

def translate_text(
    text,
    source_lang="JA",
    target_lang="EN-GB",
    model_type="prefer_quality_optimized",
    context="",
    formality="default",
    split_sentences="0",
    preserve_formatting="1"
):
    translator = deepl.Translator(deepL_api_key)

    result = translator.translate_text(
        text=text,
        source_lang=source_lang,
        target_lang=target_lang,
        model_type=model_type,
        formality=formality,
        split_sentences=split_sentences,
        preserve_formatting=preserve_formatting,
    )

    return result

path = "./processed/arranged-sentences"

def main():

    for file in os.listdir(path):
        with open(f"{path}/{file}", "r", encoding="utf-8") as f:
            data = json.load(f)

        print(f"\n\n============={file}================\n\n")

        total_result = []

        for idx, bubble in enumerate(data):
            bubble_id = bubble['bubble_id']
            sentence = bubble['sentence']
            final_boxes = bubble['final_box']

            prev_sentence = data[idx - 1]['sentence'] if idx > 0 else ""
            next_sentence = data[idx + 1]['sentence'] if idx < len(data) - 1 else ""
            context = f"{prev_sentence}\n{next_sentence}".strip()

            print(f"[Bubble ID {bubble_id}]")
            print(f"Original: {sentence}")
            print(f"Context: {context}\n")

            result = translate_text(text=sentence, context=context, split_sentences="nonewlines", preserve_formatting="1")
            print("Translation:", result.text)
            print("Billed Characters:", result.billed_characters, "\n\n")

            total_result.append({
                "bubble_id": bubble_id,
                "original": sentence,
                "translated": result.text,
                # "context": context,
                "model_used": result.model_type_used,
                "billed_characters": result.billed_characters,
                "final_box" : final_boxes
            })

        with open(f"./processed/translated-text-without-context/translated_text_{re.findall("\d+", file)[0]}.json", "w", encoding="utf-8") as f:
            json.dump(total_result, f, ensure_ascii = False, indent = 2)

if __name__ == "__main__":
    main()