from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.chunk import Chunk
from app.services.embedding.factory import get_embedding_provider

from .base import RetrievedChunk


async def semantic_search(
    db: Session,
    query: str,
    top_k: int = 10,
    document_ids: Optional[List[str]] = None,
) -> List[RetrievedChunk]:
    """
    Vector-based semantic retrieval using pgvector.
    Assumes Chunk.embedding is a normalized 1024-d vector from E5.
    """

    # Embed query with E5 (use "query:" prefix for E5 family)
    provider = get_embedding_provider()
    query_embedding = (await provider.embed([f"query: {query}"]))[0]

    # Build base query
    q = db.query(Chunk)
    if document_ids:
        uuid_ids = [UUID(did) for did in document_ids]
        q = q.filter(Chunk.document_id.in_(uuid_ids))

    # Use cosine distance provided by pgvector for ranking
    # Lower distance = more similar, so order ascending
    q = q.order_by(Chunk.embedding.cosine_distance(query_embedding)).limit(top_k)

    rows: List[Chunk] = q.all()

    results: List[RetrievedChunk] = []
    for row in rows:
        # We don't get the raw distance value easily here without labeling it,
        # so we just set a placeholder score of 1.0; you can extend this to
        # include the actual distance if needed.
        results.append(
            RetrievedChunk(
                chunk_id=str(row.id),
                document_id=str(row.document_id),
                text=row.text,
                score=1.0,
                source="vector",
            )
        )

    return results

