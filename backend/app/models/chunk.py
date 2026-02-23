import uuid
from sqlalchemy import Column, Text, Integer, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

from app.db.base import Base

class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False
    )

    chunk_index = Column(Integer, nullable=False)
    page_number = Column(Integer, nullable=True)

    text = Column(Text, nullable=False)
    token_count = Column(Integer, nullable=True)

    other_metadata = Column(JSONB, nullable=True)

    embedding = Column(Vector(1024))  # match your embedding model dimension

    created_at = Column(DateTime(timezone=True), server_default=func.now())