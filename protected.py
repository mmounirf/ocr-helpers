import os
from tkinter import filedialog, messagebox
import tkinter.ttk as ttk
import tkinter as tk
import re
from logger import logger
import shutil
from fpdf import FPDF
import glob

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

def process_pages():
    for path in issues:
        page_files = glob.glob(f'{path}/*.jpg')

        page_image_regex = r"\\([^\\]+)\\(\d{4})\\(\d{2})\\(\d{2}_\d+)\\(\d+)\.jpg$"

        for file in page_files:
            matches = re.search(page_image_regex, file)
            if matches:
                provider_name = matches.group(1)
                year = matches.group(2)
                month = matches.group(3)
                issue_day = matches.group(4)
                page_number = matches.group(5)

            protected_page_name = f"newspaper_{provider_name}_{provider_name}_{year}_{month}_{issue_day}_page_{page_number}.jpg"
            protected_path = os.path.normpath(os.path.join(path, 'protected'))
            protected_page_file = os.path.normpath(os.path.join(protected_path, protected_page_name))

            # Make destination path if not exists
            os.makedirs(os.path.dirname(protected_page_file), exist_ok=True)

            # Copy and rename the cover_file
            shutil.copy2(file, protected_page_file)
            logger.blue(f"Page generated {protected_page_file} from {file}")
            logger.blue(f"-----------------------------------------------------------")


            if(os.path.exists(os.path.normpath(os.path.join(path, page_number)))):
                process_articles(os.path.normpath(os.path.join(path, page_number)))

        # PDF file
        protected_pdf_name = f"newspaper_{provider_name}_{provider_name}_{year}_{month}_{issue_day}.pdf"
        protected_pdf_path = os.path.normpath(os.path.join(path, 'protected', protected_pdf_name))

        generate_pdf(protected_pdf_name, protected_pdf_path, page_files)

    messagebox.showinfo("Task completed", "Protected folder processing completed successfully.")
    exit()
        


    
def generate_pdf(name, path, pages):
    file = ''
    pdf = FPDF()

    for page in pages:
        pdf.add_page()
        pdf.image(page, x=0, y=0, w=pdf.w, h=pdf.h)
        file = page

    logger.orange(f"It will take few minutes Generating {name} ... Please wait!")
    pdf.output(path, "F")
    logger.orange(f"Generated {os.path.normpath(os.path.join(path, file))}")


def process_articles(path):
    articles_path_regex = r"\\([^\\]+)\\(\d{4})\\(\d{2})\\(\d{2}_\d+)\\(\d{3})$"

    path_matches = re.search(articles_path_regex, path)
    if path_matches:
        provider_name = path_matches.group(1)
        year = path_matches.group(2)
        month = path_matches.group(3)
        issue_day = path_matches.group(4)
        page_number = path_matches.group(5)
    
        files_in_page_directory = os.listdir(path)
        root_path = os.path.dirname(path)


        all_matches = []
        for article in files_in_page_directory:
            article_file_regex = r"^\d{3}_\d+\.jpg$"
            is_article = re.match(article_file_regex, article)           
            
            
            if(is_article):
                article_file = os.path.normpath(os.path.join(path, article))
                article_id = article.split("_")[1].split(".")[0]
                protected_article_name = f"newspaper_{provider_name}_{provider_name}_{year}_{month}_{issue_day}_page_{page_number}_art{article_id}.jpg"
                all_matches.append(article)

                # Construct file path
                protected_article_path = os.path.normpath(os.path.join(root_path, 'protected'))
                protected_article_file = os.path.normpath(os.path.join(protected_article_path, protected_article_name))

                # Make destination path if not exists
                os.makedirs(os.path.dirname(protected_article_file), exist_ok=True)
          
                # Copy and rename the cover_file
                shutil.copy2(article_file, protected_article_file)
                print("------------------------------------------")
                logger.yellow(f"Generated {protected_article_file} from {article}")



# Run the main window loop
select_input_directory()
