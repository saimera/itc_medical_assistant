import os
import re

from dotenv import load_dotenv
from pinecone import Pinecone
from sqlalchemy import select

from app.medical_rag.db.models.chunks import Chunk
from app.medical_rag.db.models.documents import Document
from app.medical_rag.db.session import SessionLocal

# Load environment settings such as the Pinecone API key before connecting.
load_dotenv()

INDEX_NAME = "medical-rag-chunks"
NAMESPACE = "itc-profile"
DOCUMENT_ID = "placidway-itc-profile-5"

api_key = os.getenv("PINECONE_API_KEY")
if not api_key:
    raise ValueError("PINECONE_API_KEY is missing from .env")

# Connect to the target Pinecone index and preload the document's chunk records.
pinecone = Pinecone(api_key=api_key)
index = pinecone.index(INDEX_NAME)

with SessionLocal() as session:
    document = session.get(Document, DOCUMENT_ID)

    if document is None:
        raise ValueError(f"Document not found: {DOCUMENT_ID}")

    statement = (
        select(Chunk)
        .where(Chunk.document_id == DOCUMENT_ID)
        .order_by(Chunk.chunk_index)
    )
    chunks = session.scalars(statement).all()

    if not chunks:
        raise ValueError(f"No chunks found for: {DOCUMENT_ID}")

    records = []

    for chunk in chunks:
        match = re.search(r"^\*\*Type:\*\*\s*(.+)$", chunk.content, re.MULTILINE)
        record_type = match.group(1).strip() if match else "unknown"

        metadata = chunk.metadata_json or {}
        record = dict(metadata)
        record.update({
            "_id": str(chunk.id),
            "chunk_text": chunk.content,
            "document_id": str(chunk.document_id),
            "chunk_index": chunk.chunk_index,
            "record_type": record_type,
        })
        records.append(record)

# Upsert the prepared records so search can index the latest chunk set.
response = index.documents.upsert(
    namespace=NAMESPACE,
    documents=records,
)

print(f"Upserted {response.upserted_count} chunks to Pinecone")