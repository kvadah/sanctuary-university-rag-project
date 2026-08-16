from app.utils.chunking import Chunk, chunk_pages, count_tokens


def test_count_tokens_nonzero():
    assert count_tokens("hello world") > 0
    assert count_tokens("") == 0


def test_chunk_pages_splits_long_text_with_overlap():
    text = " ".join(f"word{i}" for i in range(400))
    chunks = chunk_pages([(1, text)], max_tokens=100, overlap=20)

    assert len(chunks) > 1
    # chunk_index is sequential and global
    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))
    # page number is propagated and token budget respected
    assert all(c.page_number == 1 for c in chunks)
    assert all(c.token_count <= 100 for c in chunks)
    assert all(isinstance(c, Chunk) for c in chunks)


def test_chunk_pages_keeps_pages_separate():
    chunks = chunk_pages(
        [(1, "alpha beta gamma"), (2, "delta epsilon zeta")],
        max_tokens=100,
        overlap=0,
    )
    assert {c.page_number for c in chunks} == {1, 2}


def test_chunk_pages_skips_blank_pages():
    chunks = chunk_pages([(1, "   "), (2, "real content here")], max_tokens=100, overlap=0)
    assert len(chunks) == 1
    assert chunks[0].page_number == 2


def test_chunk_pages_rejects_bad_overlap():
    import pytest

    with pytest.raises(ValueError):
        chunk_pages([(1, "x")], max_tokens=10, overlap=10)
