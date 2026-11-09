from fastapi import APIRouter  # Chat API route banane ke liye
from pydantic import BaseModel  # Request body validate karne ke liye

from services.llm import generate_answer  # Retrieved context se jawab banane ke liye
from services.query_service import retrieve_chunks  # Relevant chunks dhoondhne ke liye

router = APIRouter()  # Chat routes ka router banao


class ChatRequest(BaseModel):  # Chat request ka format
    question: str  # User ka sawal


@router.post("/chat")  # POST /chat endpoint
def chat(request: ChatRequest):  # User ka request handle karo
    chunks = retrieve_chunks(request.question)  # Sawal ke relevant chunks retrieve karo
    answer = generate_answer(request.question, chunks)  # Chunks se LLM jawab banaye
    sources = list(dict.fromkeys(  # Duplicate URLs hatao aur order barqarar rakho
        chunk["source_url"] for chunk in chunks  # Retrieved chunks ke source URLs lo
    ))
    return {"answer": answer, "sources": sources}  # Jawab aur sources frontend ko do

    