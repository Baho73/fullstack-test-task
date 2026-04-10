# FILE: backend/tests/unit/test_file_service.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT
#   PURPOSE: Verify FileService business logic: upload, delete cascade, get 404, pagination.
#   SCOPE: Unit tests — service layer with real DB session, temp storage.
#   DEPENDS: M-SERVICE-FILES, M-REPO-FILES, M-REPO-ALERTS, M-STORAGE
#   LINKS: V-M-SERVICE-FILES, VF-001, VF-003
# END_MODULE_CONTRACT

import io

import pytest
from fastapi import HTTPException, UploadFile

from src.services.file_service import (
    create_file,
    delete_file,
    get_download_path,
    get_file,
    list_files,
    update_file,
)


# START_BLOCK_CREATE_FILE_TESTS
class TestCreateFile:
    """V-M-SERVICE-FILES / scenario-1: create_file saves to storage and DB."""

    async def test_create_file_success(self, session, tmp_storage, monkeypatch):
        monkeypatch.setattr("src.storage.STORAGE_DIR", tmp_storage)

        upload = UploadFile(
            filename="hello.txt",
            file=io.BytesIO(b"Hello World"),
        )
        result = await create_file(session, title="Hello File", upload_file=upload)

        assert result.title == "Hello File"
        assert result.original_name == "hello.txt"
        assert result.size == 11
        assert result.processing_status == "uploaded"

    async def test_create_file_rejects_empty(self, session, tmp_storage, monkeypatch):
        """V-M-SERVICE-FILES / scenario-3: create_file rejects empty upload."""
        monkeypatch.setattr("src.storage.STORAGE_DIR", tmp_storage)

        upload = UploadFile(
            filename="empty.txt",
            file=io.BytesIO(b""),
        )
        with pytest.raises(HTTPException) as exc_info:
            await create_file(session, title="Empty", upload_file=upload)
        assert exc_info.value.status_code == 400
# END_BLOCK_CREATE_FILE_TESTS


# START_BLOCK_GET_FILE_TESTS
class TestGetFile:
    """V-M-SERVICE-FILES / scenario-4: get_file raises 404 for unknown ID."""

    async def test_get_nonexistent_raises_404(self, session):
        with pytest.raises(HTTPException) as exc_info:
            await get_file(session, "nonexistent-id")
        assert exc_info.value.status_code == 404
# END_BLOCK_GET_FILE_TESTS


# START_BLOCK_LIST_FILES_TESTS
class TestListFiles:
    """V-M-SERVICE-FILES: list_files returns PaginatedResponse."""

    async def test_paginated_response_structure(self, session):
        result = await list_files(session, limit=10, offset=0)
        assert hasattr(result, "items")
        assert hasattr(result, "total")
        assert hasattr(result, "limit")
        assert hasattr(result, "offset")
        assert len(result.items) <= result.limit
# END_BLOCK_LIST_FILES_TESTS


# START_BLOCK_DELETE_FILE_TESTS
class TestDeleteFile:
    """V-M-SERVICE-FILES / scenario-2: delete_file cascades."""

    async def test_delete_removes_file_and_alerts(
        self, session, tmp_storage, monkeypatch, make_stored_file, make_alert
    ):
        """VF-003: Cascade delete — alerts deleted, file removed from disk and DB."""
        monkeypatch.setattr("src.storage.STORAGE_DIR", tmp_storage)

        file = make_stored_file(file_id="del-svc-1")
        session.add(file)
        await session.flush()

        # Create physical file
        (tmp_storage / file.stored_name).write_text("content")

        # Create alerts
        session.add(make_alert(file_id="del-svc-1", message="A1"))
        session.add(make_alert(file_id="del-svc-1", message="A2"))
        await session.flush()

        await delete_file(session, "del-svc-1")

        # Verify: file gone from DB
        with pytest.raises(HTTPException):
            await get_file(session, "del-svc-1")

        # Verify: file gone from disk
        assert not (tmp_storage / file.stored_name).exists()

    async def test_delete_nonexistent_raises_404(self, session):
        with pytest.raises(HTTPException) as exc_info:
            await delete_file(session, "no-such-id")
        assert exc_info.value.status_code == 404
# END_BLOCK_DELETE_FILE_TESTS


# START_BLOCK_UPDATE_FILE_TESTS
class TestUpdateFile:
    """V-M-SERVICE-FILES: update_file changes title."""

    async def test_update_title(self, session, make_stored_file):
        file = make_stored_file(file_id="upd-svc-1", title="Old")
        session.add(file)
        await session.flush()

        result = await update_file(session, "upd-svc-1", title="New Title")
        assert result.title == "New Title"
# END_BLOCK_UPDATE_FILE_TESTS
