# ingestion/chunker.py

from typing import List
from transformers import AutoTokenizer

# Use same tokenizer as embedding model
tokenizer = AutoTokenizer.from_pretrained("intfloat/e5-large-v2")


def chunk_text(
    text: str,
    chunk_size: int = 512,
    overlap: int = 64,
) -> List[str]:
    """
    Token-based chunking using E5 tokenizer.
    """

    tokens = tokenizer.encode(text, add_special_tokens=False)

    chunks = []
    start = 0

    while start < len(tokens):
        end = start + chunk_size
        chunk_tokens = tokens[start:end]

        chunk_text = tokenizer.decode(chunk_tokens)
        chunks.append(chunk_text)

        start = end - overlap

    return chunks