import uuid

from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.db.base import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String, nullable=False)
    title = Column(String, nullable=True)
    status = Column(String, nullable=False, default="queued")  # queued, processing, completed, failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())