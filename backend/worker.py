import asyncio
from pathlib import Path
from uuid import UUID

from app.db.session import SessionLocal
from app.db.models.document import Document
from app.services.ingestion.pipeline import ingest_file_pipeline
from app.services.ingestion.queue import pop_ingestion_task


async def process_single_task(document_id: str, file_path: str) -> None:
    db = SessionLocal()
    try:
        doc = (
            db.query(Document)
            .filter(Document.id == UUID(document_id))
            .first()
        )
        if doc is None:
            return

        doc.status = "processing"
        db.commit()

        await ingest_file_pipeline(
            db=db,
            document_id=UUID(document_id),
            file_path=Path(file_path),
        )
    except Exception:
        # Best-effort: mark document as failed
        try:
            doc = (
                db.query(Document)
                .filter(Document.id == UUID(document_id))
                .first()
            )
            if doc is not None:
                doc.status = "failed"
                db.commit()
        except Exception:
            pass
    finally:
        db.close()


def run_worker() -> None:
    """
    Long-running worker that listens to Redis for ingestion tasks.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    while True:
        task = pop_ingestion_task(block=True, timeout=5)
        if task is None:
            continue

        loop.run_until_complete(
            process_single_task(task.document_id, task.file_path)
        )


if __name__ == "__main__":
    run_worker()

