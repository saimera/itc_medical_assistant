import re  # Markdown records ko alag karne ke liye
from tokenizers import Tokenizer  # Text ke tokens count aur split karne ke liye
from sqlalchemy import delete  # Purane chunks delete karne ke liye

from app.medical_rag.db.models.chunks import Chunk  # Chunks table ka model
from app.medical_rag.db.models.documents import Document  # Documents table ka model
from app.medical_rag.db.session import SessionLocal  # Database session factory

TOKENIZER = Tokenizer.from_pretrained("nvidia/llama-nemotron-embed-1b-v2")  # Token counting ke liye tokenizer load karo
CHUNK_SIZE = 300  # Har chunk ka maximum target token size
CHUNK_OVERLAP = 50  # Lagatar chunks mein repeat hone wale tokens
DOCUMENT_ID = "placidway-itc-profile-5"  # Process karne wale document ki ID


def split_markdown(markdown: str) -> list[str]:  # Markdown ko token-based chunks mein baanto
    records = re.split(r"(?m)^---\s*$", markdown)  # Records ko --- par alag karo
    chunks = []  # Chunks jama karne ke liye list

    for record in records:  # Har Markdown record par jao
        record = record.strip()  # Record ke aage-peechhe whitespace hatao
        if not record:  # Agar record khali ho
            continue  # To usay skip karo

        parts = record.split("\n\n", 2)  # Title, type aur body alag karo
        tokens = TOKENIZER.encode(record, add_special_tokens=False).ids  # Record ke tokens banao

        if len(tokens) <= CHUNK_SIZE or len(parts) < 3:  # Chhota ya unexpected record ho
            chunks.append(record)  # To poora record ek chunk rakho
            continue  # Agle record par jao

        context = "\n\n".join(parts[:2])  # Title aur type ko har chunk ka context banao
        body = parts[2].strip()  # Record ka main text lo
        prefix = f"{context}\n\n"  # Context ke baad body ke liye jagah banao
        prefix_tokens = len(TOKENIZER.encode(prefix, add_special_tokens=False).ids)  # Context ke tokens count karo
        body_size = CHUNK_SIZE - prefix_tokens - 5  # Context aur boundary ke liye jagah chhor kar body limit nikalo
        step = body_size - CHUNK_OVERLAP  # 50-token overlap ke liye agle chunk ka start nikalo

        if step <= 0:  # Agar context overlap ke muqable mein bohat lamba ho
            raise ValueError(f"Title/type too long for chunk size: {context}")  # Saaf error dikhao

        body_tokens = TOKENIZER.encode(body, add_special_tokens=False).ids  # Body ke tokens banao

        for start in range(0, len(body_tokens), step):  # Overlap ke saath body par aage chalo
            piece_tokens = body_tokens[start : start + body_size]  # Is chunk ke body tokens lo
            piece = TOKENIZER.decode(piece_tokens).strip()  # Tokens ko text mein badlo
            chunks.append(f"{prefix}{piece}".strip())  # Context ke saath chunk list mein rakho

    return chunks  # Tamam chunks caller ko wapas do


with SessionLocal.begin() as session:  # Transaction shuru karo; success par commit hoga
    document = session.get(Document, DOCUMENT_ID)  # Database se document dhoondo

    if document is None:  # Agar document database mein nahi mila
        raise ValueError(f"Document not found: {DOCUMENT_ID}")  # Saaf error dikhao

    chunk_texts = split_markdown(document.content)  # Document content ko chunks mein baanto

    session.execute(delete(Chunk).where(Chunk.document_id == document.id))  # Sirf isi document ke purane chunks hatao

    session.add_all(  # Naye chunks database session mein add karo
        Chunk(  # Ek Chunk row banao
            document_id=document.id,  # Parent document se link karo
            chunk_index=index,  # Chunk ka order save karo
            content=text,  # Chunk ka text save karo
            metadata_json={},  # Filhaal khali metadata save karo
        )
        for index, text in enumerate(chunk_texts)  # Har chunk ko index do
    )

print(f"Saved {len(chunk_texts)} chunks for document: {DOCUMENT_ID}")  # Save result dikhao