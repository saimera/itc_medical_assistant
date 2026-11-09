from pathlib import Path  # File paths handle karne ke liye

from sqlalchemy import delete  # Purane page records delete karne ke liye

from app.medical_rag.db.models.documents import Document  # Documents table ka model
from app.medical_rag.db.session import SessionLocal  # Database session factory

SOURCE_URL = "https://www.placidway.com/profile/5/Alternative-Cancer-Treatment-by-ITC-Immunity-Therapy-Center"  # Page URL
TEXT_PATH = Path("data/processed/itc-profile.md")  # Cleaned page text ka path
DOCUMENT_ID = "placidway-itc-profile-5"  # Is webpage ka stable ID

content = TEXT_PATH.read_text(encoding="utf-8").strip()  # Page ka cleaned text load karo
title = next((line.lstrip("# ").strip() for line in content.splitlines() if line.strip()), "Untitled page")
with SessionLocal.begin() as session:  # Transaction kholo; success par commit hoga
    session.execute(delete(Document).where(Document.source_url == SOURCE_URL))  # Isi URL ke purane rows hatao
    session.add(Document(  # Webpage ka ek row banao
        id=DOCUMENT_ID,  # Stable page ID
        record_type="web_page",  # Record ko webpage mark karo
        title=title,  # Page title save karo
        content=content,  # Full cleaned page text save karo
        source_url=SOURCE_URL,  # Source URL save karo
        metadata_json={"source_type": "medical_center_profile"},  # Page-level metadata
    ))

print(f"Saved one webpage document: {DOCUMENT_ID}")  # Result dikhao

