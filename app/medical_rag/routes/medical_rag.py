
from fastapi import FastAPI

from app.medical_rag.routes.chat_router import router as chat_router

app = FastAPI(title="Medical RAG API")
app.include_router(chat_router)

@app.get("/health")
def health_check():
    return {"status": "ok"}