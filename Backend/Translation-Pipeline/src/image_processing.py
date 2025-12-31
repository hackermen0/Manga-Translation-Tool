import os
import cv2

raw_file_path = "./raw"

def ImageProcessing(raw_file_path):
    os.makedirs("./processed/debug", exist_ok=True)

    for image_file in os.listdir(raw_file_path):
        file_name = os.path.splitext(image_file)[0]
        image_path = os.path.join(raw_file_path, image_file)
        image = cv2.imread(image_path)

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)


        # _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)


        # cv2.imshow("", thresh)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()
        # edges = cv2.Canny(thresh, threshold1=30, threshold2=120)

        # print(edges)

        # ---- MSER detection ----
        mser = cv2.MSER_create(delta=20, min_area=300, max_area=5000, max_variation=0.3, min_diversity=0.8)
        mser_regions, _ = mser.detectRegions(gray)
        mser_boxes = [cv2.boundingRect(p.reshape(-1, 1, 2)) for p in mser_regions]


        for (x, y, w, h) in mser_boxes:
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 255), 1)  # Red

        # ---- Contour detection ----
        contours, _ = cv2.findContours(blurred, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 1000 or area > 150000:
                continue

            x, y, w, h = cv2.boundingRect(cnt)
            aspect_ratio = h / float(w) if w != 0 else 0
            # if aspect_ratio < 1.2:
            #     continue

            hull = cv2.convexHull(cnt)
            hull_area = cv2.contourArea(hull)
            solidity = area / float(hull_area) if hull_area != 0 else 0
            if solidity < 0.7:
                continue

            cv2.drawContours(image, [cnt], -1, (0, 255, 0), 2)  # Green

        # ---- Output ----
        output_path = f"./processed/debug/{file_name}_detected.png"
        cv2.imshow(file_name, image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        # cv2.imwrite(output_path, image)
        print(f"[✔] Processed: {file_name}")

ImageProcessing(raw_file_path)
