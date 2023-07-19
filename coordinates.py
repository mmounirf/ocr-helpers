import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import json

def draw_polygon():
    try:
        points = json.loads(points_text.get("1.0", tk.END))
        if not isinstance(points, list):
            raise ValueError("Invalid JSON format")
        for point in points:
            if not isinstance(point, dict) or "x" not in point or "y" not in point:
                raise ValueError("Invalid JSON format")
    except ValueError as e:
        print("Invalid JSON:", e)
        return

    canvas.delete("polygon")
    for i in range(len(points)):
        x1 = round((points[i]["x"] - image_x_offset) * image_scale_factor) + canvas_x_offset
        y1 = round((points[i]["y"] - image_y_offset) * image_scale_factor) + canvas_y_offset
        x2 = round((points[(i+1) % len(points)]["x"] - image_x_offset) * image_scale_factor) + canvas_x_offset
        y2 = round((points[(i+1) % len(points)]["y"] - image_y_offset) * image_scale_factor) + canvas_y_offset
        canvas.create_line(x1, y1, x2, y2, fill="green", width=2, tags="polygon")

def select_image():
    file_path = filedialog.askopenfilename(filetypes=[("JPEG Files", "*.jpg")])
    if file_path:
        # Set a higher limit for decompression
        Image.MAX_IMAGE_PIXELS = None
        global image_scale_factor, image_x_offset, image_y_offset, canvas_x_offset, canvas_y_offset
        image = Image.open(file_path)
        image_width, image_height = image.size
        canvas_width, canvas_height = 800, 600
        scale_x = canvas_width / image_width
        scale_y = canvas_height / image_height
        image_scale_factor = min(scale_x, scale_y)
        image_resized_width = int(image_width * image_scale_factor)
        image_resized_height = int(image_height * image_scale_factor)
        image_x_offset = (canvas_width - image_resized_width) // 2
        image_y_offset = (canvas_height - image_resized_height) // 2
        canvas_x_offset = image_x_offset
        canvas_y_offset = image_y_offset
        image = image.resize((image_resized_width, image_resized_height))
        photo = ImageTk.PhotoImage(image)
        canvas.create_image(canvas_x_offset, canvas_y_offset, anchor="nw", image=photo)
        canvas.image = photo  # To prevent the image from being garbage collected

root = tk.Tk()
root.title("Polygon Drawing App")

# Frame for the image
canvas_frame = tk.Frame(root)
canvas_frame.pack(side="top", pady=10)

# Canvas for displaying the image
canvas = tk.Canvas(canvas_frame, width=800, height=600)
canvas.pack()

# Button to select an image
select_button = tk.Button(root, text="Select Image", command=select_image)
select_button.pack()

# Text area for entering the JSON points
points_label = tk.Label(root, text="Enter JSON Points:")
points_label.pack()

points_text = tk.Text(root, height=6)
points_text.pack()

# Button to draw the polygon
draw_button = tk.Button(root, text="Draw Polygon", command=draw_polygon)
draw_button.pack()

# Global variables for image scaling and offsets
image_scale_factor = 1.0
image_x_offset = 0
image_y_offset = 0
canvas_x_offset = 0
canvas_y_offset = 0

root.mainloop()
