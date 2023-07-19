import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
import os
import cv2
from pycocotools.coco import COCO
import numpy as np
import webbrowser
import json



# Create a Tkinter window
window = tk.Tk()
window.geometry("500x500")
window.title("COCO Annotation Image Cropper | By Mou")

# Global variables to store the selected paths
ann_file_path = ""
image_folder_path = ""
output_folder_path = ""
path_list = ""

# Function to log text in the log_area with specified formatting
def log_text(text, color=None, bold=False, divider=False):
    # Configure tags for formatting options
    if color:
        log_area.tag_configure(color, foreground=color)
    if bold:
        log_area.tag_configure('bold', font=('Arial', 10, 'bold'))
    if divider:
        log_area.tag_configure('divider', font=('Arial', 10, 'bold'), underline=True)

    # Insert text with formatting
    log_area.configure(state='normal')  # Enable editing temporarily
    if color:
        log_area.insert(tk.END, text, (color,))
    else:
        log_area.insert(tk.END, text)
    if bold:
        log_area.tag_add('bold', 'insert -%dc' % len(text), tk.END)
    if divider:
        log_area.insert(tk.END, '\n\n' + '-' * 40 + '\n\n', ('divider',))
    log_area.see(tk.END)
    log_area.update()
    log_area.configure(state='disabled')  # Disable editing

# Function to handle the "Select annotation file" button
def select_ann_file():
    global ann_file_path
    ann_file_path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
    if ann_file_path:
        ann_file_label.config(text=f"Annotation file selected: {ann_file_path}")

# Function to handle the "Select input images" button
def select_image_folder():
    global image_folder_path
    global path_list
    image_folder_path = filedialog.askdirectory()
    if image_folder_path:
        image_folder_label.config(text=f"Input images folder selected: {image_folder_path}")
 
        folder_name = os.path.basename(image_folder_path)
        parts = folder_name.split('_')
        path_list = parts[:-2] + ['_'.join(parts[-2:])]
        print(path_list)

# Function to handle the "Select output directory" button
def select_output_folder():
    global output_folder_path
    global combined_path
    output_folder_path = filedialog.askdirectory()
    if output_folder_path:
        output_folder_label.config(text=f"Output folder selected: {output_folder_path}")


# Function to handle opening the documentation link
def open_link():
    webbrowser.open_new_tab("https://github.com/mmounirf")

# Function to handle the "Process image" button
def process_images():
    global ann_file_path, image_folder_path, output_folder_path

    # Check if all paths are selected
    if not ann_file_path or not image_folder_path or not output_folder_path:
        messagebox.showerror("Error", "Please select all paths.")
        return

    # Verify if the annotation file exists
    if not os.path.isfile(ann_file_path):
        messagebox.showerror("Error", f"Annotation file '{ann_file_path}' does not exist.")
        return

    # Initialize COCO object
    coco = COCO(ann_file_path)

    # Load all image IDs in the dataset
    image_ids = coco.getImgIds()

    log_area.delete("1.0", tk.END)

    # Iterate over each image
    for img_id in image_ids:
        # Load image information
        img_info = coco.loadImgs(img_id)[0]
        filename = img_info["file_name"].split("/")[-1]
        image_path = os.path.join(image_folder_path, filename)

        log_text(f"Processing '{image_path}'.\n", color='blue', bold=True)

        # Load the image using OpenCV
        image = cv2.imread(image_path)

        # Verify if the image is loaded successfully
        if image is None:
            log_text(f"Failed to load image file '{image_path}'. Skipping.\n", color='blue', bold=True, divider=True)

            continue

        # Load annotations for the image
        ann_ids = coco.getAnnIds(imgIds=img_info["id"])
        annotations = coco.loadAnns(ann_ids)

        # Track parent article id (always start at 1)
        parent_article_id = None

        # Iterate over each annotation
        for ann in annotations:


            filename_without_extension = filename.split('.')[0]

            # Extract the first part of the filename
            first_part = filename_without_extension.split('_')[0]

            # Create the output directory path
            output_directory = os.path.join(output_folder_path, *path_list, first_part)

            output_directory = os.path.normpath(output_directory)

            if "attributes" in ann and "parent" in ann["attributes"]:
                parent_article_id = ann['attributes']['parent']
            else:
                parent_article_id = None
                # Generate coordinates.json file
                coordinates = {
                    "pageId": img_info["id"],
                    "fileId": f"{parent_article_id}_{ann['id']}",
                    "polygon": ann["segmentation"],
                    "boundingBox": ann["bbox"]
                }


                coordinates_path = os.path.join(output_directory, f"{filename_without_extension}_{ann['id']}_coordinates.json")
               

               # Create the directories if they don't exist
                os.makedirs(output_directory, exist_ok=True)

                with open(coordinates_path, 'w') as file:
                    json.dump(coordinates, file)

                log_text(f"Generated coordinates.json file: {coordinates_path}", color='green', bold=True, divider=True)


            # Check if annotation is a bounding box or a polygon
            if (
                "segmentation" in ann
                and isinstance(ann["segmentation"], list)
                and len(ann["segmentation"]) > 0
            ):
                
                log_text("Polygon annotation\n")
  
                # Polygon annotation
                # Get the polygon points
                segmentation = ann["segmentation"]
                polygon_points = np.array(segmentation).reshape((-1, 2)).astype(np.int32)

                # Create a mask from the polygon points
                mask = np.zeros(image.shape[:2], dtype=np.uint8)
                cv2.fillPoly(mask, [polygon_points], (255))

                # Find the bounding rectangle of the polygon
                x, y, w, h = cv2.boundingRect(polygon_points)

                # Crop the region of interest from the image
                cropped_image = image[y : y + h, x : x + w].copy()  # Make a copy of the cropped region

                # Apply the mask to the cropped image
                masked_image = cv2.bitwise_and(
                    cropped_image, cropped_image, mask=mask[y : y + h, x : x + w]
                )

                # Create a white background image
                background = np.ones(cropped_image.shape, dtype=np.uint8) * 255

                # Invert the mask
                inverted_mask = cv2.bitwise_not(mask[y : y + h, x : x + w])

                # Apply the inverted mask to the background image
                background = cv2.bitwise_and(background, background, mask=inverted_mask)

                # Combine the masked image and the background
                result = cv2.bitwise_or(masked_image, background)

                # Update the cropped_image with the result
                cropped_image = result

            else:
                log_text("Bounding box annotation\n")
                # Bounding box annotation
                # Get the bounding box coordinates
                bbox = ann["bbox"]

                # Extract bounding box coordinates
                xmin, ymin, width, height = bbox
                xmax = xmin + width
                ymax = ymin + height

                # Crop the region of interest from the image
                cropped_image = image[int(ymin) : int(ymax), int(xmin) : int(xmax)]


            cropped_file_name = ann['id']
            
            if parent_article_id:
                cropped_file_name = f"{parent_article_id}_{ann['id']}"
            else:
                cropped_file_name = ann['id']

            # Create the output path with the desired file structure
            output_path = os.path.join(output_directory, f"{filename_without_extension}_{cropped_file_name}.jpg")
            
            # Normalize the path separators in the output_path
            output_path = os.path.normpath(output_path)

            # Create the directories if they don't exist
            os.makedirs(output_directory, exist_ok=True)

            cv2.imwrite(output_path, cropped_image)

            log_text(f"Saved cropped image: {output_path}", color='green', bold=True, divider=True)



    messagebox.showinfo("Processing Complete", "Image processing completed successfully.")

# Create buttons and labels
button_ann_file = tk.Button(window, text="Select annotation file", command=select_ann_file)
button_ann_file.pack(anchor=tk.W, pady=(10, 5))

ann_file_label = tk.Label(window, text="No annotation file selected")
ann_file_label.pack(anchor=tk.W)

button_image_folder = tk.Button(window, text="Select input images", command=select_image_folder)
button_image_folder.pack(anchor=tk.W, pady=(10, 5))

image_folder_label = tk.Label(window, text="No input image folder selected")
image_folder_label.pack(anchor=tk.W)

button_output_folder = tk.Button(window, text="Select output directory", command=select_output_folder)
button_output_folder.pack(anchor=tk.W, pady=(10, 5))

output_folder_label = tk.Label(window, text="No output folder selected")
output_folder_label.pack(anchor=tk.W)

button_process_images = tk.Button(window, text="Process images", command=process_images, font=("Arial", 12, "bold"))
button_process_images.pack(anchor=tk.W, pady=(20, 10))

# Create a frame to contain the scrollable text area and the link label
frame = tk.Frame(window)
frame.pack(fill=tk.BOTH, expand=True)

# Create a scrollable text area for logs
log_area = tk.Text(frame, height=10, width=50)
log_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Create a scrollbar and associate it with the log_area
scrollbar = tk.Scrollbar(frame)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
log_area.config(yscrollcommand=scrollbar.set, state='disabled')
scrollbar.config(command=log_area.yview)

# Create a frame for the link label
link_frame = tk.Frame(window)
link_frame.pack()

# Create a label for the link
link_label = tk.Label(link_frame, text="Like it? Support me here", fg="blue", cursor="hand2")
link_label.pack(pady=5)

# Bind the click event to the link label
link_label.bind("<Button-1>", open_link)


# Run the Tkinter event loop
window.mainloop()
