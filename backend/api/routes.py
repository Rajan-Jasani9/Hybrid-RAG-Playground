from typing import List
from pathlib import Path
import shutil
import uuid
import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models.document import Document
from app.services.ingestion.queue import enqueue_ingestion_task
from retrieval.base import RetrievalRequest, RetrievalResponse, RetrievalMode
from retrieval.vector import semantic_search
from retrieval.bm25 import keyword_search
from retrieval.hybrid import hybrid_search
from retrieval.rerank import semantic_mmr_rerank

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


class DocumentListItem(BaseModel):
    filename: str
    document_id: str
    status: str


class DocumentListResponse(BaseModel):
    items: List[DocumentListItem]
    count: int


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
    logger.info(f"Received batch upload request with {len(files) if files else 0} files")
    
    if not files:
        logger.warning("No files provided in batch upload request")
        raise HTTPException(status_code=400, detail="No files uploaded")

    results = []

    try:
        logger.info("Starting file processing loop")
        for idx, file in enumerate(files):
            logger.info(f"Processing file {idx + 1}/{len(files)}: {file.filename}")
            
            try:
                file_id = uuid.uuid4()
                file_path = UPLOAD_DIR / f"{file_id}_{file.filename}"
                logger.info(f"Created file path: {file_path}")

                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                logger.info(f"File saved to disk: {file_path}")

                logger.info("Creating Document model instance")
                document = Document(
                    filename=file.filename,
                    title=Path(file.filename).stem,
                    status="queued",
                )
                logger.info(f"Document model created: filename={document.filename}, status={document.status}")
                
                logger.info("Adding document to database session")
                db.add(document)
                logger.info("Committing document to database")
                db.commit()
                logger.info(f"Document committed with ID: {document.id}")
                
                db.refresh(document)
                logger.info(f"Document refreshed: id={document.id}, status={document.status}")

                logger.info("Enqueueing ingestion task")
                enqueue_ingestion_task(
                    document_id=str(document.id),
                    file_path=file_path,
                )
                logger.info(f"Ingestion task enqueued for document {document.id}")

                results.append(
                    {
                        "filename": file.filename,
                        "document_id": str(document.id),
                        "status": document.status,
                    }
                )
                logger.info(f"Added result for file {file.filename}: {results[-1]}")
                
            except Exception as file_error:
                logger.error(f"Error processing file {file.filename}: {str(file_error)}", exc_info=True)
                raise

        logger.info(f"Batch upload completed successfully. Processed {len(results)} files")
        return {"items": results, "count": len(results)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch upload: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/documents/{document_id}")
def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
):
    """
    Delete a document and all its associated chunks.
    Also removes the document from Elasticsearch and deletes the uploaded file.
    """
    logger.info(f"Received request to delete document {document_id}")
    
    try:
        from uuid import UUID as UUIDType
        from app.db.models.chunk import Chunk
        from app.services.ingestion.elastic_indexer import get_es_client, INDEX_NAME
        import glob
        
        # Convert string to UUID
        try:
            doc_uuid = UUIDType(document_id)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid document ID format: {document_id}")
        
        # Find the document
        document = db.query(Document).filter(Document.id == doc_uuid).first()
        if document is None:
            raise HTTPException(status_code=404, detail=f"Document {document_id} not found")
        
        logger.info(f"Found document: {document.filename} (status: {document.status})")
        
        # Count chunks before deletion (for logging)
        chunk_count = db.query(Chunk).filter(Chunk.document_id == doc_uuid).count()
        logger.info(f"Document has {chunk_count} chunks that will be deleted")
        
        # Delete from Elasticsearch if available
        try:
            es = get_es_client()
            # Use options() for ES 8.x compatibility
            if es.options(request_timeout=10).indices.exists(index=INDEX_NAME):
                logger.info(f"Deleting chunks from Elasticsearch for document {document_id}")
                # Use the newer API format (ES 8+ uses query parameter instead of body)
                try:
                    es.options(request_timeout=30).delete_by_query(
                        index=INDEX_NAME,
                        query={
                            "term": {
                                "document_id": document_id
                            }
                        }
                    )
                except TypeError:
                    # Fallback to older body format
                    es.options(request_timeout=30).delete_by_query(
                        index=INDEX_NAME,
                        body={
                            "query": {
                                "term": {
                                    "document_id": document_id
                                }
                            }
                        }
                    )
                logger.info("Successfully deleted chunks from Elasticsearch")
        except Exception as es_error:
            logger.warning(f"Failed to delete from Elasticsearch (non-critical): {str(es_error)}")
            # Continue with deletion even if ES fails
        
        # Delete uploaded file if it exists
        try:
            # Find files matching the document ID pattern
            pattern = str(UPLOAD_DIR / f"*_{document.filename}")
            matching_files = glob.glob(pattern)
            for file_path in matching_files:
                file_path_obj = Path(file_path)
                if file_path_obj.exists():
                    logger.info(f"Deleting uploaded file: {file_path}")
                    file_path_obj.unlink()
                    logger.info(f"Successfully deleted file: {file_path}")
        except Exception as file_error:
            logger.warning(f"Failed to delete uploaded file (non-critical): {str(file_error)}")
            # Continue with deletion even if file deletion fails
        
        # Delete document (chunks will be cascade deleted by database)
        logger.info(f"Deleting document {document_id} from database")
        db.delete(document)
        db.commit()
        logger.info(f"Successfully deleted document {document_id} and {chunk_count} chunks")
        
        return {
            "message": f"Document {document.filename} deleted successfully",
            "document_id": document_id,
            "chunks_deleted": chunk_count,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        logger.error(f"Error deleting document {document_id}: {error_detail}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents", response_model=DocumentListResponse)
def list_documents(
    db: Session = Depends(get_db),
):
    """
    List all uploaded documents with their current status.
    Returns documents ordered by creation date (newest first).
    """
    logger.info("Received request to list documents")
    
    try:
        logger.info("Starting database query for documents")
        logger.info(f"Database session: {db}")
        logger.info(f"Document model: {Document}")
        logger.info(f"Document table name: {Document.__tablename__}")
        
        # Check if table exists using the engine directly (not db.bind)
        from app.db.session import engine
        from sqlalchemy import inspect as sql_inspect
        
        logger.info("Inspecting database schema")
        inspector = sql_inspect(engine)
        tables = inspector.get_table_names()
        logger.info(f"Available tables in database: {tables}")
        
        if Document.__tablename__ not in tables:
            logger.error(f"Table '{Document.__tablename__}' not found in database!")
            raise HTTPException(
                status_code=500, 
                detail=f"Table '{Document.__tablename__}' does not exist. Available tables: {tables}"
            )
        
        # Check table columns
        logger.info(f"Checking columns in '{Document.__tablename__}' table")
        columns = inspector.get_columns(Document.__tablename__)
        column_names = [col['name'] for col in columns]
        logger.info(f"Columns in '{Document.__tablename__}' table: {column_names}")
        
        if 'status' not in column_names:
            logger.error(f"Column 'status' not found in '{Document.__tablename__}' table!")
            raise HTTPException(
                status_code=500,
                detail=f"Column 'status' does not exist in '{Document.__tablename__}' table. Available columns: {column_names}"
            )
        
        logger.info("Executing query: db.query(Document).order_by(Document.created_at.desc()).all()")
        # Use synchronous query execution
        documents = db.query(Document).order_by(Document.created_at.desc()).all()
        logger.info(f"Query returned {len(documents)} documents")
        
        items = []
        for idx, doc in enumerate(documents):
            try:
                logger.info(f"Processing document {idx + 1}/{len(documents)}: id={doc.id}, filename={doc.filename}")
                logger.info(f"Document attributes: id={doc.id}, filename={doc.filename}, status={doc.status}")
                
                item = DocumentListItem(
                    filename=doc.filename,
                    document_id=str(doc.id),
                    status=doc.status,
                )
                items.append(item)
                logger.info(f"Added item: {item}")
            except Exception as doc_error:
                logger.error(f"Error processing document {idx + 1}: {str(doc_error)}", exc_info=True)
                raise
        
        logger.info(f"Successfully created {len(items)} items")
        response = DocumentListResponse(items=items, count=len(items))
        logger.info(f"Returning response with {response.count} items")
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        logger.error(f"Error in list_documents: {error_detail}", exc_info=True)
        raise HTTPException(status_code=500, detail=error_detail)