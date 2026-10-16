from pydantic import BaseModel

class UploadResponse(BaseModel):
    filename: str
    status: str
    characters_extracted: int
    chunks_stored: int
