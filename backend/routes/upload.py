from fastapi import APIRouter, UploadFile, File
from services.pdf_service import save_pdf, extract_text, validate_file
from services.chunking_service import chunk_text
from services.vector_service import create_collection, add_chunks, list_sources
from models.schemas import UploadResponse
import logging
import os

router = APIRouter()

logger = logging.getLogger("uvicorn")

create_collection()

@router.post("/upload", response_model=UploadResponse)
def upload_pdf(file: UploadFile = File(...)):
    contents = file.file.read()
    filename = os.path.basename(file.filename)

    validate_file(filename, contents)

    file_path = save_pdf(filename, contents)
    full_text = extract_text(file_path)

    chunks = chunk_text(full_text)
    add_chunks(chunks, {"source": filename})

    logger.info(f"Extracted {len(full_text)} characters, stored {len(chunks)} chunks from {filename}")

    return UploadResponse(
        filename=filename,
        status="saved",
        characters_extracted=len(full_text),
        chunks_stored=len(chunks)
    )


@router.get("/documents")
def get_documents():
    return {"documents": list_sources()}
