from typing import List, Optional
from uuid import UUID

from elasticsearch import Elasticsearch

from app.services.ingestion.elastic_indexer import get_es_client, INDEX_NAME

from .base import RetrievedChunk


def keyword_search(
    query: str,
    top_k: int = 10,
    document_ids: Optional[List[str]] = None,
) -> List[RetrievedChunk]:
    """
    Keyword / BM25 retrieval via Elasticsearch.
    Returns empty list if Elasticsearch is not available.
    """
    import logging
    logger = logging.getLogger(__name__)

    try:
        es: Elasticsearch = get_es_client()
    except Exception as e:
        logger.warning(f"Elasticsearch not available, skipping BM25 search: {str(e)}")
        return []

    try:
        # Check if index exists before searching
        if not es.options(request_timeout=10).indices.exists(index=INDEX_NAME):
            logger.info(f"Elasticsearch index '{INDEX_NAME}' does not exist yet. No documents have been indexed.")
            return []
        
        must_clauses = [
            {
                "match": {
                    "text": query,
                }
            }
        ]

        if document_ids:
            must_clauses.append(
                {
                    "terms": {
                        "document_id": [str(UUID(did)) for did in document_ids],
                    }
                }
            )

        body = {
            "query": {
                "bool": {
                    "must": must_clauses,
                }
            },
            "size": top_k,
        }

        # Use options() for ES 8.x compatibility
        try:
            resp = es.options(request_timeout=30).search(index=INDEX_NAME, body=body)
        except TypeError:
            # Fallback: ES 8+ might use query parameter instead of body
            resp = es.options(request_timeout=30).search(index=INDEX_NAME, query=body["query"], size=top_k)
        hits = resp.get("hits", {}).get("hits", [])

        results: List[RetrievedChunk] = []
        for hit in hits:
            src = hit.get("_source", {})
            score = float(hit.get("_score", 0.0))
            metadata = src.get("metadata", {})
            results.append(
                RetrievedChunk(
                    chunk_id=str(src.get("chunk_id")),
                    document_id=str(src.get("document_id")),
                    text=str(src.get("text", "")),
                    score=score,
                    source="bm25",
                    page_number=src.get("page_number"),
                    token_count=src.get("token_count"),
                    chunk_index=src.get("chunk_index"),
                )
            )

        return results
    except Exception as e:
        # Handle NotFoundError (index doesn't exist) gracefully
        error_type = type(e).__name__
        if "NotFoundError" in error_type or "index_not_found" in str(e).lower():
            logger.info(f"Elasticsearch index '{INDEX_NAME}' does not exist yet. No documents have been indexed.")
            return []
        logger.warning(f"Error during BM25 search, returning empty results: {str(e)}")
        return []

