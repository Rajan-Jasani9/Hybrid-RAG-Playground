# app/services/embedding/factory.py 

from app.services.embedding.base import EmbeddingProvider
from app.services.embedding.e5 import E5EmbeddingProvider


def get_embedding_provider() -> EmbeddingProvider:
    # Later this can switch based on config
    return E5EmbeddingProvider()