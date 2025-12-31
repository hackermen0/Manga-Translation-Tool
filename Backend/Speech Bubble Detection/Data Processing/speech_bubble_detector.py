import cv2
import numpy as np
import json
import os


for index, file in enumerate(os.listdir(r".\Mangas\Nekodama\Manga Pages")):

# for pageNumber in range(0, 96):

    image = fr".\Mangas\Nekodama\Manga Pages\{file}"
    print(image)

    with open(r".\Mangas\Nekodama\Nekodama.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        data = data["book"]["pages"]["page"][index]
        
        try:
            frameData = data['frame']
            textData = data['text']
            bodyData = data['body']
            faceData = data['face']
        except KeyError:
            continue

    def coverText(img, x1, y1, x2, y2, padding=3):
        cv2.rectangle(img, (x1 - padding, y1 - padding), (x2 + padding, y2 + padding), (255, 255, 255), -1)


    def fill_from_text_boxes_to_outlines(enclosed_morph_mask, text_boxes, fill_color=(0, 0, 255)):
        """
        Fills regions starting from text boxes outwards, stopping at the white outlines.

        Args:
            enclosed_morph_mask (numpy.ndarray): Grayscale mask with white outlines and black interiors.
            text_boxes (list): List of dictionaries, each with 'xmin', 'ymin', 'xmax', 'ymax'.
            fill_color (tuple): BGR color tuple for filling (e.g., (0, 0, 255) for red).

        Returns:
            numpy.ndarray: A BGR image with the specified fill color from text boxes
                        up to the white outlines, preserving the white outlines.
        """
        h, w = enclosed_morph_mask.shape
        
        # 1. Create a 3-channel (BGR) image initialized with black.
        #    This will be our canvas for the final result.
        result_image = np.zeros((h, w, 3), dtype=np.uint8)
        
        # 2. Draw the white outlines onto this canvas.
        #    The 'enclosed_morph_mask' has white (255) for outlines and black (0) for interiors/background.
        result_image[enclosed_morph_mask == 255] = (255, 255, 255) # Set outlines to white

        # 3. Prepare the mask for floodFill:
        #    We need a mask that defines the boundaries for flood fill.
        #    The flood fill algorithm treats non-zero pixels in its mask as barriers.
        #    So, the white outlines (255) in `enclosed_morph_mask` are perfect barriers.
        #    We need to expand the mask by 2 pixels for floodFill
        flood_fill_mask = np.zeros((h + 2, w + 2), dtype=np.uint8)
        flood_fill_mask[1:h+1, 1:w+1] = enclosed_morph_mask

        # 4. Perform flood fill for each text box.
        for text in text_boxes:
            x1 = int(text["xmin"])
            y1 = int(text["ymin"])
            x2 = int(text["xmax"])
            y2 = int(text["ymax"])

            # Calculate a seed point within the text box
            seed_x = (x1 + x2) // 2
            seed_y = (y1 + y2) // 2
            
            # Ensure seed point is within image bounds
            if 0 <= seed_x < w and 0 <= seed_y < h:
                # Check the pixel at the seed point in result_image to ensure it's not already filled or an outline
                # If it's black (0,0,0), it's eligible for flood fill
                if np.array_equal(result_image[seed_y, seed_x], [0, 0, 0]):
                    # Flood fill starting from the seed point
                    # It will fill with the `fill_color` until it hits white (255,255,255) outlines
                    # The 'flood_fill_mask' prevents it from crossing the outlines.
                    cv2.floodFill(result_image, flood_fill_mask, (seed_x, seed_y), fill_color,
                                loDiff=(1, 1, 1), upDiff=(1, 1, 1), flags=cv2.FLOODFILL_FIXED_RANGE)

        return result_image

    # === MAIN PROCESSING ===

    img = cv2.imread(image)

    # Original image is not directly used for coloring the bubbles, only for context if needed.
    # For the desired output (colored fill inside white outlines on black background),
    # we focus on manipulating masks.

    # Step 1: Prepare the initial mask with covered text
    temp_img_for_threshold = img.copy()
    for text in textData:
        x1 = int(text["xmin"])
        y1 = int(text["ymin"])
        x2 = int(text["xmax"])
        y2 = int(text["ymax"])
        coverText(temp_img_for_threshold, x1, y1, x2, y2, 2)

    # Convert to grayscale and threshold to get potential bubble regions (black text on white/gray)
    gray = cv2.cvtColor(temp_img_for_threshold, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU) # Inverted for black bubbles, white background

    # Create ROI mask around text boxes to focus processing
    roi_mask = np.zeros_like(thresh)
    for text in textData:
        x1 = int(text["xmin"])
        y1 = int(text["ymin"])
        x2 = int(text["xmax"])
        y2 = int(text["ymax"])
        
        padding = 45 # Expanded padding for ROI
        cv2.rectangle(roi_mask, (x1 - padding, y1 - padding), (x2 + padding, y2 + padding), 255, -1)

    # Apply ROI mask to isolate relevant areas for bubble detection
    masked_thresh = cv2.bitwise_and(thresh, thresh, mask=roi_mask)

    # Apply gentle blur cleaning and re-threshold
    blur_clean = cv2.GaussianBlur(masked_thresh, (3, 3), 0)
    _, blur_clean = cv2.threshold(blur_clean, 127, 255, cv2.THRESH_BINARY)

    # === ENCLOSE SPEECH BUBBLES (This creates the white outlines with black interiors) ===
    # Morphological closing to connect parts of outlines and fill small holes within them
    kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
    enclosed_morph = cv2.morphologyEx(blur_clean, cv2.MORPH_CLOSE, kernel_close, iterations=2)

    # === FILL FROM TEXT BOXES TO OUTLINES ===
    # Define the fill color (BGR format: Blue, Green, Red)
    fill_color = (0, 0, 255) # RED

    final_colored_bubbles_from_text = fill_from_text_boxes_to_outlines(enclosed_morph, textData, fill_color)


    final_with_text_boxes_overlay = final_colored_bubbles_from_text.copy()


    black_color = np.array([0, 0, 0])

    # Define the white color (BGR)
    white_color = np.array([255, 255, 255])

    # Create a mask where pixels are black
    # np.all() checks if all channels (B, G, R) are 0 for each pixel
    black_mask = np.all(final_with_text_boxes_overlay == black_color, axis=-1)

    # Replace black pixels with white pixelss
    final_with_text_boxes_overlay[black_mask] = white_color

    # Save the modified image
    output_image_path = f"./Mangas/Nekodama/Final_Result_Black_to_White/{index:03}.png"
    cv2.imwrite(output_image_path, final_with_text_boxes_overlay)

    # for text in textData:
    #     x1 = int(text["xmin"])
    #     y1 = int(text["ymin"])
    #     x2 = int(text["xmax"])
    #     y2 = int(text["ymax"])

    #     cv2.rectangle(final_with_text_boxes_overlay, (x1, y1), (x2, y2), (0, 255, 0), 1)

    # output_image_path = f"./Mangas/Joouari/Final_Result_Black_to_White_With_Overlay/{pageNumber:03}.png"
    # cv2.imwrite(output_image_path, final_with_text_boxes_overlay)

    # for text in textData:
    #     x1 = int(text["xmin"])
    #     y1 = int(text["ymin"])
    #     x2 = int(text["xmax"])
    #     y2 = int(text["ymax"])

    #     cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 1)

    # output_image_path = f"./Mangas/Joouari/Original_Image_With_Overlay/{pageNumber:03}.png"
    # cv2.imwrite(output_image_path, img)

