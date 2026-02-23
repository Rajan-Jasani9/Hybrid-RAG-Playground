# ingestion/parser.py

from pathlib import Path
from typing import Callable

from pypdf import PdfReader
from docx import Document as DocxDocument


def parse_txt(file_path: Path) -> str:
    return file_path.read_text(encoding="utf-8")


def parse_pdf(file_path: Path) -> str:
    reader = PdfReader(str(file_path))
    text_parts = []

    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text_parts.append(extracted)

    return "\n".join(text_parts)


def parse_docx(file_path: Path) -> str:
    doc = DocxDocument(str(file_path))
    return "\n".join([para.text for para in doc.paragraphs])


def parse_file(file_path: Path) -> str:
    """
    Detect file type and extract text.
    """

    suffix = file_path.suffix.lower()

    parsers: dict[str, Callable[[Path], str]] = {
        ".txt": parse_txt,
        ".pdf": parse_pdf,
        ".docx": parse_docx,
    }

    if suffix not in parsers:
        raise ValueError(f"Unsupported file type: {suffix}")

    text = parsers[suffix](file_path)

    if not text.strip():
        raise ValueError("Parsed file is empty.")

    return text