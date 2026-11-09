from datetime import datetime  # Timestamp type ke liye
from typing import Any  # Metadata ki flexible value types ke liye

from sqlalchemy import DateTime, String, Text, func  # Column types aur database time ke liye
from sqlalchemy.dialects.postgresql import JSONB  # PostgreSQL JSON metadata ke liye

from sqlalchemy.orm import Mapped, mapped_column  # SQLAlchemy model columns ke liye

from app.medical_rag.db.base import Base  # Shared model base import karo

class Document(Base):  # Documents table ka ORM model
     __tablename__ = "documents"  # Database table ka naam
     
     id: Mapped[str] = mapped_column(String(100), primary_key=True)  # Corpus ID, jaise faq-001
     record_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)  # FAQ, review, testimonial, ya profile section
     title: Mapped[str] = mapped_column(Text, nullable=False)  # Record ka title
     content: Mapped[str] = mapped_column(Text, nullable=False)  # Record ka full text
     source_url: Mapped[str] = mapped_column(Text, nullable=False)  # Original source URL
     metadata_json: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, nullable=False, default=dict)  # Extra fields, jaise rating ya section ID
     created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)  # Row create hone ka waqt

