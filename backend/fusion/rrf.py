from collections import defaultdict
from typing import Dict, Iterable, List, Tuple


def reciprocal_rank_fusion(
    rankings: Iterable[Iterable[Tuple[str, float]]],
    k: int = 60,
) -> List[Tuple[str, float]]:
    """
    Simple Reciprocal Rank Fusion (RRF).

    rankings: list of rankings, each ranking is an iterable of (id, score) where
    earlier entries are considered better ranked.
    Returns: list of (id, fused_score) sorted by fused_score descending.
    """
    scores: Dict[str, float] = defaultdict(float)

    for ranking in rankings:
        for rank, (item_id, _) in enumerate(ranking, start=1):
            scores[item_id] += 1.0 / (k + rank)

    return sorted(scores.items(), key=lambda x: x[1], reverse=True)

