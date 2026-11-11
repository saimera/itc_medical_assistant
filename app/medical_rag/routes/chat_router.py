from fastapi import APIRouter
from pydantic import BaseModel

from services.llm import generate_answer
from services.query_service import retrieve_chunks

router = APIRouter()


class ChatRequest(BaseModel):
    question: str


# Use the retrieval results as grounding context for the LLM response.
@router.post("/chat")
def chat(request: ChatRequest):
    chunks = retrieve_chunks(request.question)
    answer = generate_answer(request.question, chunks)
    sources = list(dict.fromkeys(chunk["source_url"] for chunk in chunks))
    return {"answer": answer, "sources": sources}
    