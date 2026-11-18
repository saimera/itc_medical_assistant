import os
import re

from pinecone import Pinecone

INDEX_NAME = "medical-rag-chunks"
NAMESPACE = "itc-profile"


def get_record_type(content: str) -> str:
    match = re.search(r"^\*\*Type:\*\*\s*(.+)$", content, re.MULTILINE)
    return match.group(1).strip() if match else "unknown"


def embed_text(chunks: list[dict]) -> int:
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        raise ValueError("PINECONE_API_KEY is missing from .env")

    if not chunks:
        return 0

    index = Pinecone(api_key=api_key).index(INDEX_NAME)

    records = []
    for chunk in chunks:
        record = dict(chunk.get("metadata") or {})
        record.update({
            "_id": str(chunk["id"]),
            "chunk_text": chunk["content"],
            "document_id": chunk["document_id"],
            "chunk_index": chunk["chunk_index"],
            "record_type": get_record_type(chunk["content"]),
        })
        records.append(record)

    response = index.documents.upsert(
        namespace=NAMESPACE,
        documents=records,
    )

    return response.upserted_count