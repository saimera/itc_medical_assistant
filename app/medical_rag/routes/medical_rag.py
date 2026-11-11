from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.medical_rag.routes.chat_router import router as chat_router


app = FastAPI(title="Medical RAG API")
app.mount(
    "/static",
    StaticFiles(directory=Path(__file__).resolve().parents[3] / "static"),
    name="static",
)
app.include_router(chat_router)


# Serve the main UI page and a lightweight health check for deployment checks.
@app.get("/", include_in_schema=False)
def home():
    return FileResponse("templates/medical_rag.html")


@app.get("/health")
def health_check():
    return {"status": "ok"}