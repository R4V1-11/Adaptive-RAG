from fastapi import APIRouter
from pydantic import BaseModel
from services.answer_service import answer_question


router = APIRouter()

class AskRequest(BaseModel):
    query: str
    source: str | None = None

@router.post("/ask")
def ask_question(request: AskRequest):
    result = answer_question(request.query, source=request.source)
    return result