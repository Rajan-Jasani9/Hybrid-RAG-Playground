# ingestion/pipeline.py

import uuid
from pathlib import Path
from typing import List

from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.chunk import Chunk

from ingestion.parser import parse_file
from ingestion.chunker import chunk_text
from ingestion.vector_indexer import index_chunks_to_vector_db
from ingestion.elastic_indexer import index_chunks_to_elasticsearch


async def ingest_file_pipeline(
    db: Session,
    file_path: Path,
) -> dict:
    """
    Full ingestion orchestration.
    """

    # 1️⃣ Parse file
    raw_text = parse_file(file_path)

    # 2️⃣ Chunk
    chunks = chunk_text(raw_text)

    if not chunks:
        raise ValueError("No chunks generated from file.")

    # 3️⃣ Create Document
    document = Document(
        filename=file_path.name,
        title=file_path.stem,
    )

    db.add(document)
    db.flush()  # get document.id without committing

    # 4️⃣ Vector index (Postgres)
    await index_chunks_to_vector_db(
        db=db,
        document_id=document.id,
        chunks=chunks,
    )

    # 5️⃣ Fetch inserted chunks for ES indexing
    inserted_chunks: List[Chunk] = (
        db.query(Chunk)
        .filter(Chunk.document_id == document.id)
        .all()
    )

    # 6️⃣ Prepare ES records
    es_records = [
        {
            "chunk_id": str(chunk.id),
            "chunk_index": chunk.chunk_index,
            "text": chunk.text,
            "metadata": chunk.other_metadata,
        }
        for chunk in inserted_chunks
    ]

    # 7️⃣ Elastic index
    index_chunks_to_elasticsearch(
        document_id=document.id,
        chunk_records=es_records,
    )

    return {
        "document_id": str(document.id),
        "num_chunks": len(inserted_chunks),
    }