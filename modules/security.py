"""
Security helpers for validating uploads and sanitizing untrusted content.
"""

import html
import io
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse


MAX_PDF_UPLOAD_SIZE = 5 * 1024 * 1024
PDF_SIGNATURE = b"%PDF-"


def escape_html(value: Any) -> str:
    """Escape text before rendering it in HTML."""
    return html.escape("" if value is None else str(value), quote=True)


def sanitize_external_url(url: Optional[str], fallback: str = "#") -> str:
    """Allow only absolute http(s) URLs for external links."""
    candidate = (url or "").strip()
    if not candidate:
        return fallback
    
    parsed = urlparse(candidate)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
        return fallback
    
    return escape_html(candidate)


def validate_pdf_upload(file_input, max_size_bytes: int = MAX_PDF_UPLOAD_SIZE) -> None:
    """Validate uploaded PDF files before parsing."""
    if isinstance(file_input, (str, Path)):
        path = Path(file_input)
        if path.suffix.lower() != ".pdf":
            raise ValueError("Only PDF resumes are supported.")
        if path.stat().st_size > max_size_bytes:
            raise ValueError("Resume PDF exceeds the 5 MB upload limit.")
        with path.open("rb") as pdf_file:
            header = pdf_file.read(len(PDF_SIGNATURE))
        if not header.startswith(PDF_SIGNATURE):
            raise ValueError("Resume file must be a valid PDF.")
        return
    
    name = getattr(file_input, "name", "")
    if name and not str(name).lower().endswith(".pdf"):
        raise ValueError("Only PDF resumes are supported.")
    
    size = _get_stream_size(file_input)
    if size is not None and size > max_size_bytes:
        raise ValueError("Resume PDF exceeds the 5 MB upload limit.")
    
    header = _peek_stream(file_input, len(PDF_SIGNATURE))
    if not header.startswith(PDF_SIGNATURE):
        raise ValueError("Resume file must be a valid PDF.")
    
    _rewind_stream(file_input)


def _get_stream_size(file_input) -> Optional[int]:
    if hasattr(file_input, "getbuffer"):
        return file_input.getbuffer().nbytes
    
    if hasattr(file_input, "seek") and hasattr(file_input, "tell"):
        current_pos = file_input.tell()
        file_input.seek(0, io.SEEK_END)
        size = file_input.tell()
        file_input.seek(current_pos)
        return size
    
    return None


def _peek_stream(file_input, size: int) -> bytes:
    if not hasattr(file_input, "read"):
        return b""
    
    if hasattr(file_input, "seek"):
        file_input.seek(0)
    header = file_input.read(size)
    if hasattr(file_input, "seek"):
        file_input.seek(0)
    return header


def _rewind_stream(file_input) -> None:
    if hasattr(file_input, "seek"):
        file_input.seek(0)
