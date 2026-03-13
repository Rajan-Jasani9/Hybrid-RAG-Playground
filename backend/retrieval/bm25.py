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
    """

    es: Elasticsearch = get_es_client()

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

    resp = es.search(index=INDEX_NAME, body=body)
    hits = resp.get("hits", {}).get("hits", [])

    results: List[RetrievedChunk] = []
    for hit in hits:
        src = hit.get("_source", {})
        score = float(hit.get("_score", 0.0))
        results.append(
            RetrievedChunk(
                chunk_id=str(src.get("chunk_id")),
                document_id=str(src.get("document_id")),
                text=str(src.get("text", "")),
                score=score,
                source="bm25",
            )
        )

    return results

