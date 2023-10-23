import os
from PIL import Image
from tkinter import Tk, filedialog, Button, Label


def convert_png_to_jpg(input_folder, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for filename in os.listdir(input_folder):
        if filename.lower().endswith(".png"):
            png_path = os.path.join(input_folder, filename)
            jpg_filename = filename[:-4] + ".jpg"
            jpg_path = os.path.join(output_folder, jpg_filename)
            
            img = Image.open(png_path)
            
            # Create a new image with white background
            new_img = Image.new("RGB", img.size, "white")
            new_img.paste(img, img)

            new_img.save(jpg_path, "JPEG")

            print(f"Converted {png_path} to {jpg_path}")


def select_input_folder():
    input_folder = filedialog.askdirectory()
    input_label.config(text="Input Folder: " + input_folder)
    return input_folder


def select_output_folder():
    output_folder = filedialog.askdirectory()
    output_label.config(text="Output Folder: " + output_folder)
    return output_folder


def convert_folders():
    input_folder = input_label.cget("text")[14:]
    output_folder = output_label.cget("text")[15:]
    convert_png_to_jpg(input_folder, output_folder)


# Create GUI window
root = Tk()
root.title("PNG to JPG Converter")
root.geometry("600x360")  # Set window size to 640x480

# Input Folder Selection
input_label = Label(root, text="Input Folder: None")
input_label.pack()
select_input_button = Button(root, text="Select Input Folder", command=select_input_folder)
select_input_button.pack()

# Output Folder Selection
output_label = Label(root, text="Output Folder: None")
output_label.pack()
select_output_button = Button(root, text="Select Output Folder", command=select_output_folder)
select_output_button.pack()

# Convert Button
convert_button = Button(root, text="Convert", command=convert_folders)
convert_button.pack()

# Start GUI event loop
root.mainloop()
