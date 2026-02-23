# routes/ingestion.py

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from pathlib import Path
import shutil
import uuid

from app.db.session import get_db
from app.services.ingestion.pipeline import ingest_file_pipeline

router = APIRouter()


UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/ingest")
async def ingest_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    try:
        # Save file temporarily
        file_id = uuid.uuid4()
        file_path = UPLOAD_DIR / f"{file_id}_{file.filename}"

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        result = await ingest_file_pipeline(
            db=db,
            file_path=file_path,
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))