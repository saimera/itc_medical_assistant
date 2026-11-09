import os  # Environment variables se API key lene ke liye
from pinecone import EmbedQuery, Pinecone  # Pinecone search aur query embedding ke liye
from sqlalchemy import select  # PostgreSQL query banane ke liye

from app.medical_rag.db.models.chunks import Chunk  # Chunks table ka model
from app.medical_rag.db.models.documents import Document  # Documents table ka model
from app.medical_rag.db.session import SessionLocal  # Database session factory

from dotenv import load_dotenv  # .env file load karne ke liye


load_dotenv()  # .env ki values environment mein load karo

INDEX_NAME = "medical-rag-chunks"  # Pinecone index ka naam
NAMESPACE = "itc-profile"  # Is project ke vectors ka namespace

pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])  # Pinecone client banao
index = pc.index(INDEX_NAME)  # Pinecone index se connect karo


def retrieve_chunks(query: str, top_k: int = 5) -> list[dict]:  # Relevant chunks dhoondo
    response = index.documents.search(  # Pinecone mein semantic search karo
        namespace=NAMESPACE,  # Apne vectors ka namespace select karo
        top_k=top_k,  # Wapas aane wale results ki maximum tadaad
        score_by=[EmbedQuery(field="chunk_text", query=query)],  # Query ko Pinecone se embed karwao
        include_fields=["document_id", "chunk_index", "record_type"],  # Result metadata mango
    )

    ranked_ids = [(int(match.id), match.score) for match in response.matches]  # Pinecone IDs aur scores lo
    chunk_ids = [chunk_id for chunk_id, _ in ranked_ids]  # PostgreSQL ke liye chunk IDs nikalo

    if not chunk_ids:  # Agar Pinecone ko relevant chunk na mile
        return []  # Khali result wapas do

    with SessionLocal() as session:  # PostgreSQL session kholo
        rows = session.execute(  # Chunks aur unke source URLs fetch karo
            select(Chunk, Document.source_url)  # Chunk row aur document ka URL select karo
            .join(Document, Chunk.document_id == Document.id)  # Chunk ko parent document se joro
            .where(Chunk.id.in_(chunk_ids))  # Sirf Pinecone se mile IDs lao
        ).all()  # Query ke tamam results lo

    chunks_by_id = {chunk.id: (chunk, source_url) for chunk, source_url in rows}  # Results ko ID se map karo

    return [  # Results ko Pinecone ke relevance order mein wapas do
        {  # Ek retrieved chunk ka record banao
            "chunk_id": chunk_id,  # Chunk ki database ID
            "content": chunks_by_id[chunk_id][0].content,  # PostgreSQL se chunk ka text
            "score": score,  # Pinecone ka similarity score
            "metadata": chunks_by_id[chunk_id][0].metadata_json,  # PostgreSQL se chunk metadata
            "source_url": chunks_by_id[chunk_id][1],  # Parent document ka source URL
        }
        for chunk_id, score in ranked_ids  # Pinecone ranking ke order mein har result lo
        if chunk_id in chunks_by_id  # PostgreSQL mein milne wale chunks hi rakho
    ]


if __name__ == "__main__":  # Direct run par hi test query chalao
    results = retrieve_chunks("What treatments does ITC offer?")  # Pinecone se top 5 relevant chunks lo
    for result in results:  # Har retrieved chunk par jao
        print(f"Score: {result['score']}")  # Relevance score dikhao
        print(f"Chunk ID: {result['chunk_id']}")  # Chunk ID dikhao
        print(result["content"])  # Chunk ka text dikhao
        print(f"Source: {result['source_url']}\n")  # Source URL dikhao

        