import re

from sqlalchemy import delete, select
from tokenizers import Tokenizer

from app.medical_rag.db.models.chunks import Chunk
from app.medical_rag.db.models.documents import Document
from app.medical_rag.db.session import SessionLocal

TOKENIZER = Tokenizer.from_pretrained("nvidia/llama-nemotron-embed-1b-v2")
CHUNK_SIZE = 300
CHUNK_OVERLAP = 50


def split_markdown(markdown: str) -> list[str]:
    records = re.split(r"(?m)^---\s*$", markdown)
    chunks = []

    for record in records:
        record = record.strip()
        if not record:
            continue

        parts = record.split("\n\n", 2)
        tokens = TOKENIZER.encode(record, add_special_tokens=False).ids

        if len(tokens) <= CHUNK_SIZE or len(parts) < 3:
            chunks.append(record)
            continue

        context = "\n\n".join(parts[:2])
        body = parts[2].strip()
        prefix = f"{context}\n\n"
        prefix_tokens = len(
            TOKENIZER.encode(prefix, add_special_tokens=False).ids
        )
        body_size = CHUNK_SIZE - prefix_tokens - 5
        step = body_size - CHUNK_OVERLAP

        if step <= 0:
            raise ValueError(f"Title/type too long for chunk size: {context}")

        body_tokens = TOKENIZER.encode(body, add_special_tokens=False).ids

        for start in range(0, len(body_tokens), step):
            piece_tokens = body_tokens[start : start + body_size]
            piece = TOKENIZER.decode(piece_tokens).strip()
            chunks.append(f"{prefix}{piece}".strip())

    return chunks


with SessionLocal.begin() as session:
    documents = session.scalars(
        select(Document).where(
            Document.status == Document.Status.TO_BE_CHUNKED,
            Document.content.is_not(None),
            Document.content != "",
        )
    ).all()

    for document in documents:
        markdown = document.content.strip()
        if not markdown:
            continue

        chunk_texts = split_markdown(markdown)
        if not chunk_texts:
            continue

        session.execute(
            delete(Chunk).where(Chunk.document_id == document.id)
        )

        session.add_all(
            Chunk(
                document_id=document.id,
                chunk_index=index,
                content=text,
                metadata_json={},
            )
            for index, text in enumerate(chunk_texts)
        )

        session.flush()
        document.status = Document.Status.TO_BE_VECT

        print(f"Saved {len(chunk_texts)} chunks for document: {document.id}")

    if not documents:
        print("No documents are waiting to be chunked.")