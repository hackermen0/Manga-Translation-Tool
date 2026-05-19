import os

path = r"Temp"
Output_Path = r"Temp"
i = 967
for file in os.listdir(path):
    os.rename(f"{path}/{file}", f"{Output_Path}/Mask_{i:03}.png")
    i += 1  