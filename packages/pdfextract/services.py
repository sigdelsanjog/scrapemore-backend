from PyPDF2 import PdfReader
from pathlib import Path
from PIL import Image
import io

'''
TODO: 
    1. Preprocess the extracted text
    1.a create a json file for the extracted text where key will be the paper title and value will be the content inside that paper
    2. Or instead create a general template to map the key value pair within the extracted paper. Example below in 2.1
    2.1 {Authors: [Author1, Author2, Author3], 
        Abstract: "Abstract content",
        Introduction: "Introduction content",
        RElated Work: "Related work content",
        Methodology: "Methodology content",
        Results: "Results content",
        Conclusion: "Conclusion content",
        References: [Reference1, Reference2, Reference3]}

    Extract images from the PDF file and save them to the "extracted_images" directory.
    2. Append the file paths of the extracted images to the "images" list in the "result" dictionary.
    3. Or store the downloaded images in a database and return the image URLs in the "images" list.
    -- The images inside a research paper is not that important inLLMS yet. So we can actually skip this portaion at the moment.
'''

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
