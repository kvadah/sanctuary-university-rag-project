"""Unit tests for the MinIO storage wrapper (mocked client — no live MinIO)."""
from unittest.mock import MagicMock, patch

from app.utils import storage


def test_build_object_key_namespaces_under_job():
    key = storage.build_object_key("job-123", "Student Handbook.pdf")
    assert key == "uploads/job-123/Student Handbook.pdf"


def test_build_object_key_sanitizes_path_separators():
    # A filename can't be allowed to climb out of its job prefix.
    key = storage.build_object_key("j1", "../../etc/passwd")
    assert key.startswith("uploads/j1/")
    assert "/etc/passwd" not in key


def test_build_object_key_handles_missing_filename():
    key = storage.build_object_key("j1", "")
    assert key == "uploads/j1/upload"


def test_put_object_shapes_client_call():
    fake = MagicMock()
    with patch.object(storage, "_client", return_value=fake):
        returned = storage.put_object("uploads/j1/a.pdf", b"hello", "application/pdf")

    assert returned == "uploads/j1/a.pdf"
    assert fake.put_object.call_count == 1
    args, kwargs = fake.put_object.call_args
    # (bucket, key, stream, ...) positional; length + content_type as kwargs.
    assert args[1] == "uploads/j1/a.pdf"
    assert kwargs["length"] == 5
    assert kwargs["content_type"] == "application/pdf"


def test_get_object_reads_and_releases():
    fake = MagicMock()
    response = MagicMock()
    response.read.return_value = b"data"
    fake.get_object.return_value = response
    with patch.object(storage, "_client", return_value=fake):
        data = storage.get_object("uploads/j1/a.pdf")

    assert data == b"data"
    response.close.assert_called_once()
    response.release_conn.assert_called_once()


def test_ensure_bucket_creates_when_missing():
    fake = MagicMock()
    fake.bucket_exists.return_value = False
    with patch.object(storage, "_client", return_value=fake):
        storage.ensure_bucket()
    fake.make_bucket.assert_called_once()


def test_ensure_bucket_noop_when_present():
    fake = MagicMock()
    fake.bucket_exists.return_value = True
    with patch.object(storage, "_client", return_value=fake):
        storage.ensure_bucket()
    fake.make_bucket.assert_not_called()
