from datetime import datetime  # Timestamp type ke liye
from typing import Any  # Metadata ki flexible value types ke liye

from sqlalchemy import DateTime, ForeignKey, Integer, Text, UniqueConstraint, func  # Column types aur constraints
from sqlalchemy.dialects.postgresql import JSONB  # PostgreSQL JSON metadata ke liye
from sqlalchemy.orm import Mapped, mapped_column  # ORM model columns ke liye

from app.medical_rag.db.base import Base  # Shared model base import karo


class Chunk(Base):  # Chunks table ka ORM model
    __tablename__ = "chunks"  # Database table ka naam

    __table_args__ = (  # Table-level constraints
        UniqueConstraint("document_id", "chunk_index", name="uq_chunks_document_index"),  # Ek document mein chunk order unique rakho
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)  # Har chunk ko auto-increment ID do
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)  # Parent document se link
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)  # Document ke andar chunk ka order
    content: Mapped[str] = mapped_column(Text, nullable=False)  # Chunk ka actual text
    metadata_json: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, nullable=False, default=dict)  # Chunk metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)  # Row create hone ka waqt

