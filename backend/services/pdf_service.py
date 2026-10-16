import os
from pypdf import PdfReader
from fastapi import HTTPException
from config import UPLOAD_DIR, MAX_FILE_SIZE_MB, ALLOWED_EXTENSIONS

def validate_file(filename: str, contents: bytes):
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Only {ALLOWED_EXTENSIONS} files are allowed.")

    size_mb = len(contents) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(status_code=400, detail=f"File size exceeds the maximum limit of {MAX_FILE_SIZE_MB} MB.")

def save_pdf(filename: str, contents: bytes) -> str:
    file_path = os.path.join(UPLOAD_DIR, filename)
    with open(file_path, "wb") as f:
        f.write(contents)
    return file_path

def extract_text(file_path: str) -> str:
    try:
        reader = PdfReader(file_path)
        full_text = ""
        for page in reader.pages:
            full_text += page.extract_text() + '\n'
        return full_text
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Could not read PDF file: {str(e)}")