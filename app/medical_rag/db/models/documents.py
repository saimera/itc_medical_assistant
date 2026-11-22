from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.medical_rag.db.base import Base


class Document(Base):

    __tablename__ = "documents"

    class Status(StrEnum):
        PENDING_MARKDOWN = "pending_markdown"
        TO_BE_CHUNKED = "to_be_chunked"
        TO_BE_VECT = "to_be_vectorize"
        INGESTED = "ingested"


    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    record_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, nullable=False, default=dict)
    status: Mapped[Status | None] = mapped_column(String(30), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

