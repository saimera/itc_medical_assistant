from fastapi import APIRouter
from pydantic import BaseModel

from services.llm import generate_answer
from services.query_service import retrieve_chunks

router = APIRouter()

MIN_RELEVANCE_SCORE = 0.34


class ChatRequest(BaseModel):
    question: str


# Use the retrieval results as grounding context for the LLM response.
@router.post("/chat")
def chat(request: ChatRequest):
    chunks = retrieve_chunks(request.question)

    has_relevant_chunks = (
        bool(chunks)
        and chunks[0]["score"] >= MIN_RELEVANCE_SCORE
    )

    print(
        f"Query: {request.question} | "
        f"Top score: {chunks[0]['score'] if chunks else 'no results'} | "
        f"Relevant: {has_relevant_chunks}"
    )

    answer = generate_answer(request.question, chunks)

    sources_by_url = {}
    for chunk in chunks:
        url = chunk["source_url"]
        sources_by_url[url] = {
            "title": chunk["source_title"],
            "url": url,
        }

    return {
        "answer": answer,
        "sources": list(sources_by_url.values()),
    }