from dotenv import load_dotenv
from sqlalchemy import select

from app.medical_rag.core.embed import embed_text
from app.medical_rag.db.models.chunks import Chunk
from app.medical_rag.db.models.documents import Document
from app.medical_rag.db.session import SessionLocal

load_dotenv()

BATCH_SIZE = 100

with SessionLocal() as session:
    pending_chunks = session.scalars(
        select(Chunk)
        .where(Chunk.embedded.is_(False))
        .order_by(Chunk.document_id, Chunk.chunk_index)
    ).all()

    work_items = [
        {
            "id": chunk.id,
            "document_id": chunk.document_id,
            "chunk_index": chunk.chunk_index,
            "content": chunk.content,
            "metadata": chunk.metadata_json or {},
        }
        for chunk in pending_chunks
    ]

if not work_items:
    print("No chunks are waiting to be vectorized.")

for start in range(0, len(work_items), BATCH_SIZE):
    batch = work_items[start : start + BATCH_SIZE]

    # Pinecone creates embeddings and stores these records through its integrated model.
    upserted_count = embed_text(batch)

    if upserted_count != len(batch):
        raise RuntimeError(
            f"Pinecone accepted {upserted_count} of {len(batch)} chunks"
        )

    chunk_ids = [item["id"] for item in batch]

    with SessionLocal.begin() as session:
        saved_chunks = session.scalars(
            select(Chunk).where(Chunk.id.in_(chunk_ids))
        ).all()

        for chunk in saved_chunks:
            chunk.embedded = True

    print(f"Stored {upserted_count} chunks in Pinecone.")

document_ids = {item["document_id"] for item in work_items}

for document_id in document_ids:
    with SessionLocal.begin() as session:
        document = session.get(Document, document_id)

        pending_id = session.scalar(
            select(Chunk.id)
            .where(
                Chunk.document_id == document_id,
                Chunk.embedded.is_(False),
            )
            .limit(1)
        )

        if document and pending_id is None:
            document.status = Document.Status.INGESTED
            print(f"Document marked ingested: {document_id}")