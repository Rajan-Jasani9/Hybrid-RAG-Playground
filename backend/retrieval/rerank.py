from typing import List

from .base import RetrievedChunk


def semantic_mmr_rerank(
    chunks: List[RetrievedChunk],
    top_k: int = 10,
) -> List[RetrievedChunk]:
    """
    Placeholder for Semantic + MMR reranking.

    For now, this is an identity function that simply truncates to top_k.
    You can later implement full MMR using embeddings of the chunks.
    """
    return chunks[:top_k]

