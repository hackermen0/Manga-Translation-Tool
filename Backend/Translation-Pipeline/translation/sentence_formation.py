import os
import json
import re



def arrange_sentences(path):

    for file in os.listdir(path):

        page_sentences = []
    
        print(file + "\n\n\n")
        with open(f"{path}/{file}", "r", encoding="utf-8") as f:
            data = json.load(f)

        for bubble_data in data:
            bubble_id = bubble_data['bubble_id']
            

            bubble_sentence = []
            final_box_data = []
            for sentence in bubble_data['sentences']:
                bubble_sentence.append(sentence['sentence'])
                final_box_data.append(sentence['final_box'])

            final_sentence = {
                "bubble_id" : bubble_id,
                "sentence" : " ".join(bubble_sentence),
                "final_box" : final_box_data
            }

            page_sentences.append(final_sentence)

            
        with open(f"./processed/arranged-sentences/arranged_sentences_{re.findall("\d+", file)[0]}.json", "w", encoding="utf-8") as f:
            json.dump(page_sentences, f, ensure_ascii=False, indent=2)
            print(f"Done with arranged_sentences_{re.findall("\d+", file)[0]}.json")

def main():
    path = "./processed/bubble-clusters"
    arrange_sentences(path)

if __name__ == "__main__":
    main()