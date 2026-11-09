from fastapi import FastAPI  # FastAPI application banane ke liy
from pathlib import Path  # File path handle karne ke liye

from fastapi.responses import FileResponse  # Static files serve karne ke liye
from fastapi.staticfiles import StaticFiles

from app.medical_rag.routes.chat_router import router as chat_router  # Chat router import karo


app = FastAPI(title="Medical RAG API")  # API application create karo
app.mount(
    "/static",
    StaticFiles(directory=Path(__file__).resolve().parents[3] / "static"),
    name="static",
)
app.include_router(chat_router)  # Chat routes app ke saath register karo


@app.get("/",include_in_schema=False)  # Root route define karo
def home():
    return FileResponse("templates/medical_rag.html")

@app.get("/health")  # Health-check route define karo
def health_check():  # Health-check request handle karo
    return {"status": "ok"}  # App ka status return karo