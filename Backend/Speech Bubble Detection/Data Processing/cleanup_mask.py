import cv2
import numpy as np
import os

def clean_mask_cv2(mask_path, save_path):

    mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)

    if mask is None:
        print(f"Error: Could not load mask from {mask_path}")
        return

    _, mask_binary = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)

    
    cv2.imwrite(save_path, mask_binary)


for file in os.listdir(r".\Dataset\Training\Masks"):
    clean_mask_cv2(rf".\Dataset\Training\Masks\{file}", rf".\Temp\{file}")