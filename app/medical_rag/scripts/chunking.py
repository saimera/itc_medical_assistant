from sqlalchemy import delete, select

from app.medical_rag.core.chunk import split_markdown
from app.medical_rag.db.models.chunks import Chunk
from app.medical_rag.db.models.documents import Document
from app.medical_rag.db.session import SessionLocal

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
                embedded=False,
            )
            for index, text in enumerate(chunk_texts)
        )

        session.flush()
        document.status = Document.Status.TO_BE_VECT

        print(f"Saved {len(chunk_texts)} chunks for document: {document.id}")

    if not documents:
        print("No documents are waiting to be chunked.")