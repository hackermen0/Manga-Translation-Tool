import os
import shutil

path_label = r"C:\Users\KIIT\Documents\Coding Projects\Python projects\On-going Projects\Manga Translation Tool\Backend\New Speech Bubble Detection\Labels"
path_images = r"C:\Users\KIIT\Documents\Coding Projects\Python projects\On-going Projects\Manga Translation Tool\Backend\New Speech Bubble Detection\Manga"

output_path_labels = r"C:\Users\KIIT\Documents\Coding Projects\Python projects\On-going Projects\Manga Translation Tool\Backend\New Speech Bubble Detection\manga_yolo_dataset\labels\val"
output_path_images = r"C:\Users\KIIT\Documents\Coding Projects\Python projects\On-going Projects\Manga Translation Tool\Backend\New Speech Bubble Detection\manga_yolo_dataset\images\val"

os.makedirs(output_path_labels, exist_ok=True)
os.makedirs(output_path_images, exist_ok=True)

count = 0

for i in os.listdir(path_label)[72:]:
    manga_label_dir = os.path.join(path_label, i)

    if not os.path.isdir(manga_label_dir):
        continue

    for j in os.listdir(manga_label_dir):
        src_label_path = os.path.join(path_label, i, j)
        base_filename = os.path.splitext(j)[0]

        src_image_path = os.path.join(path_images, i, f"{base_filename}.jpg")

        if not os.path.exists(src_image_path):
            src_image_path = os.path.join(path_images, i, f"{base_filename}.png")

        if not os.path.exists(src_image_path):
            print(f"Warning: Image file missing for label {src_label_path}")
            continue

        dst_image_path = os.path.join(output_path_images, f"{count}.jpg")
        dst_label_path = os.path.join(output_path_labels, f"{count}.txt")

        print(f"Copying validation pair #{count}: {i}/{base_filename}")
        shutil.copy(src_image_path, dst_image_path)
        shutil.copy(src_label_path, dst_label_path)

        count += 1
