# FILE: backend/tests/unit/test_file_repository.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT
#   PURPOSE: Verify FileRepository: paginated listing, CRUD, edge cases.
#   SCOPE: Unit tests with in-memory DB session from conftest.
#   DEPENDS: M-REPO-FILES, M-MODELS
#   LINKS: V-M-REPO-FILES
# END_MODULE_CONTRACT

import pytest

from src.repositories.file_repository import (
    create_file,
    delete_file,
    get_file,
    list_files,
    update_file,
)


# START_BLOCK_LIST_FILES_TESTS
class TestListFiles:
    """V-M-REPO-FILES / scenario-1: list_files returns correct page with total count."""

    async def test_empty_list(self, session):
        files, total = await list_files(session, limit=10, offset=0)
        assert files == []
        assert total == 0

    async def test_pagination_returns_correct_subset(self, session, make_stored_file):
        for i in range(5):
            session.add(make_stored_file(file_id=f"page-test-{i}", title=f"File {i}"))
        await session.flush()

        files, total = await list_files(session, limit=2, offset=0)
        assert len(files) == 2
        assert total == 5

    async def test_pagination_offset(self, session, make_stored_file):
        for i in range(5):
            session.add(make_stored_file(file_id=f"offset-test-{i}", title=f"File {i}"))
        await session.flush()

        files, total = await list_files(session, limit=2, offset=3)
        assert len(files) == 2
        assert total == 5

    async def test_pagination_beyond_total(self, session, make_stored_file):
        session.add(make_stored_file(file_id="beyond-1"))
        await session.flush()

        files, total = await list_files(session, limit=10, offset=100)
        assert files == []
        assert total == 1
# END_BLOCK_LIST_FILES_TESTS


# START_BLOCK_GET_FILE_TESTS
class TestGetFile:
    """V-M-REPO-FILES / scenario-3: get_file returns None for unknown ID."""

    async def test_get_existing_file(self, session, make_stored_file):
        file = make_stored_file(file_id="get-test-1")
        session.add(file)
        await session.flush()

        result = await get_file(session, "get-test-1")
        assert result is not None
        assert result.id == "get-test-1"

    async def test_get_nonexistent_file_returns_none(self, session):
        result = await get_file(session, "nonexistent-id")
        assert result is None
# END_BLOCK_GET_FILE_TESTS


# START_BLOCK_CREATE_FILE_TESTS
class TestCreateFile:
    """V-M-REPO-FILES / scenario-2: create_file inserts and returns refreshed record."""

    async def test_create_and_retrieve(self, session, make_stored_file):
        file = make_stored_file(file_id="create-test-1", title="Created File")
        result = await create_file(session, file)

        assert result.id == "create-test-1"
        assert result.title == "Created File"
# END_BLOCK_CREATE_FILE_TESTS


# START_BLOCK_UPDATE_FILE_TESTS
class TestUpdateFile:
    """V-M-REPO-FILES: update_file changes title."""

    async def test_update_title(self, session, make_stored_file):
        file = make_stored_file(file_id="update-test-1", title="Old Title")
        session.add(file)
        await session.flush()

        result = await update_file(session, "update-test-1", title="New Title")
        assert result is not None
        assert result.title == "New Title"

    async def test_update_nonexistent_returns_none(self, session):
        result = await update_file(session, "no-such-id", title="Title")
        assert result is None
# END_BLOCK_UPDATE_FILE_TESTS


# START_BLOCK_DELETE_FILE_TESTS
class TestDeleteFile:
    """V-M-REPO-FILES: delete_file removes record."""

    async def test_delete_existing(self, session, make_stored_file):
        file = make_stored_file(file_id="delete-test-1")
        session.add(file)
        await session.flush()

        result = await delete_file(session, "delete-test-1")
        assert result is True

        check = await get_file(session, "delete-test-1")
        assert check is None

    async def test_delete_nonexistent_returns_false(self, session):
        result = await delete_file(session, "no-such-id")
        assert result is False
# END_BLOCK_DELETE_FILE_TESTS
