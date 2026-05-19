import os
import shutil
import re

path = "./Temp"
ImagePath = "./Mangas/HinagikuKenzan/Manga Pages"
OutputPath = "./Temp_Images"

os.makedirs(OutputPath, exist_ok=True)

i = 1055

for file in os.listdir(path):
    fileNumber = (re.findall(r"(\d+)", str(file))[0])
    print(fileNumber)
    src = os.path.join(ImagePath, f"{fileNumber:03}.jpg")
    dst = os.path.join(OutputPath, f"Image_{i:03}.png")

    if os.path.exists(src):
        shutil.copyfile(src, dst)
        i += 1
    else:   
        print(f"❌ Image not found: {src}")