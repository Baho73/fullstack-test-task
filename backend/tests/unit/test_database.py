# FILE: backend/tests/unit/test_database.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT
#   PURPOSE: Verify database module: session factory, get_session dependency.
#   SCOPE: Unit tests — verifies session lifecycle and DI generator using test SQLite engine.
#   DEPENDS: M-DB
#   LINKS: V-M-DB
# END_MODULE_CONTRACT

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import src.database as db_module
from src.database import get_session


# START_BLOCK_FIXTURES
@pytest.fixture(autouse=True)
async def _patch_db(monkeypatch):
    """Replace production engine/session with SQLite for testing."""
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    test_session_maker = async_sessionmaker(test_engine, expire_on_commit=False)
    monkeypatch.setattr(db_module, "engine", test_engine)
    monkeypatch.setattr(db_module, "async_session_maker", test_session_maker)
    yield
    await test_engine.dispose()
# END_BLOCK_FIXTURES


# START_BLOCK_SESSION_FACTORY_TESTS
class TestSessionFactory:
    """V-M-DB / scenario-1: Session factory creates valid async sessions."""

    async def test_session_factory_returns_async_session(self):
        async with db_module.async_session_maker() as session:
            assert isinstance(session, AsyncSession)

    async def test_session_is_active(self):
        async with db_module.async_session_maker() as session:
            assert session.is_active
# END_BLOCK_SESSION_FACTORY_TESTS


# START_BLOCK_GET_SESSION_TESTS
class TestGetSession:
    """V-M-DB / scenario-2: get_session yields session and closes properly."""

    async def test_get_session_yields_session(self):
        gen = get_session()
        session = await gen.__anext__()
        assert isinstance(session, AsyncSession)
        try:
            await gen.__anext__()
        except StopAsyncIteration:
            pass

    async def test_get_session_completes_cleanly(self):
        """Generator yields valid session and exits without error."""
        gen = get_session()
        session = await gen.__anext__()
        assert session.is_active
        await gen.aclose()
# END_BLOCK_GET_SESSION_TESTS
