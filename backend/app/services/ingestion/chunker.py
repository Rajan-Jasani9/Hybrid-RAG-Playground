# ingestion/chunker.py

from typing import List, Tuple
from dataclasses import dataclass

from transformers import AutoTokenizer

# Use same tokenizer as the embedding model (E5)
tokenizer = AutoTokenizer.from_pretrained("intfloat/e5-large-v2")


@dataclass
class ChunkWithMetadata:
    """A chunk with its associated metadata."""
    text: str
    page_number: int | None
    token_count: int
    start_char: int  # Character position in original text
    end_char: int


def chunk_text(
    text: str,
    pages: List,  # List of ParsedPage objects from parser
    chunk_size: int = 512,
    overlap: int = 200,
) -> List[ChunkWithMetadata]:
    """
    Token-based chunking using the E5 tokenizer, with page number tracking.

    - Each chunk is at most `chunk_size` tokens.
    - Consecutive chunks overlap by `overlap` tokens to preserve context.
    - Tracks which page each chunk comes from.
    """

    if chunk_size <= 0:
        raise ValueError("chunk_size must be > 0")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be >= 0 and < chunk_size")

    # Build character-to-page mapping
    char_to_page: List[int] = []
    char_pos = 0
    for page in pages:
        page_text = page.text
        # Map each character in this page to the page number
        for _ in range(len(page_text)):
            char_to_page.append(page.page_number)
        # Add newline separator
        if char_pos < len(text) - 1:
            char_to_page.append(page.page_number)
            char_pos += 1

    tokens = tokenizer.encode(text, add_special_tokens=False)
    token_to_char = _build_token_to_char_mapping(text, tokens)

    chunks: List[ChunkWithMetadata] = []
    start = 0

    while start < len(tokens):
        end = start + chunk_size
        chunk_tokens = tokens[start:end]
        if not chunk_tokens:
            break

        chunk_text_str = tokenizer.decode(chunk_tokens)
        
        # Find character positions for this chunk
        start_char = token_to_char[start] if start < len(token_to_char) else 0
        end_char = token_to_char[min(end - 1, len(token_to_char) - 1)] if token_to_char else len(text)
        
        # Determine page number (use the page of the start character)
        page_number = None
        if start_char < len(char_to_page):
            page_number = char_to_page[start_char]
        elif char_to_page:
            page_number = char_to_page[-1]

        chunks.append(ChunkWithMetadata(
            text=chunk_text_str,
            page_number=page_number,
            token_count=len(chunk_tokens),
            start_char=start_char,
            end_char=end_char
        ))

        # Slide window forward with overlap
        start = end - overlap

    return chunks


def _build_token_to_char_mapping(text: str, tokens: List[int]) -> List[int]:
    """
    Build a mapping from token index to character position in the original text.
    Uses the tokenizer's offset mapping if available, otherwise approximates.
    """
    char_positions = []
    
    # Try to use tokenizer's offset mapping (if available)
    try:
        encoding = tokenizer(text, return_offsets_mapping=True, add_special_tokens=False)
        if hasattr(encoding, 'offset_mapping') and encoding.offset_mapping:
            for offset in encoding.offset_mapping:
                char_positions.append(offset[0] if offset else 0)
            return char_positions[:len(tokens)]
    except:
        pass
    
    # Fallback: approximate based on token lengths
    current_pos = 0
    for token_id in tokens:
        char_positions.append(current_pos)
        # Approximate token length (most tokens are 1-4 chars when decoded)
        token_str = tokenizer.decode([token_id], skip_special_tokens=True)
        current_pos += len(token_str)
    
    return char_positions