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

    sources_by_url = {}
    for chunk in chunks:
        url = chunk["source_url"]
        sources_by_url[url] = {
            "title": chunk["source_title"],
            "url": url,
        }

    return {"answer": answer, "sources": list(sources_by_url.values())}