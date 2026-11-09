import os  # Environment variables read karne ke liye
import re  # Chunk text se record type nikalne ke liye

from dotenv import load_dotenv  # .env file load karne ke liye
from pinecone import Pinecone  # Pinecone SDK client
from sqlalchemy import select  # PostgreSQL se chunks query karne ke liye

from app.medical_rag.db.models.chunks import Chunk  # Chunks table ka model
from app.medical_rag.db.models.documents import Document  # Documents table ka model
from app.medical_rag.db.session import SessionLocal  # Database session factory

load_dotenv()  # .env se Pinecone API key load karo

INDEX_NAME = "medical-rag-chunks"  # Pinecone index ka naam
NAMESPACE = "itc-profile"  # Is document ke vectors ka namespace
DOCUMENT_ID = "placidway-itc-profile-5"  # PostgreSQL document ki ID

api_key = os.getenv("PINECONE_API_KEY")  # .env se Pinecone API key lo
if not api_key:  # API key missing ho to
    raise ValueError("PINECONE_API_KEY is missing from .env")  # Saaf error dikhao

pinecone = Pinecone(api_key=api_key)  # Pinecone account se connect karo
index = pinecone.index(INDEX_NAME)  # Existing Pinecone index select karo

with SessionLocal() as session:  # PostgreSQL session kholo
    document = session.get(Document, DOCUMENT_ID)  # Parent document load karo

    if document is None:  # Document na mile to
        raise ValueError(f"Document not found: {DOCUMENT_ID}")  # Saaf error dikhao

    statement = (  # Is document ke chunks ki query banao
        select(Chunk)  # Chunk rows select karo
        .where(Chunk.document_id == DOCUMENT_ID)  # Sirf isi document ke chunks lo
        .order_by(Chunk.chunk_index)  # Chunk order mein rakho
    )
    chunks = session.scalars(statement).all()  # Query chala kar chunks lo

    if not chunks:  # Chunks na milen to
        raise ValueError(f"No chunks found for: {DOCUMENT_ID}")  # Saaf error dikhao

    records = []  # Pinecone ko bhejne wale records rakho

    for chunk in chunks:  # Har database chunk par jao
        match = re.search(r"^\*\*Type:\*\*\s*(.+)$", chunk.content, re.MULTILINE)  # Record type dhoondo
        record_type = match.group(1).strip() if match else "unknown"  # Type na mile to default rakho

        metadata = chunk.metadata_json or {}  # Chunk ka metadata lo
        record = dict(metadata)  # Metadata se Pinecone record shuru karo
        record.update({  # Zaroori Pinecone fields add karo
            "_id": str(chunk.id),  # Chunk ID ko Pinecone vector ID banao
            "chunk_text": chunk.content,  # Integrated model ke liye text bhejo
            "document_id": str(chunk.document_id),  # Postgres document link rakho
            "chunk_index": chunk.chunk_index,  # Chunk ka order rakho
            "record_type": record_type,  # FAQ/review/etc. ka type rakho
        })
        records.append(record)  # Record batch mein add karo

response = index.documents.upsert(  # Records Pinecone mein upsert karo
    namespace=NAMESPACE,  # Namespace select karo
    documents=records,  # Chunk records bhejo
)

print(f"Upserted {response.upserted_count} chunks to Pinecone")  # Upload count dikhao