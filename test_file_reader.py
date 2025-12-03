import pytest
from file_reader import FileReader


def test_validate_ok(tmp_path):
    """When the file exists and is a regular file, no exception should be raised."""
    p = tmp_path / "file.txt"
    p.write_text("data", encoding="utf-8")

    # If no exception is raised, the test passes
    FileReader.validate(str(p))


def test_validate_not_exists(tmp_path):
    """When the file does not exist, FileNotFoundError should be raised."""
    p = tmp_path / "no_such_file.txt"

    with pytest.raises(FileNotFoundError):
        FileReader.validate(str(p))


def test_validate_is_dir(tmp_path):
    """When the path points to a directory, ValueError should be raised."""
    with pytest.raises(ValueError):
        FileReader.validate(str(tmp_path))


def test_chunks_splits_content(tmp_path):
    """
    If chunk_size is smaller than the file size,
    the content should be split into multiple chunks.
    """
    p = tmp_path / "file.bin"
    p.write_bytes(b"abcdefghijkl")  # 12 bytes

    chunks = list(FileReader.chunks(str(p), chunk_size=5))

    assert chunks == [b"abcde", b"fghij", b"kl"]


def test_chunks_full_file_in_one_chunk(tmp_path):
    """If chunk_size >= file size, the whole file should be returned as one chunk."""
    p = tmp_path / "file.bin"
    p.write_bytes(b"abcdef")

    chunks = list(FileReader.chunks(str(p), chunk_size=100))

    assert chunks == [b"abcdef"]


def test_chunks_default_chunk_size(tmp_path):
    """
    When chunk_size=None, FileReader.CHUNK_SIZE should be used.
    We temporarily override CHUNK_SIZE in the test.
    """
    p = tmp_path / "file.bin"
    p.write_bytes(b"abcdef")

    original = FileReader.CHUNK_SIZE
    FileReader.CHUNK_SIZE = 3
    try:
        chunks = list(FileReader.chunks(str(p)))
    finally:
        FileReader.CHUNK_SIZE = original

    assert chunks == [b"abc", b"def"]