# ingestion/vector_indexer.py

from typing import List
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.chunk import Chunk
from app.services.embedding.factory import get_embedding_provider
from app.services.ingestion.chunker import ChunkWithMetadata


async def index_chunks_to_vector_db(
    db: Session,
    document_id: UUID,
    chunks: List[ChunkWithMetadata],
) -> int:
    """
    Embeds chunks using E5 (intfloat/e5-large-v2) and stores them in Postgres (pgvector).
    Stores page_number, token_count, and other metadata for each chunk.
    Returns number of inserted chunks.
    """

    if not chunks:
        return 0

    # Prefix for E5 model (recommended for passage embeddings)
    prefixed_chunks = [f"passage: {chunk.text}" for chunk in chunks]

    # Get embedding provider (E5EmbeddingProvider)
    embedding_provider = get_embedding_provider()

    # Embed in batch
    embeddings = await embedding_provider.embed(prefixed_chunks)

    if len(embeddings) != len(chunks):
        raise ValueError("Embedding count does not match chunk count")

    # Insert into DB (one row per chunk) with all metadata
    for idx, (chunk_meta, embedding) in enumerate(zip(chunks, embeddings)):
        # Prepare other_metadata JSONB field
        other_metadata = {
            "start_char": chunk_meta.start_char,
            "end_char": chunk_meta.end_char,
        }

        db_chunk = Chunk(
            document_id=document_id,
            chunk_index=idx,
            page_number=chunk_meta.page_number,
            text=chunk_meta.text,
            token_count=chunk_meta.token_count,
            embedding=embedding,
            other_metadata=other_metadata,
        )
        db.add(db_chunk)

    db.commit()

    return len(chunks)