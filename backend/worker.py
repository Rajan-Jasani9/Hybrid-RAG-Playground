import asyncio
import logging
import traceback
from pathlib import Path
from uuid import UUID

from app.db.session import SessionLocal
from app.db.models.document import Document
from app.services.ingestion.pipeline import ingest_file_pipeline
from app.services.ingestion.queue import pop_ingestion_task

logger = logging.getLogger(__name__)


async def process_single_task(document_id: str, file_path: str) -> None:
    db = SessionLocal()
    try:
        doc = (
            db.query(Document)
            .filter(Document.id == UUID(document_id))
            .first()
        )
        if doc is None:
            logger.warning(f"Document {document_id} not found in database")
            return

        logger.info(f"Processing document {document_id}: {doc.filename}")
        doc.status = "processing"
        db.commit()

        await ingest_file_pipeline(
            db=db,
            document_id=UUID(document_id),
            file_path=Path(file_path),
        )
        logger.info(f"Successfully processed document {document_id}")
    except Exception as e:
        logger.error(f"Error processing document {document_id}: {str(e)}", exc_info=True)
        logger.error(f"Traceback: {traceback.format_exc()}")
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
                logger.info(f"Marked document {document_id} as failed")
        except Exception as db_error:
            logger.error(f"Failed to update document status: {str(db_error)}")
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

