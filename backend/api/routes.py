from typing import List
from pathlib import Path
import shutil
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models.document import Document
from app.services.ingestion.queue import enqueue_ingestion_task
from retrieval.base import RetrievalRequest, RetrievalResponse, RetrievalMode
from retrieval.vector import semantic_search
from retrieval.bm25 import keyword_search
from retrieval.hybrid import hybrid_search
from retrieval.rerank import semantic_mmr_rerank

router = APIRouter()


UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/ingest")
async def ingest_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Ingest a single file into the Hybrid RAG pipeline.
    """
    try:
        file_id = uuid.uuid4()
        file_path = UPLOAD_DIR / f"{file_id}_{file.filename}"

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Create document in DB with queued status
        document = Document(
            filename=file.filename,
            title=Path(file.filename).stem,
            status="queued",
        )
        db.add(document)
        db.commit()
        db.refresh(document)

        # Push task to Redis for background processing
        enqueue_ingestion_task(
            document_id=str(document.id),
            file_path=file_path,
        )

        return {
            "document_id": str(document.id),
            "status": document.status,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retrieve", response_model=RetrievalResponse)
async def retrieve(
    body: RetrievalRequest,
    db: Session = Depends(get_db),
):
    """
    Unified retrieval endpoint supporting:
      - semantic (pgvector)
      - keyword (Elasticsearch BM25)
      - hybrid (fusion)
      - semantic_mmr (semantic + basic MMR placeholder)
    """

    if not body.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    if body.mode == RetrievalMode.SEMANTIC:
        chunks = await semantic_search(
            db=db,
            query=body.query,
            top_k=body.top_k,
            document_ids=body.document_ids,
        )
    elif body.mode == RetrievalMode.KEYWORD:
        chunks = keyword_search(
            query=body.query,
            top_k=body.top_k,
            document_ids=body.document_ids,
        )
    elif body.mode == RetrievalMode.HYBRID:
        chunks = await hybrid_search(
            db=db,
            query=body.query,
            top_k=body.top_k,
            document_ids=body.document_ids,
        )
    elif body.mode == RetrievalMode.SEMANTIC_MMR:
        base_chunks = await semantic_search(
            db=db,
            query=body.query,
            top_k=body.top_k * 3,
            document_ids=body.document_ids,
        )
        chunks = semantic_mmr_rerank(base_chunks, top_k=body.top_k)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported mode: {body.mode}")

    return RetrievalResponse(
        mode=body.mode,
        top_k=body.top_k,
        chunks=chunks,
    )


@router.post("/ingest/batch")
async def ingest_files_batch(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    """
    Ingest multiple files in one request.

    This is intended to be called from the Data tab in the frontend,
    where a user can select a batch of documents to index.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    results = []

    try:
        for file in files:
            file_id = uuid.uuid4()
            file_path = UPLOAD_DIR / f"{file_id}_{file.filename}"

            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            document = Document(
                filename=file.filename,
                title=Path(file.filename).stem,
                status="queued",
            )
            db.add(document)
            db.commit()
            db.refresh(document)

            enqueue_ingestion_task(
                document_id=str(document.id),
                file_path=file_path,
            )

            results.append(
                {
                    "filename": file.filename,
                    "document_id": str(document.id),
                    "status": document.status,
                }
            )

        return {"items": results, "count": len(results)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))