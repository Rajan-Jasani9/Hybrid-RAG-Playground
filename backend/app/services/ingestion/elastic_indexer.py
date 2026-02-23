# ingestion/elastic_indexer.py

from typing import List
from uuid import UUID

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk


INDEX_NAME = "documents_chunks"


def get_es_client() -> Elasticsearch:
    return Elasticsearch("http://localhost:9200")


def ensure_index_exists(es: Elasticsearch):
    if es.indices.exists(index=INDEX_NAME):
        return

    mapping = {
        "mappings": {
            "properties": {
                "chunk_id": {"type": "keyword"},
                "document_id": {"type": "keyword"},
                "chunk_index": {"type": "integer"},
                "text": {
                    "type": "text",
                    "analyzer": "standard"
                },
                "metadata": {"type": "object"},
            }
        }
    }

    es.indices.create(index=INDEX_NAME, body=mapping)


def index_chunks_to_elasticsearch(
    document_id: UUID,
    chunk_records: List[dict],
) -> int:
    """
    chunk_records must contain:
        {
            "chunk_id": str,
            "chunk_index": int,
            "text": str,
            "metadata": dict | None
        }
    """

    if not chunk_records:
        return 0

    es = get_es_client()
    ensure_index_exists(es)

    actions = []

    for record in chunk_records:
        actions.append({
            "_index": INDEX_NAME,
            "_id": record["chunk_id"],
            "_source": {
                "chunk_id": record["chunk_id"],
                "document_id": str(document_id),
                "chunk_index": record["chunk_index"],
                "text": record["text"],
                "metadata": record.get("metadata"),
            }
        })

    bulk(es, actions)

    return len(actions)