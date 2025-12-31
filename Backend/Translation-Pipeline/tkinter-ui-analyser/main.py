import tkinter as tk
from tkinter import Scrollbar, Listbox, Button, Label, Entry
from PIL import Image, ImageTk, ImageDraw
import os
import ast

path = "./processed/grayscale"
all_coordinates = []

def select_image():
    global selected_index
    selected = listbox1.curselection()
    if selected:
        selected_index = selected[0]  
        filename = listbox1.get(selected_index) + ".jpg"
        img_path = os.path.join(path, filename)
        if os.path.exists(img_path):
            img = Image.open(img_path)  
            photo = ImageTk.PhotoImage(img)
            image_label.config(image=photo)
            image_label.image = photo

            label2.grid(row=0, column=3, padx=10, sticky="n")
            entry1.grid(row=0, column=3, padx=10, pady=(30,0), sticky="n")
            submit_button.grid(row=0, column=3, pady=(60,0), sticky="n")
            clear_button.grid(row=0, column=3, pady=(100, 0), sticky="n")


def clear_all():
    global all_coordinates
    all_coordinates = []

    filename = listbox1.get(selected_index) + ".jpg"
    img_path = os.path.join(path, filename)
    if os.path.exists(img_path):
        img = Image.open(img_path).convert("RGB")
        update_image(img)

def submit_coordinates():
    global all_coordinates
    coordinates = entry1.get()
    print(f"Coordinates: {coordinates}")
  
    try:
        coordinates = ast.literal_eval(coordinates)
        if not isinstance(coordinates, list):
            raise ValueError

        all_coordinates.append(coordinates)
        print(f"All Coordinates: {all_coordinates}")

        print(f"Selcted_Index: {selected_index}")
        filename = os.listdir(path)[selected_index]
        img_path = os.path.join(path, filename)
        if os.path.exists(img_path):
            img = Image.open(img_path).convert("RGB")

            for coords in all_coordinates:
                img = draw_boxes(img, coords)

            update_image(img)

    except (SyntaxError, ValueError):
        print("Invalid coordinate format.")

def draw_boxes(image : Image, coordinates : list):
    draw = ImageDraw.Draw(image)
    draw.polygon(xy=coordinates, outline='red', width=2)
    return image

def update_image(image: Image):
    photo = ImageTk.PhotoImage(image)
    image_label.config(image=photo)
    image_label.image = photo


root = tk.Tk()
root.title("Image Uploader")


listbox1 = Listbox(root, width=25)
scrollbar = Scrollbar(root, command=listbox1.yview)
listbox1.config(yscrollcommand=scrollbar.set)

listbox1.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="n")
scrollbar.grid(row=0, column=1, sticky="ns", pady=(10, 5))
select_button = Button(root, text="Select", command=select_image)
select_button.grid(row=0, column=0, columnspan=2, pady=(200, 10))


image_label = tk.Label(root)
image_label.grid(row=0, column=2, rowspan=3, padx=10, pady=10)


label2 = Label(root, width=25, text="Enter coordinates")
entry1 = Entry(root)
submit_button = Button(root, text="Submit", command=submit_coordinates)
clear_button = Button(root, text="Clear All", command=clear_all)

for i, filename in enumerate(os.listdir(path)):
    listbox1.insert(i, os.path.splitext(filename)[0])



root.mainloop()
