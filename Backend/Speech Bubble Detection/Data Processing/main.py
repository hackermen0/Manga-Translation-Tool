import os
import cv2
import json
import numpy as np

# folderPath = r"C:\Users\KIIT\Downloads\Manga109s_released_2023_12_07\Manga109s_released_2023_12_07\images\UnbalanceTokyo"
dataPath = "UnbalanceTokyo.xml"

pageNumber = 3

image = fr"C:\Users\KIIT\Downloads\Manga109s_released_2023_12_07\Manga109s_released_2023_12_07\images\UnbalanceTokyo\{pageNumber:03}.jpg"
print(image)

with open("UnbalanceTokyo.json", "r", encoding="utf-8") as f:
    data = json.load(f)
    data = data["pages"]["page"][3]
    frameData = data['frame']
    textData = data['text']
    bodyData = data['body']
    faceData = data['face']

def coverText(img, x1, y1, x2, y2, padding = 3):
    cv2.rectangle(img, (x1 - padding, y1 - padding), (x2 + padding, y2 + padding), (255, 255, 255), -1)

img = cv2.imread(image)

for text in textData:
    x1 = int(text["xmin"])
    y1 = int(text["ymin"])
    x2 = int(text["xmax"])
    y2 = int(text["ymax"])


    coverText(img, x1, y1, x2, y2, 2)

gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
_, thresh = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

kernel = np.ones((5, 5), np.uint8)
closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

color = cv2.cvtColor(closed, cv2.COLOR_GRAY2BGR)

for text in textData:
    x1 = int(text["xmin"])
    y1 = int(text["ymin"])
    x2 = int(text["xmax"])
    y2 = int(text["ymax"])

    cv2.rectangle(color, (x1, y1), (x2, y2), (255, 0, 255), 1)


roi_mask = np.zeros_like(closed)

for text in textData:
    x1 = int(text["xmin"])
    y1 = int(text["ymin"])
    x2 = int(text["xmax"])
    y2 = int(text["ymax"])
    
    padding = 45
    cv2.rectangle(roi_mask, (x1 - padding, y1 - padding), (x2 + padding, y2 + padding), 255, -1)


masked_closed = cv2.bitwise_and(closed, closed, mask=roi_mask)

cv2.imwrite("Masked Bubble Area.png", masked_closed)
cv2.waitKey(0)


# cv2.imshow("Bubble Mask", color)
# cv2.waitKey(0)
# cv2.destroyAllWindows()
    
# for text in textData:
#     x1 = int(text["xmin"])
#     y1 = int(text["ymin"])
#     x2 = int(text["xmax"])
#     y2 = int(text["ymax"])

#     cv2.rectangle(img, (x1, y1), (x2, y2), (255, 0, 255), 1)

# cv2.imshow("Page 3", img)
# cv2.waitKey(0)
# cv2.destroyAllWindows()



# for image in os.listdir(folderPath):
#     print(image)
#     img = cv2.imread(f"{folderPath}/{image}")
#     # cv2.imshow("funy", img)
#     # cv2.waitKey(0)

# for frame in frameData:
#     cv2.rectangle(img, (int(frame["xmin"]), int(frame["ymin"])), (int(frame["xmax"]), int(frame["ymax"])), (0, 0, 255), 2)

# for body in bodyData:
#     cv2.rectangle(img, (int(body["xmin"]), int(body["ymin"])), (int(body["xmax"]), int(body["ymax"])), (255, 0, 0), 2)

# for face in faceData:
#     cv2.rectangle(img, (int(face["xmin"]), int(face["ymin"])), (int(face["xmax"]), int(face["ymax"])), (220, 6, 145), 2)
