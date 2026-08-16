"""Document text extraction for uploaded files.

Returns a list of ``(page_number, text)`` tuples. Only PDFs carry real page
numbers; DOCX/TXT yield a single ``(None, text)`` entry. These are synchronous,
CPU-bound functions — callers should run them via ``run_in_threadpool``.
"""
from io import BytesIO
from typing import List, Optional, Tuple

Page = Tuple[Optional[int], str]

SUPPORTED_TYPES = ("pdf", "docx", "txt")


def extract_pages(data: bytes, file_type: str) -> List[Page]:
    """Extract text from ``data`` according to ``file_type`` (``pdf``/``docx``/``txt``).

    Raises ``ValueError`` for unsupported or unparseable content.
    """
    file_type = file_type.lower().lstrip(".")
    if file_type == "pdf":
        return _extract_pdf(data)
    if file_type == "docx":
        return _extract_docx(data)
    if file_type == "txt":
        return _extract_txt(data)
    raise ValueError(
        f"Unsupported file type '{file_type}'. Supported: {', '.join(SUPPORTED_TYPES)}."
    )


def _extract_pdf(data: bytes) -> List[Page]:
    from pypdf import PdfReader

    try:
        reader = PdfReader(BytesIO(data))
    except Exception as exc:  # pypdf raises a variety of errors on bad input
        raise ValueError(f"Could not read PDF: {exc}") from exc

    pages: List[Page] = []
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        pages.append((i, text))
    return pages


def _extract_docx(data: bytes) -> List[Page]:
    import docx

    try:
        document = docx.Document(BytesIO(data))
    except Exception as exc:
        raise ValueError(f"Could not read DOCX: {exc}") from exc

    text = "\n".join(p.text for p in document.paragraphs if p.text)
    return [(None, text)]


def _extract_txt(data: bytes) -> List[Page]:
    return [(None, data.decode("utf-8", errors="ignore"))]
