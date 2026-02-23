# ingestion/vector_indexer.py

from typing import List
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.chunk import Chunk
from app.services.embedding.factory import get_embedding_provider

async def index_chunks_to_vector_db(
    db: Session,
    document_id: UUID,
    chunks: List[str],
) -> int:
    """
    Embeds chunks using E5 and stores them in Postgres (pgvector).
    Returns number of inserted chunks.
    """

    if not chunks:
        return 0

    # Prefix for E5 model
    prefixed_chunks = [f"passage: {chunk}" for chunk in chunks]

    # Get embedding provider
    embedding_provider = get_embedding_provider()

    # Embed in batch
    embeddings = await embedding_provider.embed(prefixed_chunks)

    if len(embeddings) != len(chunks):
        raise ValueError("Embedding count does not match chunk count")

    # Insert into DB
    for idx, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
        db_chunk = Chunk(
            document_id=document_id,
            chunk_index=idx,
            text=chunk_text,
            embedding=embedding,
        )
        db.add(db_chunk)

    db.commit()

    return len(chunks)