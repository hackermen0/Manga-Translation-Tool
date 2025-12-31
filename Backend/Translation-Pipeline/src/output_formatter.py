import re
import os

path = "./processed/countours"

for file in os.listdir(path):
    input_path = f"{path}/{file}"
    file_name = os.path.splitext(file)[0] 
    output_path = f"{path}/{file_name}_final.txt"

    # Read the original content
    with open(input_path, "r", encoding="utf-8") as file:
        content = file.read()

    # Add newline before every [number]
    modified_content = re.sub(r'(?=\[\d+\])', r'\n', content)

    # Save the modified content
    with open(output_path, "w", encoding="utf-8") as file:
        file.write(modified_content)

    print("New lines added before each [number]. Output saved to:", output_path)
