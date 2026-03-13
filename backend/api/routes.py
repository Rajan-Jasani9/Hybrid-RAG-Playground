from typing import List
from pathlib import Path
import shutil
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models.document import Document
from app.services.ingestion.queue import enqueue_ingestion_task

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