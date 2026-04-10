import io

import pytest
from fastapi import UploadFile

from src.storage import delete_file, get_path, save_file


class TestSaveFile:
    """V-M-STORAGE / scenario-1: save_file writes content and returns size."""

    async def test_save_file_writes_content(self, tmp_storage, monkeypatch):
        monkeypatch.setattr("src.storage.STORAGE_DIR", tmp_storage)

        content = b"Hello, World! This is test content."
        upload = UploadFile(
            filename="test.txt",
            file=io.BytesIO(content),
        )

        stored_name, size = await save_file(upload, "test-id-123")

        assert size == len(content)
        assert (tmp_storage / stored_name).exists()
        assert (tmp_storage / stored_name).read_bytes() == content

    async def test_save_file_generates_stored_name(self, tmp_storage, monkeypatch):
        monkeypatch.setattr("src.storage.STORAGE_DIR", tmp_storage)

        upload = UploadFile(
            filename="document.pdf",
            file=io.BytesIO(b"fake pdf content"),
        )

        stored_name, _ = await save_file(upload, "id-456")
        assert stored_name.startswith("id-456")
        assert stored_name.endswith(".pdf")


class TestDeleteFile:
    """V-M-STORAGE / scenario-2: delete_file removes existing file."""

    def test_delete_existing_file(self, tmp_storage, monkeypatch):
        monkeypatch.setattr("src.storage.STORAGE_DIR", tmp_storage)

        file_path = tmp_storage / "to-delete.txt"
        file_path.write_text("content")
        assert file_path.exists()

        delete_file("to-delete.txt")

        assert not file_path.exists()

    def test_delete_nonexistent_file_is_safe(self, tmp_storage, monkeypatch):
        """Deleting a file that doesn't exist should not raise."""
        monkeypatch.setattr("src.storage.STORAGE_DIR", tmp_storage)
        delete_file("nonexistent.txt")


class TestGetPath:
    """V-M-STORAGE / scenario-3: get_path raises for non-existent file."""

    def test_get_path_existing_file(self, tmp_storage, monkeypatch):
        monkeypatch.setattr("src.storage.STORAGE_DIR", tmp_storage)

        file_path = tmp_storage / "exists.txt"
        file_path.write_text("content")

        result = get_path("exists.txt")
        assert result == file_path

    def test_get_path_missing_file_raises(self, tmp_storage, monkeypatch):
        monkeypatch.setattr("src.storage.STORAGE_DIR", tmp_storage)

        with pytest.raises(Exception):
            get_path("missing.txt")
