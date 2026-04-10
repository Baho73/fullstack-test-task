# FILE: backend/tests/unit/test_schemas.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT
#   PURPOSE: Verify Pydantic schemas: FileItem, FileUpdate, AlertItem, PaginatedResponse.
#   SCOPE: Unit tests — pure validation, no DB or I/O.
#   DEPENDS: M-SCHEMAS
#   LINKS: V-M-SCHEMAS
# END_MODULE_CONTRACT

from datetime import datetime, timezone

import pytest

from src.schemas import AlertItem, FileItem, FileUpdate, PaginatedResponse


# START_BLOCK_FILE_ITEM_TESTS
class TestFileItem:
    """V-M-SCHEMAS / scenario-1: FileItem validates from ORM-like attributes."""

    def test_valid_file_item(self):
        data = {
            "id": "abc-123",
            "title": "Test",
            "original_name": "file.txt",
            "stored_name": "abc-123.txt",
            "mime_type": "text/plain",
            "size": 1024,
            "processing_status": "uploaded",
            "scan_status": None,
            "scan_details": None,
            "metadata_json": None,
            "requires_attention": False,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        item = FileItem.model_validate(data)
        assert item.id == "abc-123"
        assert item.size == 1024
        assert item.requires_attention is False

    def test_file_item_with_metadata(self):
        data = {
            "id": "abc-456",
            "title": "PDF Doc",
            "original_name": "doc.pdf",
            "stored_name": "abc-456.pdf",
            "mime_type": "application/pdf",
            "size": 50000,
            "processing_status": "processed",
            "scan_status": "clean",
            "scan_details": "no threats found",
            "metadata_json": {"extension": ".pdf", "approx_page_count": 5},
            "requires_attention": False,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        item = FileItem.model_validate(data)
        assert item.metadata_json["approx_page_count"] == 5
        assert item.scan_status == "clean"
# END_BLOCK_FILE_ITEM_TESTS


# START_BLOCK_FILE_UPDATE_TESTS
class TestFileUpdate:
    """V-M-SCHEMAS / scenario-3: FileUpdate validation."""

    def test_valid_update(self):
        update = FileUpdate(title="New Title")
        assert update.title == "New Title"

    def test_rejects_empty_title(self):
        """FileUpdate should reject whitespace-only titles."""
        with pytest.raises(Exception):
            FileUpdate(title="   ")
# END_BLOCK_FILE_UPDATE_TESTS


# START_BLOCK_ALERT_ITEM_TESTS
class TestAlertItem:
    """V-M-SCHEMAS: AlertItem validates correctly."""

    def test_valid_alert_item(self):
        data = {
            "id": 1,
            "file_id": "abc-123",
            "level": "warning",
            "message": "File requires attention",
            "created_at": datetime.now(timezone.utc),
        }
        item = AlertItem.model_validate(data)
        assert item.level == "warning"
        assert item.file_id == "abc-123"
# END_BLOCK_ALERT_ITEM_TESTS


# START_BLOCK_PAGINATED_RESPONSE_TESTS
class TestPaginatedResponse:
    """V-M-SCHEMAS / scenario-2: PaginatedResponse wraps items with total/limit/offset."""

    def test_paginated_response_structure(self):
        resp = PaginatedResponse[FileItem](
            items=[],
            total=0,
            limit=20,
            offset=0,
        )
        assert resp.items == []
        assert resp.total == 0
        assert resp.limit == 20
        assert resp.offset == 0

    def test_paginated_response_with_items(self):
        file_data = {
            "id": "abc-123",
            "title": "Test",
            "original_name": "file.txt",
            "stored_name": "abc-123.txt",
            "mime_type": "text/plain",
            "size": 100,
            "processing_status": "uploaded",
            "scan_status": None,
            "scan_details": None,
            "metadata_json": None,
            "requires_attention": False,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        resp = PaginatedResponse[FileItem](
            items=[FileItem.model_validate(file_data)],
            total=50,
            limit=10,
            offset=0,
        )
        assert len(resp.items) == 1
        assert resp.total == 50
        assert resp.items[0].id == "abc-123"

    def test_items_count_within_limit(self):
        """Deterministic assertion: len(items) <= limit."""
        resp = PaginatedResponse[AlertItem](
            items=[],
            total=100,
            limit=5,
            offset=0,
        )
        assert len(resp.items) <= resp.limit
# END_BLOCK_PAGINATED_RESPONSE_TESTS
