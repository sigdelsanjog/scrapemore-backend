from PyPDF2 import PdfReader
from pathlib import Path
from PIL import Image
import io

def extract_text_and_images(pdf_path: str):
    result = {"text": "", "images": []}
    reader = PdfReader(pdf_path)
    
    # Extract text
    for page in reader.pages:
        result["text"] += page.extract_text() or ""
    
    # Extract images
    for page in reader.pages:
        if hasattr(page, 'images'):
            for image_file in page.images:
                img_data = io.BytesIO(image_file.data)
                img = Image.open(img_data)
                img_path = Path("extracted_images") / image_file.name
                img.save(img_path)
                result["images"].append(str(img_path))
    
    return result
