## OCR helpers

A collection of python helper scripts used in a large scale OCR POC project.

### Scripts

1.  `coordinates.py`  
    Draw a bounding box or polygon on a selected image based on the annotation value in `{x: number, y: number}[]` format.
2.  `logger.py`  
    Pretty print colored logs
3.  `coco-cropper.py`  
    Crop images providing [COCO annotation format](https://opencv.github.io/cvat/docs/manual/advanced/formats/format-coco/) json file.
4.  `ocr.py`  
    Get OCR results from [Google Cloud Vision](https://cloud.google.com/vision) api

### Usage

1.  Install dependencies  
    `pip install -r requirements.txt`
2.  Run script  
    `py coco-cropper.py`

### Package build

`py -m PyInstaller --onefile --name CocoCropper--icon icon.ico coco-cropper.py`
