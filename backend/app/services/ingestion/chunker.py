# ingestion/chunker.py

from typing import List

from transformers import AutoTokenizer

# Use same tokenizer as the embedding model (E5)
tokenizer = AutoTokenizer.from_pretrained("intfloat/e5-large-v2")


def chunk_text(
    text: str,
    chunk_size: int = 512,
    overlap: int = 200,
) -> List[str]:
    """
    Token-based chunking using the E5 tokenizer.

    - Each chunk is at most `chunk_size` tokens.
    - Consecutive chunks overlap by `overlap` tokens to preserve context.
    """

    if chunk_size <= 0:
        raise ValueError("chunk_size must be > 0")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be >= 0 and < chunk_size")

    tokens = tokenizer.encode(text, add_special_tokens=False)

    chunks: List[str] = []
    start = 0

    while start < len(tokens):
        end = start + chunk_size
        chunk_tokens = tokens[start:end]
        if not chunk_tokens:
            break

        chunk_text_str = tokenizer.decode(chunk_tokens)
        chunks.append(chunk_text_str)

        # Slide window forward with overlap
        start = end - overlap

    return chunks