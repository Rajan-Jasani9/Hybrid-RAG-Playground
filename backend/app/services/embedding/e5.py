# app/services/embedding/e5.py

import asyncio
from typing import List

import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel

from app.services.embedding.base import EmbeddingProvider


class E5EmbeddingProvider(EmbeddingProvider):
    def __init__(self, model_name: str = "intfloat/e5-large-v2"):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.model.to(self.device)
        self.model.eval()

    def _mean_pooling(self, model_output, attention_mask):
        token_embeddings = model_output[0]
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(
            input_mask_expanded.sum(1), min=1e-9
        )

    def _embed_sync(self, texts: List[str]) -> List[List[float]]:
        encoded_input = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            return_tensors="pt",
            max_length=512,
        )

        encoded_input = {k: v.to(self.device) for k, v in encoded_input.items()}

        with torch.no_grad():
            model_output = self.model(**encoded_input)

        embeddings = self._mean_pooling(model_output, encoded_input["attention_mask"])

        # Normalize for cosine similarity
        embeddings = F.normalize(embeddings, p=2, dim=1)

        return embeddings.cpu().tolist()

    async def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Async wrapper to avoid blocking FastAPI event loop.
        """
        return await asyncio.to_thread(self._embed_sync, texts)