import os
import cv2
from PIL import Image

processed_image_folder = "./processed/grayscale"

for image_file in os.listdir(processed_image_folder):

    print(image_file)
    
    image_path = os.path.join(processed_image_folder, image_file)
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Optional: Thresholding (binarization) to clean up for better contour detection
    _, thresh = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY_INV)

    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    print("Total contours detected:", len(contours))

    for i, contour in enumerate(contours):
        area = cv2.contourArea(contour)
        if area < 500:
            continue

        x, y, w, h = cv2.boundingRect(contour)
        aspect_ratio = max(w / h, h / w)
        if aspect_ratio > 5:
            continue

        if hierarchy[0][i][3] != -1:
            continue

        cv2.drawContours(image, [contour], -1, (0, 0, 255), 2)

    # Convert to RGB for PIL
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    Image.fromarray(image_rgb).show()
