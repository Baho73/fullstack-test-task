# FILE: backend/tests/conftest.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT
#   PURPOSE: Shared test fixtures for async DB sessions, temp storage, and factory helpers.
#   SCOPE: conftest for all backend tests (unit + integration)
#   DEPENDS: M-DB, M-MODELS, M-STORAGE
#   LINKS: V-M-DB, V-M-MODELS, V-M-STORAGE, V-M-APP
# END_MODULE_CONTRACT

import asyncio
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.models import Alert, Base, StoredFile


# START_BLOCK_TEST_ENGINE
@pytest.fixture(scope="session")
def event_loop():
    """Create a single event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


def _enable_sqlite_fk(dbapi_conn, connection_record):
    """Enable foreign key enforcement in SQLite (required for cascade deletes)."""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create an in-memory SQLite async engine for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    event.listen(engine.sync_engine, "connect", _enable_sqlite_fk)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
# END_BLOCK_TEST_ENGINE


# START_BLOCK_SESSION_FIXTURE
@pytest.fixture
async def session(test_engine) -> AsyncSession:
    """Provide an async session. Cleans all tables after each test."""
    session_maker = async_sessionmaker(test_engine, expire_on_commit=False)
    async with session_maker() as session:
        yield session

    # Clean up all tables after each test for isolation
    async with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())
# END_BLOCK_SESSION_FIXTURE


# START_BLOCK_STORAGE_FIXTURE
@pytest.fixture
def tmp_storage(tmp_path) -> Path:
    """Provide a temporary storage directory for file operations."""
    storage_dir = tmp_path / "storage" / "files"
    storage_dir.mkdir(parents=True, exist_ok=True)
    return storage_dir
# END_BLOCK_STORAGE_FIXTURE


# START_BLOCK_FACTORY_HELPERS
@pytest.fixture
def make_stored_file():
    """Factory fixture for creating StoredFile instances."""

    def _make(
        *,
        file_id: str | None = None,
        title: str = "Test File",
        original_name: str = "test.txt",
        stored_name: str | None = None,
        mime_type: str = "text/plain",
        size: int = 100,
        processing_status: str = "uploaded",
        scan_status: str | None = None,
        scan_details: str | None = None,
        metadata_json: dict | None = None,
        requires_attention: bool = False,
    ) -> StoredFile:
        fid = file_id or str(uuid4())
        return StoredFile(
            id=fid,
            title=title,
            original_name=original_name,
            stored_name=stored_name or f"{fid}.txt",
            mime_type=mime_type,
            size=size,
            processing_status=processing_status,
            scan_status=scan_status,
            scan_details=scan_details,
            metadata_json=metadata_json,
            requires_attention=requires_attention,
        )

    return _make


@pytest.fixture
def make_alert():
    """Factory fixture for creating Alert instances."""

    def _make(
        *,
        file_id: str,
        level: str = "info",
        message: str = "Test alert",
    ) -> Alert:
        return Alert(
            file_id=file_id,
            level=level,
            message=message,
        )

    return _make
# END_BLOCK_FACTORY_HELPERS
