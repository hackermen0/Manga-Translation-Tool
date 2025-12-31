import cv2
import numpy as np

def color_black_to_red(image_path):
    # Load the image
    img = cv2.imread(image_path)

    if img is None:
        print(f"Error: Could not load image from {image_path}")
        return

    # Convert the image to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Create a mask for the black areas.
    # In your image, the black areas are 0 and white areas are 255.
    # We want to select the black pixels.
    # A simple threshold at 1 will make all pixels with value > 0 as white (255) and 0 as black (0).
    # We need the inverse, so black areas become white in the mask.
    ret, mask = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY_INV)

    # Define the red color (BGR format)
    red = (255, 255, 255)

    # Create a red image of the same size as the original
    red_overlay = np.full(img.shape, red, dtype=np.uint8)

    # Use the mask to select only the black regions from the red_overlay
    # and place them onto a black background.
    red_regions = cv2.bitwise_and(red_overlay, red_overlay, mask=mask)

    # Create a mask for the white areas (outlines) from the original image
    ret_white, white_mask = cv2.threshold(gray, 250, 255, cv2.THRESH_BINARY) # Threshold to get white areas

    # Combine the original white areas with the new red areas
    # First, mask out the black areas from the original image to keep only white and potential other colors
    img_without_black = cv2.bitwise_and(img, img, mask=cv2.bitwise_not(mask))

    # Add the red regions to the image without the original black areas
    output_img = cv2.add(img_without_black, red_regions)

    # Display the result
    cv2.imshow('Original Image', img)
    cv2.imwrite('Final Mask.png', output_img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    # Optionally, save the result
    # cv2.imwrite('output_image_red.png', output_img)

# Call the function with your image file name
image_file_name = r'Final_Result_Black_to_White.png'
color_black_to_red(image_file_name)