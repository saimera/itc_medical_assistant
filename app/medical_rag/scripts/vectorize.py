import os
import re

from dotenv import load_dotenv
from pinecone import Pinecone
from sqlalchemy import select

from app.medical_rag.db.models.chunks import Chunk
from app.medical_rag.db.models.documents import Document
from app.medical_rag.db.session import SessionLocal

load_dotenv()

INDEX_NAME = "medical-rag-chunks"
NAMESPACE = "itc-profile"
BATCH_SIZE = 100

api_key = os.getenv("PINECONE_API_KEY")
if not api_key:
    raise ValueError("PINECONE_API_KEY is missing from .env")

pinecone = Pinecone(api_key=api_key)
index = pinecone.index(INDEX_NAME)


def get_record_type(content: str) -> str:
    match = re.search(r"^\*\*Type:\*\*\s*(.+)$", content, re.MULTILINE)
    return match.group(1).strip() if match else "unknown"


# Copy pending document/chunk data out of the database session.
with SessionLocal() as session:
    documents = session.scalars(
        select(Document).where(
            Document.status == Document.Status.TO_BE_VECT,
            Document.content.is_not(None),
            Document.content != "",
        )
    ).all()

    work_items = []

    for document in documents:
        chunks = session.scalars(
            select(Chunk)
            .where(Chunk.document_id == document.id)
            .order_by(Chunk.chunk_index)
        ).all()

        pending_chunks = [
            {
                "id": chunk.id,
                "content": chunk.content,
                "chunk_index": chunk.chunk_index,
                "metadata": chunk.metadata_json or {},
            }
            for chunk in chunks
            if not chunk.embedded
        ]

        work_items.append((document.id, len(chunks), pending_chunks))


if not work_items:
    print("No documents are waiting to be vectorized.")

for document_id, total_chunks, pending_chunks in work_items:
    if total_chunks == 0:
        print(f"No chunks found for document: {document_id}")
        continue

    for start in range(0, len(pending_chunks), BATCH_SIZE):
        chunk_batch = pending_chunks[start : start + BATCH_SIZE]

        records = []
        for chunk in chunk_batch:
            record = dict(chunk["metadata"])
            record.update(
                {
                    "_id": str(chunk["id"]),
                    "chunk_text": chunk["content"],
                    "document_id": document_id,
                    "chunk_index": chunk["chunk_index"],
                    "record_type": get_record_type(chunk["content"]),
                }
            )
            records.append(record)

        response = index.documents.upsert(
            namespace=NAMESPACE,
            documents=records,
        )

        if response.upserted_count != len(records):
            raise RuntimeError(
                f"Pinecone accepted {response.upserted_count} of "
                f"{len(records)} chunks for {document_id}"
            )

        chunk_ids = [chunk["id"] for chunk in chunk_batch]

        # Mark chunks embedded only after their Pinecone upsert succeeds.
        with SessionLocal.begin() as session:
            saved_chunks = session.scalars(
                select(Chunk).where(Chunk.id.in_(chunk_ids))
            ).all()

            for chunk in saved_chunks:
                chunk.embedded = True

        print(f"Upserted {len(records)} chunks for document: {document_id}")

    # Mark the document ingested only when every chunk is embedded.
    with SessionLocal.begin() as session:
        document = session.get(Document, document_id)

        remaining_chunk_id = session.scalar(
            select(Chunk.id)
            .where(
                Chunk.document_id == document_id,
                Chunk.embedded.is_(False),
            )
            .limit(1)
        )

        if document and remaining_chunk_id is None:
            document.status = Document.Status.INGESTED
            print(f"Document marked ingested: {document_id}")