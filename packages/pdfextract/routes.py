from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
import shutil
from config.file_utils import create_temp_folder  # Import your function to create the directory
from .services import extract_text_and_images

router = APIRouter()

@router.post("/extract")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")
    
    # Create the temporary folder if it doesn't exist
    temp_dir = create_temp_folder('temp')  # You can change the folder name if needed

    # Define the full path to store the uploaded file
    temp_file_path = Path(temp_dir) / file.filename

    # Save the file to the temp directory
    with open(temp_file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        # Process the PDF file (assuming you have a function to extract text and images)
        result = extract_text_and_images(str(temp_file_path))
        return result
    finally:
        # Clean up: Delete the uploaded file after processing
        if temp_file_path.exists():
            temp_file_path.unlink(missing_ok=True)
