"""Unit tests for the in-process BM25 lexical index (pure, no services).

``rank_bm25`` is a local, deterministic library, so these run without a DB or
network — the index is built directly from fixture rows via ``build_from_rows``.
"""
import uuid
from types import SimpleNamespace

from app.models.knowledge import DocumentClassification
from app.retrieval.bm25_index import BM25Index, _tokenize

ALL_CLASSES = [
    DocumentClassification.PUBLIC,
    DocumentClassification.STUDENT,
    DocumentClassification.FACULTY,
    DocumentClassification.STAFF,
    DocumentClassification.ADMIN,
]


def _row(content, classification=DocumentClassification.PUBLIC, term=None, title="Doc"):
    return SimpleNamespace(
        chunk_id=uuid.uuid4(),
        content=content,
        document_id=uuid.uuid4(),
        document_title=title,
        classification=classification,
        academic_term=term,
        page_number=1,
        section_title=None,
    )


def test_tokenize_lowercases_and_splits_on_punctuation():
    assert _tokenize("Fall-2026 Policy!") == ["fall", "2026", "policy"]


def test_lexical_match_ranks_relevant_chunk_first():
    index = BM25Index.build_from_rows(
        [
            _row("The library closes at midnight during finals week."),
            _row("Parking permits are issued at the transportation office."),
            _row("Graduation ceremony details and cap and gown pickup."),
        ]
    )
    results = index.search("library hours", ALL_CLASSES, top_k=3)
    assert results
    assert "library" in results[0].content.lower()


def test_rbac_excludes_disallowed_classifications():
    index = BM25Index.build_from_rows(
        [
            _row("Confidential admin budget figures.", DocumentClassification.ADMIN),
            _row("Public budget overview for everyone.", DocumentClassification.PUBLIC),
        ]
    )
    allowed = [DocumentClassification.PUBLIC, DocumentClassification.STUDENT]
    results = index.search("budget", allowed, top_k=5)
    assert results
    assert all(r.classification == "PUBLIC" for r in results)


def test_academic_term_filter():
    index = BM25Index.build_from_rows(
        [
            _row("Enrollment deadline information.", term="Fall 2026"),
            _row("Enrollment deadline information.", term="Spring 2026"),
        ]
    )
    results = index.search(
        "enrollment deadline", ALL_CLASSES, academic_term="Fall 2026", top_k=5
    )
    assert results
    assert all(r.academic_term == "Fall 2026" for r in results)


def test_empty_index_returns_nothing():
    index = BM25Index.build_from_rows([])
    assert index.search("anything", ALL_CLASSES, top_k=5) == []
