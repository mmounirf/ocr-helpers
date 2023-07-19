import os
from tkinter import filedialog, messagebox
import tkinter.ttk as ttk
import tkinter as tk
import re
from logger import logger
import shutil
from fpdf import FPDF
import glob
from PIL import Image, ImageFilter

files_tree = {}
input_directory = ""
issues = []

def group_page(row, path, issue_day, page_number):
    parent_path = os.path.dirname(path)
    if parent_path not in issues:
        # Create a new list for the issue_day if it doesn't exist
        issues[parent_path] = []
    
    # Append the page_number to the corresponding issue_day list
    issues[parent_path].append([page_number, row])


def select_input_directory():
    global input_directory, files_tree
    input_directory = filedialog.askdirectory(title="Select Input Folder")
    if input_directory:
        files_tree = {}
        process_issue_day_path()

def process_issue_day_path():
    # Match all issue_day directories
    issue_day_path_regex = r"[\\/]([^\\/]+)[\\/](\d{4})[\\/](\d{2})[\\/](\d{2}_\d+)$"

    # Recrusively loop through the selected input directory
    for root, _, files in os.walk(input_directory):
      
        # Normalize root path and match it against issue_day_path_regex
        path = os.path.normpath(root)
        matches = re.search(issue_day_path_regex, root)
        if(matches):
            # Add the matched path to issues array
            issues.append(path)
    # After consturing array of issues, lets process pages
    process_pages()
    process_articles_preview()
    process_articles_thumbnails()
    messagebox.showinfo("Task completed", "Unprotected folder processing completed successfully.")
    exit()

def process_pages():
    logger.yellow(' -------------------- Processing cover and pages -------------------- ')
    for path in issues:
        page_files = glob.glob(f'{path}/*.jpg')
        page_image_regex = r"\\([^\\]+)\\(\d{4})\\(\d{2})\\(\d{2}_\d+)\\(\d+)\.jpg$"
        cover_page = page_files[0]

        matches = re.search(page_image_regex, cover_page)

        provider_name = matches.group(1)
        year = matches.group(2)
        month = matches.group(3)
        issue_day = matches.group(4)

        unprotected_path = os.path.normpath(os.path.join(path, 'unprotected'))
        unprotected_cover_name = f"newspaper_{provider_name}_{provider_name}_{year}_{month}_{issue_day}_cover.jpg"
        unprotected_cover_file = os.path.normpath(os.path.join(unprotected_path, unprotected_cover_name))

        os.makedirs(os.path.dirname(unprotected_cover_file), exist_ok=True)

        cover_image = Image.open(cover_page)

        cover_image.convert('RGB')
        width, height = cover_image.size
        aspect_ratio = width / height
        resized_width = 500
        resized_height = int(resized_width / aspect_ratio)
        resized_cover_image = cover_image.resize((resized_width, resized_height))

        # Calculate the cropping coordinates
        left = 0
        top = 0
        right = 500
        bottom = 280

        cropped_cover_image = resized_cover_image.crop((left, top, right, bottom))
        cropped_cover_image.save(unprotected_cover_file, optimize=True, comment="Oppa")

        # Keep the generated image size under 2Mb
        logger.blue(f"Generating {unprotected_cover_name}")


        for page in page_files:
            matches = re.search(page_image_regex, page)

            provider_name = matches.group(1)
            year = matches.group(2)
            month = matches.group(3)
            issue_day = matches.group(4)
            page_number = matches.group(5)

            unprotected_page_name = f"newspaper_{provider_name}_{provider_name}_{year}_{month}_{issue_day}_page_{page_number}.jpg"
            unprotected_page_file = os.path.normpath(os.path.join(unprotected_path, unprotected_page_name))

            os.makedirs(os.path.dirname(unprotected_page_file), exist_ok=True)

            page_image = Image.open(page)
            
            cover_image.convert('RGB')
            page_image.save(unprotected_page_file, optimize=True, comment="Oppa")
            # Keep the generated image size under 2Mb
            logger.blue(f"Generating {unprotected_page_name}")
            while os.path.getsize(unprotected_page_file) > 1024 * 1024 * 2:
                logger.orange(f"Reducing file {unprotected_page_name} under 2MB. File size is {round(os.path.getsize(unprotected_page_file) / (1024 * 1024), 2)}MB.")
                page_image.thumbnail((int(page_image.size[0]/2),int(page_image.size[1]/2)))
                page_image.save(unprotected_page_file, optimize=True, comment="Oppa")
            logger.green(f"Generating {unprotected_page_name} | File size {round(os.path.getsize(unprotected_page_file) / (1024 * 1024), 2)}MB")






def process_articles_preview():
    logger.yellow(' -------------------- Processing articles preview -------------------- ')
    article_file_regex = r"^\d{3}_\d+\.jpg$"
     
    for root, _, files in os.walk(input_directory): 
        for file in files:
            is_article = re.match(article_file_regex, file)  
            if(is_article):
                article_path_regex = r"\\([^\\]+)\\(\d{4})\\(\d{2})\\(\d{2}_\d+)\\(\d{3})\\(\d{1,3}_\d{1,3})\.jpg$"
                matches = re.search(article_path_regex, os.path.normpath(os.path.join(root, file)))
                provider_name = matches.group(1)
                year = matches.group(2)
                month = matches.group(3)
                issue_day = matches.group(4)
                page_number = matches.group(5)

                root_path = os.path.dirname(root)

                unprotected_article_path = os.path.normpath(os.path.join(root_path, 'unprotected'))

                
                article_file = os.path.normpath(os.path.join(root, file))
                article_id = file.split("_")[1].split(".")[0]

                # Generating Article Preview
                uprotected_article_preview_name = f"newspaper_{provider_name}_{provider_name}_{year}_{month}_{issue_day}_page_{page_number}_art{article_id}_preview.jpg"
                uprotected_article_preview_file = os.path.normpath(os.path.join(unprotected_article_path, uprotected_article_preview_name))


                os.makedirs(os.path.dirname(uprotected_article_preview_file), exist_ok=True)

                article_image = Image.open(article_file)
                article_image.convert('RGB')
                
                width, height = article_image.size

                aspect_ratio = width / height
                target_height = int(800 / aspect_ratio)


                article_image = article_image.resize((800, target_height))
                
                average_size = (article_image.size[0] + article_image.size[1]) / 2
                blurr_factor = average_size / 100
                blurred_image = article_image.filter(ImageFilter.GaussianBlur(blurr_factor))
                blurred_image.save(uprotected_article_preview_file, optimize=True, comment="Oppa")
                # Keep the generated image size under 2Mb
                logger.blue(f"Generating article preview {uprotected_article_preview_name}")


def process_articles_thumbnails():
    logger.yellow(' -------------------- Processing articles thumbnails -------------------- ')
    article_file_regex = r"^\d{3}_\d+\.jpg$"
     
    for root, _, files in os.walk(input_directory): 
        for file in files:
            is_article = re.match(article_file_regex, file)  
            if(is_article):
                article_path_regex = r"\\([^\\]+)\\(\d{4})\\(\d{2})\\(\d{2}_\d+)\\(\d{3})\\(\d{1,3}_\d{1,3})\.jpg$"
                matches = re.search(article_path_regex, os.path.normpath(os.path.join(root, file)))
                provider_name = matches.group(1)
                year = matches.group(2)
                month = matches.group(3)
                issue_day = matches.group(4)
                page_number = matches.group(5)

                root_path = os.path.dirname(root)

                unprotected_article_path = os.path.normpath(os.path.join(root_path, 'unprotected'))

                
                article_file = os.path.normpath(os.path.join(root, file))
                article_id = file.split("_")[1].split(".")[0]
        
                # Generating Article Thumbnail
                uprotected_article_thumbnail_name = f"newspaper_{provider_name}_{provider_name}_{year}_{month}_{issue_day}_page_{page_number}_art{article_id}_thumbnail.jpg"
                uprotected_article_thumbnail_file = os.path.normpath(os.path.join(unprotected_article_path, uprotected_article_thumbnail_name))

                os.makedirs(os.path.dirname(uprotected_article_thumbnail_file), exist_ok=True)

                article_thumbnail = Image.open(article_file)
                article_thumbnail.convert('RGB')
                
                width, height = article_thumbnail.size
                aspect_ratio = width / height
                resized_width = 500
                resized_height = int(resized_width / aspect_ratio)
                resized_article_thumbnail = article_thumbnail.resize((resized_width, resized_height))

                # Calculate the cropping coordinates
                left = 0
                top = 0
                right = 500
                bottom = 280

                cropped_article_thumbnail = resized_article_thumbnail.crop((left, top, right, bottom))
                cropped_article_thumbnail.save(uprotected_article_thumbnail_file, optimize=True, comment="Oppa")

                logger.cyan(f"Generating article thumbnail {uprotected_article_thumbnail_name}")


# Run the main window loop
select_input_directory()
