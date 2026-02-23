# app/services/embedding/base.py

from abc import ABC, abstractmethod
from typing import List


class EmbeddingProvider(ABC):
    """
    Abstract base class for embedding providers.
    """

    @abstractmethod
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Takes a list of texts and returns a list of embeddings.
        Each embedding is a list of floats.
        """
        pass