from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


class RetrievalMode(str, Enum):
    SEMANTIC = "semantic"
    KEYWORD = "keyword"
    HYBRID = "hybrid"
    SEMANTIC_MMR = "semantic_mmr"


class RetrievedChunk(BaseModel):
    chunk_id: str
    document_id: str
    text: str
    score: float
    source: str  # "vector", "bm25", "hybrid"


class RetrievalRequest(BaseModel):
    query: str
    mode: RetrievalMode = RetrievalMode.HYBRID
    top_k: int = 10
    document_ids: Optional[List[str]] = None


class RetrievalResponse(BaseModel):
    mode: RetrievalMode
    top_k: int
    chunks: List[RetrievedChunk]

