import os
import sys
import json
from tkinter.ttk import Treeview
from tkinter import filedialog, messagebox
import tkinter.ttk as ttk
import tkinter as tk
import base64
import asyncio
import aiohttp


files_tree = {}
input_directory = ""
children = {}

def select_input_directory():
    global input_directory, files_tree, children
    input_directory = filedialog.askdirectory(title="Select Input Folder")
    if input_directory:
        children = {}
        files_tree = {}
        tree.delete(*tree.get_children())
        tree.update()
        directory_label.config(text=f"Input Directory: {input_directory}")
        read_files()

def read_files():
    index = 0
    for root, _, files in os.walk(input_directory):

        for file in files:
            if file.endswith(".jpg"):
                index += 1
                is_parent = len(file.split('_')) < 3


                if is_parent:
                    print(f"{file} is parent ")
                    row = tree.insert('', 'end', values=(index, '', os.path.normpath(root), file, 'Pending'))
                    files_tree[file] = []
                else:
                    parent = '_'.join(file.split('_')[:-1]) + '.jpg'
                    print(f"{file} is child for parent {parent}")
                    row = tree.insert('', 'end', values=(index, parent, os.path.normpath(root), file, 'Pending'))

                    if parent not in files_tree:
                        print(f"{parent} does not exist in the files_tree. Intializing.")
                        files_tree[parent] = []
                        continue
                    print(f"{parent} does exist in the files_tree. Append {file}")
                    files_tree[parent].append(file)



async def process_files():
    async with aiohttp.ClientSession() as session:
        for row in tree.get_children():
            item_values  = tree.item(row, 'values')
            parent = item_values[1]
            
            is_child = parent != ''

            file_path = os.path.normpath(os.path.join(item_values[2], item_values[3]))
            
            parent_path = os.path.normpath(os.path.join(file_path[:file_path.rindex("\\")+1], parent.replace('.jpg', '.json')))

            if(is_child):
                if parent_path not in children:
                    children[parent_path] = [file_path.replace('.jpg', '.json')]
                else:
                    children[parent_path].append(file_path.replace('.jpg', '.json'))

            print('Start processing file: ', file_path)
            tree.set(row, 'Status', 'Processing')
            tree.update()
            await vision_request(session, file_path)
            tree.set(row, 'Status', 'Completed')
            tree.update()
        
    merge_child_files()
    messagebox.showinfo('OCR Completed!', "OCR Completed!")
    

def merge_child_files():
    for (key, values) in children.items():

        merged_content = []
        for value in values:
            
            with open(value, encoding='utf-8') as file:
                file_content = json.load(file)
                
            merged_content.append(file_content)
            
        with open(key, 'w', encoding='utf-8') as file:
            file.write(json.dumps(merged_content, indent=2, ensure_ascii=False))


async def vision_request(session, file_path):
    # Send the image file to Google Cloud Vision for OCR processing
    with open(file_path, "rb") as image_file:
        content = image_file.read()
 
    # Prepare the request URL
    url = "https://vision.googleapis.com/v1/images:annotate"
    params = {
        "key": ""
    }
    headers = {
        "Content-Type": "application/json"
    }

    # Prepare the request payload
    request_data = {
        "requests": [
            {
                "image": {
                    "content": base64.b64encode(content).decode()
                },
                "features": [
                    {
                        "type": "DOCUMENT_TEXT_DETECTION"
                    }
                ],
                "imageContext": {
                    "languageHints": ["ar"]
                }
            }
        ]
    }

    print(f"Sending {file_path} to Google Cloud Vision")
    # Send the request to the Vision API
    async with session.post(url, params=params, headers=headers, json=request_data) as response:
        response_json = await response.json()

    # Save the response JSON to a file
    file_name = os.path.splitext(os.path.basename(file_path))[0]
    output_file_path = file_path.replace('.jpg', '.json')
    with open(output_file_path, "w", encoding="utf-8") as json_file:
        json.dump(response_json, json_file, ensure_ascii=False, indent=2)

    print(f"Generated {file_path} OCR json file")

# Button to start processing the files
def process_files_button():
    asyncio.run(process_files())



# Create the main window
window = tk.Tk()
window.title("Image Processing App")
window.geometry("800x600")

# Create the requests table
tree = Treeview(window, columns=('Index', 'Parent', 'Path', 'File', 'Status'), show='headings')



# tree.heading('Index', text='#')
tree.column("Index", width=50, stretch=False)
tree.heading('Index', text='Index')


tree.column("Parent", width=100, stretch=False)
tree.heading('Parent', text='Parent')

tree.heading('Path', text='Path')
tree.heading('File', text='File')
tree.heading('Status', text='Status')
tree.pack(fill='both', expand=True)

# Button to trigger file selection dialog
select_button = ttk.Button(window, text="Select Directory", command=select_input_directory)
select_button.pack(pady=(10, 5))

# Label to display the selected input directory
directory_label = ttk.Label(window, text="Input Folder: Not Selected")
directory_label.pack()

# Button to start processing the files
process_button = ttk.Button(window, text="Start Processing", command=process_files_button)
process_button.pack(pady=(10, 5))

# Run the main window loop
window.mainloop()
