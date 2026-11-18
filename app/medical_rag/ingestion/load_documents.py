from pathlib import Path

from sqlalchemy import delete

from app.medical_rag.db.models.documents import Document
from app.medical_rag.db.session import SessionLocal

SOURCE_URL = "https://www.placidway.com/package/7901/Alternative-Anal-Cancer-Treatment-Package-in-Tijuana-Mexico-by-ITC"
TEXT_PATH = Path("data/markdown/itc-anal-package.md")
DOCUMENT_ID = "placidway-itc-package-7901"

content = TEXT_PATH.read_text(encoding="utf-8").strip()
title = next((line.lstrip("# ").strip() for line in content.splitlines() if line.strip()), "Untitled page")

# Replace the document row for this source URL so the database reflects the latest scrape.
with SessionLocal.begin() as session:
    session.execute(delete(Document).where(Document.source_url == SOURCE_URL))
    session.add(
        Document(
            id=DOCUMENT_ID,
            record_type="web_page",
            title=title,
            content=content,
            source_url=SOURCE_URL,
            metadata_json={"source_type": "medical_center_package"},
            status=Document.Status.TO_BE_CHUNKED
        )
    )

print(f"Saved one webpage document: {DOCUMENT_ID}")
