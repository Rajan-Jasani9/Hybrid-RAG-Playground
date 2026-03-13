# ingestion/pipeline.py

from pathlib import Path
from typing import List
from uuid import UUID

from sqlalchemy.orm import Session
from elasticsearch import Elasticsearch

from app.db.models.document import Document
from app.db.models.chunk import Chunk
from app.services.ingestion.parser import parse_file
from app.services.ingestion.chunker import chunk_text
from app.services.ingestion.vector_indexer import index_chunks_to_vector_db
from app.services.ingestion.elastic_indexer import (
    index_chunks_to_elasticsearch,
    get_es_client,
    INDEX_NAME,
)


async def ingest_file_pipeline(
    db: Session,
    document_id: UUID,
    file_path: Path,
) -> dict:
    """
    Full ingestion orchestration for a pre-created Document.

    The API layer should create a `Document` row with status `queued` / `processing`,
    then enqueue a task to a worker which calls this function.
    """

    document = (
        db.query(Document)
        .filter(Document.id == document_id)
        .first()
    )
    if document is None:
        raise ValueError(f"Document {document_id} not found")

    # 1️⃣ Parse file
    raw_text = parse_file(file_path)

    # 2️⃣ Chunk
    chunks = chunk_text(raw_text)

    if not chunks:
        document.status = "failed"
        db.commit()
        raise ValueError("No chunks generated from file.")

    # 3️⃣ Vector index (Postgres)
    await index_chunks_to_vector_db(
        db=db,
        document_id=document.id,
        chunks=chunks,
    )

    # 4️⃣ Fetch inserted chunks for ES indexing
    inserted_chunks: List[Chunk] = (
        db.query(Chunk)
        .filter(Chunk.document_id == document.id)
        .all()
    )

    # 5️⃣ Prepare ES records
    es_records = [
        {
            "chunk_id": str(chunk.id),
            "chunk_index": chunk.chunk_index,
            "text": chunk.text,
            "metadata": chunk.other_metadata,
        }
        for chunk in inserted_chunks
    ]

    # 6️⃣ Elastic index
    index_chunks_to_elasticsearch(
        document_id=document.id,
        chunk_records=es_records,
    )

    # 7️⃣ Mark document as completed
    document.status = "completed"
    db.commit()

    return {
        "document_id": str(document.id),
        "num_chunks": len(inserted_chunks),
    }


def get_ingestion_status(
    db: Session,
    document_id: UUID,
) -> dict:
    """
    Check status of the ingestion pipeline for a given document.

    - Verifies the document exists.
    - Counts chunks stored in Postgres (pgvector table `chunks`).
    - Counts chunks indexed in Elasticsearch for this document.
    """

    # Check document existence
    document = db.query(Document).filter(Document.id == document_id).first()
    exists = document is not None

    # Count chunks in Postgres
    pg_chunk_count: int = (
        db.query(Chunk)
        .filter(Chunk.document_id == document_id)
        .count()
    )

    # Count chunks in Elasticsearch
    es_chunk_count = 0
    try:
        es: Elasticsearch = get_es_client()
        if es.indices.exists(index=INDEX_NAME):
            es_resp = es.count(
                index=INDEX_NAME,
                body={
                    "query": {
                        "term": {
                            "document_id": str(document_id),
                        }
                    }
                },
            )
            es_chunk_count = es_resp.get("count", 0)
    except Exception:
        # If ES is unavailable, we just report 0 and let caller decide how to handle it
        es_chunk_count = 0

    return {
        "document_exists": exists,
        "document_id": str(document_id),
        "pgvector_chunk_count": pg_chunk_count,
        "elasticsearch_chunk_count": es_chunk_count,
    }