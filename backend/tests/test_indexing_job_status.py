"""Unit tests for IndexingJob status transitions.

Uses a minimal fake AsyncSession and drives the async repository methods with
``asyncio.run`` so the suite stays synchronous and needs no running database.
"""
import asyncio
import uuid

from app.models.audit import IndexingJob, IndexingStatus
from app.repositories.indexing_job_repository import IndexingJobRepository


class _FakeResult:
    def __init__(self, obj):
        self._obj = obj

    def scalar_one_or_none(self):
        return self._obj


class _FakeSession:
    """Records add/flush and returns a fixed row from execute()."""

    def __init__(self, existing=None):
        self.existing = existing
        self.added = []
        self.flush_count = 0

    def add(self, obj):
        self.added.append(obj)

    async def flush(self):
        self.flush_count += 1

    async def refresh(self, obj):
        pass

    async def execute(self, *_args, **_kwargs):
        return _FakeResult(self.existing)


def _run(coro):
    return asyncio.run(coro)


def _job(status: IndexingStatus) -> IndexingJob:
    return IndexingJob(
        source_id=uuid.uuid4(), status=status.value, total_documents=1
    )


def test_create_sets_pending_defaults():
    session = _FakeSession()
    repo = IndexingJobRepository(session)
    job = _run(repo.create(source_id=uuid.uuid4(), original_filename="h.pdf"))

    assert job.status == IndexingStatus.PENDING.value
    assert job.total_documents == 1
    assert job.processed_documents == 0
    assert job.chunk_count == 0
    assert job.original_filename == "h.pdf"
    assert job in session.added
    assert session.flush_count >= 1


def test_set_status_moves_to_processing():
    existing = _job(IndexingStatus.PENDING)
    repo = IndexingJobRepository(_FakeSession(existing=existing))

    updated = _run(repo.set_status(uuid.uuid4(), IndexingStatus.PROCESSING))
    assert updated is existing
    assert existing.status == IndexingStatus.PROCESSING.value


def test_set_completed_records_document_and_chunks():
    existing = _job(IndexingStatus.PROCESSING)
    repo = IndexingJobRepository(_FakeSession(existing=existing))
    doc_id = uuid.uuid4()

    _run(repo.set_completed(uuid.uuid4(), document_id=doc_id, chunk_count=7))
    assert existing.status == IndexingStatus.COMPLETED.value
    assert existing.document_id == doc_id
    assert existing.chunk_count == 7
    assert existing.processed_documents == 1
    assert existing.error_message is None


def test_set_failed_records_and_truncates_message():
    existing = _job(IndexingStatus.PROCESSING)
    repo = IndexingJobRepository(_FakeSession(existing=existing))

    _run(repo.set_failed(uuid.uuid4(), "x" * 5000))
    assert existing.status == IndexingStatus.FAILED.value
    assert existing.error_message is not None
    assert len(existing.error_message) == 2000  # capped


def test_setters_return_none_when_job_missing():
    repo = IndexingJobRepository(_FakeSession(existing=None))
    assert _run(repo.set_status(uuid.uuid4(), IndexingStatus.PROCESSING)) is None
    assert (
        _run(
            repo.set_completed(
                uuid.uuid4(), document_id=uuid.uuid4(), chunk_count=1
            )
        )
        is None
    )
    assert _run(repo.set_failed(uuid.uuid4(), "e")) is None
