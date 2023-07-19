import os
from tkinter import filedialog, messagebox

import re
from logger import logger
import json
from datetime import datetime, date
import asyncio
import aiohttp
import sys

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
    process_local_data()
    asyncio.run(process_remote_data())
    messagebox.showinfo("Task completed", "Content folder processing completed successfully.")
    exit()



def convert_coordinates(coordinates):
    formatted_coordinates = []
    # Check if the input is a bounding box (4 coordinates) or a polygon (>4 coordinates)
    if len(coordinates) == 4:
        x, y, w, h = coordinates
        x = round(x)
        y = round(y)
        w = round(w)
        h = round(h)

        formatted_coordinates = [
            {'x': x, 'y': y},
            {'x': x + w, 'y': y},
            {'x': x + w, 'y': y + h},
            {'x': x, 'y': y + h},
        ]

    else:
        # In case of a polygon, you can use a nested loop to create pairs of coordinates
        for i in range(0, len(coordinates), 2):
            x = round(coordinates[i])
            y = round(coordinates[i + 1])
            formatted_coordinates.append({'x': x, 'y': y})

    return formatted_coordinates

    
def get_coordinates(json_content):
    if len(json_content["polygon"])==0:
        return convert_coordinates(json_content["boundingBox"])
    else:
        return convert_coordinates(json_content["polygon"][0])
    
def get_response_text(ocr_json_response):
    if(len(ocr_json_response) > 1):
        return "\r\n".join(response["fullTextAnnotation"]["text"] for item in ocr_json_response for response in item["responses"])
    else:
        return ocr_json_response['responses'][0]["fullTextAnnotation"]["text"]
    

def get_poly_y_range(poly):
    y_list = []
    for v in poly['vertices']:
        if v['y'] not in y_list:
            y_list.append(v['y'])
    return y_list


def get_poly_x(poly):
    return poly['vertices'][0]['x']


def get_lines(response):
    lines = []
    current_line = None

    for annotation in response['textAnnotations'][1:]:
        description = annotation.get("description", "").strip()
        vertices = annotation.get("boundingPoly", {}).get("vertices", [])

        if not description or len(vertices) != 4:
            continue

        # Extract the top-left and bottom-right coordinates
        top_left = (vertices[0].get("x", 0), vertices[0].get("y", 0))
        bottom_right = (vertices[2].get("x", 0), vertices[2].get("y", 0))

        if not current_line:
            # Start a new line
            current_line = {
                "line number": len(lines) + 1,
                "line_coordinates": {
                    "top_left": top_left,
                    "bottom_right": bottom_right,
                    "top_right": (bottom_right[0], top_left[1]),
                    "bottom_left": (top_left[0], bottom_right[1]),
                },
                "line_text": description,
            }
        else:
            # Check if the current annotation is within the same line based on vertical position
            if top_left[1] <= current_line["line_coordinates"]["bottom_right"][1]:
                # Extend the line's text
                current_line["line_text"] += " " + description
                current_line["line_coordinates"]["bottom_right"] = bottom_right
                current_line["line_coordinates"]["top_right"] = (bottom_right[0], top_left[1])
            else:
                # Save the completed line and start a new line
                lines.append(current_line)
                current_line = {
                    "line number": len(lines) + 1,
                    "line_coordinates": {
                        "top_left": top_left,
                        "bottom_right": bottom_right,
                        "top_right": (bottom_right[0], top_left[1]),
                        "bottom_left": (top_left[0], bottom_right[1]),
                    },
                    "line_text": description,
                }

    # Add the last line, if any
    if current_line:
        lines.append(current_line)

    return {"lines": lines}


def process_line_coordinates(ocr_json_response):
    lines = [];
    if(len(ocr_json_response) > 1):
        for item in ocr_json_response:
            for response in item["responses"]:
                lines.append(get_lines(response))
                    
        return lines
    else:
        lines = get_lines(ocr_json_response['responses'][0])
        return lines

def process_local_data():
    logger.yellow(' -------------------- Processing local data -------------------- ')

    for root, _, files in os.walk(input_directory):
        for file in files:
            coordinates_file_json_files = r"\\([^\\]+)\\(\d{4})\\(\d{2})\\(\d{2}_\d+)\\(\d{3})\\(\d{3}_\d{1,3}_coordinates).json$"
            ocr_json_file_name = file.replace('_coordinates', '')
       
            ocr_json_file = os.path.normpath(os.path.join(root, ocr_json_file_name));
            coordinates_json_file = os.path.normpath(os.path.join(root, file));

            json_matches = re.search(coordinates_file_json_files, coordinates_json_file)
            if(json_matches):

                logger.orange(f"Getting data from {file} and {ocr_json_file_name}")
                
                provider_name = json_matches.group(1)
                year = json_matches.group(2)
                month = json_matches.group(3)
                issue_day = json_matches.group(4)
                day = issue_day.split("_")[0]
                issue = issue_day.split("_")[1]
                page_number = json_matches.group(5)
                coordinates_file = json_matches.group(6)

                ocr_json_file_obj = open(ocr_json_file, encoding='utf-8')
                ocr_json_content = json.load(ocr_json_file_obj)

                coordinates_json_file_obj = open(coordinates_json_file)
                coordinates_json_content = json.load(coordinates_json_file_obj)

                parent_directory = os.path.normpath(os.path.dirname(root))

                name_base = f"newspaper_{provider_name}_{provider_name}_{year}_{month}_{issue_day}"
                page_base_name = f"{name_base}_page_{page_number}"
                article_base_name = f"{page_base_name}_art{coordinates_json_content['fileId']}"

                

                json_data = {
                    "batch_info": {
                        "batch_version": "1",
                        "batch_date": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")
                    },
                    "cover_name": f"{name_base}_cover.jpg",
                    "document_date_utc": datetime(int(year), int(month), int(day)).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                    "document_id": article_base_name,
                    "edition_number": issue,
                    "document_title": "",
                    "author": [],
                    "files_info": {
                        "pages": [coordinates_json_content['pageId']],
                        "ocr_text": get_response_text(ocr_json_content),
                        "post_ocr_text": "",
                        "image_name": f"{article_base_name}.jpg",
                        "article_coordinates": get_coordinates(coordinates_json_content),
                        "lines": process_line_coordinates(ocr_json_content),
                        "thumbnail_name": f"{article_base_name}_thumbnail.jpg",
                    },
                    "pages": [{
                        "image_name": f"{page_base_name}.jpg",
                        "page_number": coordinates_json_content['pageId'],
                        "thumbnail_name": f"{article_base_name}_thumbnail.jpg",
                        "preview_name": f"{article_base_name}_preview.jpg",
                    }],
                    "pdf_file": f"{name_base}.pdf",
                    "preview": [{
                        "preview_name": f"{article_base_name}_preview.jpg"
                    }],
                    "provider_id": f"{provider_name}",
                    "provider_name_ar": "الأهرام",
                    "provider_name_en": f"{provider_name}",
                    "publish_country_ar": "مصر",
                    "publish_country_en": "Egypt",
                    "source_format_ar": "صحيفة",
                    "source_format_en": "Newspaper",
                    "source_language_name_ar": "العربية",
                    "source_language_name_en": "Arabic",
                    "source_name": "الأهرام",
                    "source_name_norm_ar": "الأهرام",
                    "source_nationality_ar": "مصر",
                    "source_nationality_en": "Egypt",
                    "source_periodicity_release_ar": "يومي",
                    "source_periodicity_release_en": "Daily",
                    "media_type_en": "Print",
                    "document_type_en": "newspaper",
                    "ocr_info": [
                        {
                        "author": "Oppa",
                        "ocr_version": "1",
                        "batch_date": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")
                        }
                    ],
                    "transaction_id": f"{year}-{month}-{day}",
                    "Major_version": "1",
                    "Minor_version": "3",
                    "issue_date": f"{year}-{month}-{day}"
                }




                artilce_json_file = f"newspaper_{provider_name}_{provider_name}_{year}_{month}_{issue_day}_page_{page_number}_art{coordinates_json_content['fileId']}.json"
                
                article_json_file_path = os.path.join(parent_directory, 'content', artilce_json_file)
            
            # Create the directories if they don't exist
                os.makedirs(os.path.dirname(article_json_file_path), exist_ok=True)

                with open(article_json_file_path, 'w', encoding='utf-8') as file:
                    json.dump(json_data, file, ensure_ascii=False, indent=2)

    logger.yellow(' -------------------- Processing local data completed -------------------- ')




async def process_remote_data():
    logger.yellow(' -------------------- Processing remote data -------------------- ')
    async with aiohttp.ClientSession() as session:
        for root, _, files in os.walk(input_directory):
            for file in files:

                ocr_json_files = r"\\([^\\]+)\\(\d{4})\\(\d{2})\\(\d{2}_\d+)\\(\d{3})\\\d{3}_(\d{1,3}).json$"
                json_file = os.path.normpath(os.path.join(root, file));
                json_matches = re.search(ocr_json_files, json_file)
                
                if(json_matches):        
                    provider_name = json_matches.group(1)
                    year = json_matches.group(2)
                    month = json_matches.group(3)
                    issue_day = json_matches.group(4)
                    day = issue_day.split("_")[0]
                    issue = issue_day.split("_")[1]
                    page_number = json_matches.group(5)
                    article_id = json_matches.group(6)

                    parent_directory = os.path.normpath(os.path.dirname(root))

                    request_query = f"{provider_name}_{year}_{month}_{issue_day}_{page_number}_{page_number}_{article_id}"

                    logger.cyan(f"Getting article data from server {request_query}")

                    article_data = await get_article_request(session, request_query)

                    saved_json_file = f"newspaper_{provider_name}_{provider_name}_{year}_{month}_{issue_day}_page_{page_number}_art{article_id}.json"

                    file_path = os.path.normpath(os.path.join(parent_directory, 'content', saved_json_file))
    
                    with open(file_path, 'r+', encoding='utf-8') as file:
                        file_data = json.load(file)

                        file_data['author'] = list(filter(None, article_data['authors']))
                        file_data['document_title'] = article_data['title']
                        file_data['files_info']['post_ocr_text'] = article_data['content']

                        file.seek(0)
                        json.dump(file_data, file, ensure_ascii=False, indent=2)                  
            
    logger.yellow(' -------------------- Processing remote data completed -------------------- ')






async def get_article_request(session, article_id):
 
    # Prepare the request URL
    url = f"https://us-central1-oppa-ai-hub.cloudfunctions.net/getArticle?id={article_id}"

    headers = {
        "Content-Type": "application/json"
    }


    # Send the request to the Vision API
    async with session.get(url, headers=headers) as response:
        response_json = await response.json()
        return response_json



    # json = {'date': {'month': '06', 'year': '1981', 'label': '1981-06-01', 'day': '01'}, 'pageNumber': '011', 'file': {'bucket': 'oppa-ai-hub.appspot.com', 'path': 'ahram/1981/06/01_34504/011/011_87.jpg', 'fileName': '011_87', 'mediaLink': 'https://storage.googleapis.com/download/storage/v1/b/oppa-ai-hub.appspot.com/o/ahram%2F1981%2F06%2F01_34504%2F011%2F011_87.jpg?generation=1688838054654463&alt=media', 'selfLink': 'https://www.googleapis.com/storage/v1/b/oppa-ai-hub.appspot.com/o/ahram%2F1981%2F06%2F01_34504%2F011%2F011_87.jpg'}, 'issue': '34504', 'provider': 'ahram', 'id': 'ahram_1981_06_01_34504_011_011_87', 'coordinates': {'polygon': [], 'boundingBox': [{'x': 6180, 'y': 5335}, {'x': 8470, 'y': 5335}, {'x': 8470, 'y': 8985}, {'x': 6180, 'y': 8985}]}, 'title': 'الشرقية: بنت القرية لأول مرة في دور شرطى المطافىء ..', 'content': 'بدأت محافظات مصر تنفيذ الخطة التي أعدتها وزارة الداخلية لتدريب جيل\nمن العاملين بالمحافظات على اطفاء الحرائق والتركيز على ربـات البيوت\nبهدف التقليل من حجم الخسائر في أي حريق يشب فجاة في أي منزل من\nالمنازل أثناء طهـو\nالطعام أو تشغيل\nالافران في القرى\nوتنفيذا لذلك عقد\nاللواء امين ميتكيس\nمحافظ الشرقيه\nاجتماعا شهده\nاللواء احمد حسـن\nمسـاعد وزير\nالداخلية والمقـدم\nرضا ابراهيم رئيس قسم الاطفاء والحريق بالمحافظة ، وتم الاتفاق على البـدء\nفورا في تنظيم دورات تدريبية لفتيات القرى وربات البيوت وموظفات المصـالح\nالحكومية بعد تقسيمهن الى مجموعات ، وتمتد فترة التدريب الى 6 أيام منهـا\n٤ ايام للتدريب النظري لدراسة أسباب الحرائق وانواعها واسـلوب الصيانة\nوالوقاية من اخطار الحرائق ، كمـا يتـم التـدريب العلمـى لمدة يومين على\nاستخدام اجهزة الاطفاء اليدوية لمقاومة الحرائق .\nوقد تم تنفيذ التجربة على مدى ٤٦ دورة اشترك فيها ۹۳٠ سيده وفتاة مـن\nسيدات وفتيات القرى والموظفات ، واعلن قائد المطافي نجاح هـذه التجـارب\nوقال ان بنت القرية أثبتت دورها لأول مرة ، وهي تقوم بدور شرطي المطاف\nبنت القرية .. في تدريب عملي على الأطفاء .', 'savedBy': 'sohamohamed246@gmail.com', 'authors': ['', 'عبد المجيد الشوادفى'], 'status': 'saved', 'ocr': 'الشرقية\nبنت القرية لأول مرة\nفي دور شرطى المطافىء\nبدأت محافظات مصر تنفيذ الخطة التي أعدتها وزارة الداخلية لتدريب جيل\nمن العاملين بالمحافظات على اطفاء الحرائق والتركيز على ربـات البيوت\nبهدف التقليل من حجم الخسائر في أي حريق يشب فجاة في أي منزل من\nالمنازل أثناء طهـو\nالطعام أو تشغيل\nالافران في القرى\nوتنفيذا لذلك عقد\nاللواء امين ميتكيس\nمحافظ الشرقيه\nاجتماعا شهده\nاللواء احمد حسـن\nمسـاعد وزير\n2\nبنت القرية .. في تدريب عملي على الأطفاء\nالداخلية والمقـدم\nرضا ابراهيم رئيس قسم الاطفاء والحريق بالمحافظة ، وتم الاتفاق على البـدء\nفورا في تنظيم دورات تدريبية لفتيات القرى وربات البيوت وموظفات المصـالح\nالحكومية بعد تقسيمهن الى مجموعات ، وتمتد فترة التدريب الى 6 أيام منهـا\n٤ ايام للتدريب النظري لدراسة أسباب الحرائق وانواعها واسـلوب الصيانة\nوالوقاية من اخطار الحرائق ، كمـا يتـم التـدريب العلمـى لمدة يومين على\nاستخدام اجهزة الاطفاء اليدوية لمقاومة الحرائق\nوقد تم تنفيذ التجربة على مدى ٤٦ دورة اشترك فيها ۹۳٠ سيده وفتاة مـن\nسيدات وفتيات القرى والموظفات ، واعلن قائد المطافي نجاح هـذه التجـارب\nوقال ان بنت القرية أثبتت دورها لأول مرة ، وهي تقوم بدور شرطي المطاف\nعبد المجيد الشوادف\n.\nI'}

    # return json

# Run the main window loop
select_input_directory()
