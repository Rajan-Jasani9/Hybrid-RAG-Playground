from typing import List, Optional, Dict

from sqlalchemy.orm import Session

from fusion.rrf import reciprocal_rank_fusion

from .base import RetrievedChunk
from .vector import semantic_search
from .bm25 import keyword_search


async def hybrid_search(
    db: Session,
    query: str,
    top_k: int = 10,
    document_ids: Optional[List[str]] = None,
) -> List[RetrievedChunk]:
    """
    Hybrid retrieval that fuses semantic (pgvector) and keyword (BM25) results
    using Reciprocal Rank Fusion.
    Falls back to vector-only search if BM25/Elasticsearch is unavailable.
    """
    import logging
    logger = logging.getLogger(__name__)

    vector_results = await semantic_search(
        db=db,
        query=query,
        top_k=top_k,
        document_ids=document_ids,
    )

    bm25_results = keyword_search(
        query=query,
        top_k=top_k,
        document_ids=document_ids,
    )

    # If no results from either source, return empty
    if not vector_results and not bm25_results:
        return []

    # If only one source has results, return those (with appropriate source label)
    if not bm25_results:
        logger.info("BM25 unavailable, returning vector-only results")
        return vector_results[:top_k]
    
    if not vector_results:
        logger.info("Vector search returned no results, returning BM25-only results")
        return bm25_results[:top_k]

    # Both sources have results - fuse them
    # Build rankings for RRF based on rank order only
    vec_ranking = [(r.chunk_id, r.score) for r in vector_results]
    bm25_ranking = [(r.chunk_id, r.score) for r in bm25_results]

    fused = reciprocal_rank_fusion([vec_ranking, bm25_ranking])

    # Index by chunk_id to look up full chunk info; prefer vector fields then bm25
    by_id: Dict[str, RetrievedChunk] = {
        r.chunk_id: r for r in vector_results
    }
    for r in bm25_results:
        by_id.setdefault(r.chunk_id, r)

    output: List[RetrievedChunk] = []
    for chunk_id, fused_score in fused[:top_k]:
        base = by_id.get(chunk_id)
        if base is None:
            continue
        output.append(
            RetrievedChunk(
                chunk_id=base.chunk_id,
                document_id=base.document_id,
                text=base.text,
                score=fused_score,
                source="hybrid",
            )
        )

    return output

