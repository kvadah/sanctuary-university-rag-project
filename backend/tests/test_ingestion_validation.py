"""Unit tests for upload file-type validation (pure, no services)."""
import pytest
from fastapi import HTTPException

from app.models.knowledge import KnowledgeSourceType
from app.services.ingestion_service import resolve_file_type, source_type_for


@pytest.mark.parametrize(
    "filename,expected",
    [
        ("handbook.pdf", "pdf"),
        ("Policy.PDF", "pdf"),  # case-insensitive
        ("notes.docx", "docx"),
        ("faq.txt", "txt"),
        ("a.b.c.pdf", "pdf"),  # only the last extension matters
    ],
)
def test_resolve_file_type_supported(filename, expected):
    assert resolve_file_type(filename) == expected


@pytest.mark.parametrize(
    "filename", [None, "", "noextension", "archive.zip", "image.png", "data.csv"]
)
def test_resolve_file_type_rejects_unsupported(filename):
    with pytest.raises(HTTPException) as exc:
        resolve_file_type(filename)
    assert exc.value.status_code == 400


def test_source_type_mapping():
    assert source_type_for("pdf") == KnowledgeSourceType.PDF
    assert source_type_for("docx") == KnowledgeSourceType.DOCX
    # TXT uploads are grouped under the FAQ source type.
    assert source_type_for("txt") == KnowledgeSourceType.FAQ
