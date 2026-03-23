# ingestion/elastic_indexer.py

import logging
from typing import List
from uuid import UUID

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from elasticsearch.exceptions import ConnectionError as ESConnectionError, RequestError

from app.config import settings

logger = logging.getLogger(__name__)

INDEX_NAME = "documents_chunks"


def get_es_client() -> Elasticsearch:
    es_url = settings.ELASTICSEARCH_URL
    logger.info(f"Connecting to Elasticsearch at {es_url}")
    try:
        # For ES 8.x, configure client with proper timeout settings
        # Elasticsearch Python client 9.x defaults to compatibility mode 9,
        # but ES 8.11.1 only supports modes 7 or 8, so we need to override headers
        es = Elasticsearch(
            es_url,
            request_timeout=30,
            max_retries=3,
            retry_on_timeout=True,
        )
        # Override default headers to use compatibility mode 8 for ES 8.11.1
        es._headers = {"Accept": "application/vnd.elasticsearch+json; compatible-with=8"}
        # Test connection using info() - more reliable than ping() in ES 8.x
        # ping() can return False even when ES is accessible, so we use info() instead
        try:
            info = es.options(request_timeout=10).info()
            cluster_name = info.get('cluster_name', 'unknown')
            version = info.get('version', {}).get('number', 'unknown')
            logger.info(f"Successfully connected to Elasticsearch cluster '{cluster_name}' (version {version})")
        except Exception as info_error:
            # If info() fails, try ping() as fallback
            logger.warning(f"Info() failed: {str(info_error)}, trying ping() as fallback")
            try:
                ping_result = es.options(request_timeout=10).ping()
                if not ping_result:
                    raise ConnectionError("Both info() and ping() failed - Elasticsearch is not accessible")
                logger.info("Ping() fallback successful")
            except Exception as ping_error:
                raise ConnectionError(f"Both info() and ping() failed. Info error: {str(info_error)}, Ping error: {str(ping_error)}")
        return es
    except ESConnectionError as e:
        # Re-raise Elasticsearch connection errors
        logger.error(f"Elasticsearch connection error: {str(e)}", exc_info=True)
        raise ConnectionError(f"Elasticsearch connection failed: {str(e)}") from e
    except Exception as e:
        logger.error(f"Failed to connect to Elasticsearch: {str(e)}", exc_info=True)
        # Wrap other exceptions in ConnectionError for consistency
        raise ConnectionError(f"Elasticsearch connection failed: {str(e)}") from e


def ensure_index_exists(es: Elasticsearch):
    try:
        if es.options(request_timeout=10).indices.exists(index=INDEX_NAME):
            logger.info(f"Elasticsearch index '{INDEX_NAME}' already exists")
            return

        logger.info(f"Creating Elasticsearch index '{INDEX_NAME}'")
        index_settings = {
            "number_of_shards": 1,
            "number_of_replicas": 0,
        }
        mapping = {
            "settings": index_settings,
            "mappings": {
                "properties": {
                    "chunk_id": {"type": "keyword"},
                    "document_id": {"type": "keyword"},
                    "chunk_index": {"type": "integer"},
                    "page_number": {"type": "integer"},
                    "token_count": {"type": "integer"},
                    "text": {
                        "type": "text",
                        "analyzer": "standard"
                    },
                    "metadata": {"type": "object"},
                }
            },
        }

        # Use the newer API format for ES 8+
        try:
            es.options(request_timeout=10).indices.create(
                index=INDEX_NAME,
                settings=index_settings,
                mappings=mapping["mappings"],
            )
        except TypeError:
            # Fallback to older API format
            es.options(request_timeout=10).indices.create(index=INDEX_NAME, body=mapping)
        logger.info(f"Successfully created Elasticsearch index '{INDEX_NAME}'")
    except Exception as e:
        logger.error(f"Error ensuring index exists: {str(e)}")
        raise


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
        logger.warning("No chunk records provided for Elasticsearch indexing")
        return 0

    logger.info(f"Preparing to index {len(chunk_records)} chunks to Elasticsearch")
    
    try:
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
                    "page_number": record.get("page_number"),
                    "token_count": record.get("token_count"),
                    "text": record["text"],
                    "metadata": record.get("metadata"),
                }
            })

        logger.info(f"Bulk indexing {len(actions)} documents to Elasticsearch")
        result = bulk(es, actions, raise_on_error=False)
        
        # Check for errors in bulk operation
        if result[1]:
            errors = [item for item in result[1] if item.get("index", {}).get("error")]
            if errors:
                logger.error(f"Elasticsearch bulk indexing errors: {errors}")
                raise RequestError(f"Bulk indexing failed with {len(errors)} errors")
        
        logger.info(f"Successfully indexed {len(actions)} chunks to Elasticsearch")
        return len(actions)
    except ESConnectionError as e:
        logger.error(f"Elasticsearch connection error: {str(e)}", exc_info=True)
        raise ConnectionError(f"Elasticsearch connection failed: {str(e)}") from e
    except RequestError as e:
        logger.error(f"Elasticsearch request error: {str(e)}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Unexpected error during Elasticsearch indexing: {str(e)}", exc_info=True)
        # Wrap in ConnectionError if it's a connection-related issue
        if "connection" in str(e).lower() or "connect" in str(e).lower():
            raise ConnectionError(f"Elasticsearch connection failed: {str(e)}") from e
        raise