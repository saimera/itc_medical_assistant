import os

from dotenv import load_dotenv
from pinecone import EmbedQuery, Pinecone
from sqlalchemy import select

from app.medical_rag.db.models.chunks import Chunk
from app.medical_rag.db.models.documents import Document
from app.medical_rag.db.session import SessionLocal

load_dotenv()

INDEX_NAME = "medical-rag-chunks"
NAMESPACE = "itc-profile"

pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
index = pc.index(INDEX_NAME)


def retrieve_chunks(query: str, top_k: int = 5) -> list[dict]:
    response = index.documents.search(
        namespace=NAMESPACE,
        top_k=top_k,
        score_by=[EmbedQuery(field="chunk_text", query=query)],
        include_fields=["document_id", "chunk_index", "record_type"],
    )

    ranked_ids = [(int(match.id), match.score) for match in response.matches]
    chunk_ids = [chunk_id for chunk_id, _ in ranked_ids]

    if not chunk_ids:
        return []

    with SessionLocal() as session:
        rows = session.execute(
            select(Chunk, Document.source_url)
            .join(Document, Chunk.document_id == Document.id)
            .where(Chunk.id.in_(chunk_ids))
        ).all()

    chunks_by_id = {chunk.id: (chunk, source_url) for chunk, source_url in rows}

    return [
        {
            "chunk_id": chunk_id,
            "content": chunks_by_id[chunk_id][0].content,
            "score": score,
            "metadata": chunks_by_id[chunk_id][0].metadata_json,
            "source_url": chunks_by_id[chunk_id][1],
        }
        for chunk_id, score in ranked_ids
        if chunk_id in chunks_by_id
    ]


if __name__ == "__main__":
    results = retrieve_chunks("What treatments does ITC offer?")
    for result in results:
        print(f"Score: {result['score']}")
        print(f"Chunk ID: {result['chunk_id']}")
        print(result["content"])
        print(f"Source: {result['source_url']}\n")
        