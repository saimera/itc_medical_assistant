import os

from app.medical_rag.core.embedding import embed_text
from dotenv import load_dotenv
from pinecone import Pinecone
from sqlalchemy import select

from app.medical_rag.db.models.chunks import Chunk
from app.medical_rag.db.models.documents import Document
from app.medical_rag.db.session import SessionLocal

load_dotenv()

INDEX_NAME = "medical-rag-jina-v5"
NAMESPACE = "itc-profile"
BATCH_SIZE = 100

api_key = os.getenv("PINECONE_API_KEY")
if not api_key:
    raise ValueError("PINECONE_API_KEY is missing from .env")

index = Pinecone(api_key=api_key).index(INDEX_NAME)

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
    embeddings = embed_text([item["content"] for item in batch])

    vectors = [
        {
            "id": str(item["id"]),
            "values": embedding,
            "metadata": {
                **item["metadata"],
                "document_id": item["document_id"],
                "chunk_index": item["chunk_index"],
            },
        }
        for item, embedding in zip(batch, embeddings)
    ]

    result = index.upsert(vectors=vectors, namespace=NAMESPACE)

    if result.upserted_count != len(vectors):
        raise RuntimeError("Pinecone did not accept every vector in the batch")

    chunk_ids = [item["id"] for item in batch]

    with SessionLocal.begin() as session:
        saved_chunks = session.scalars(
            select(Chunk).where(Chunk.id.in_(chunk_ids))
        ).all()

        for chunk in saved_chunks:
            chunk.embedded = True

    print(f"Stored {len(vectors)} vectors in Pinecone.")

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