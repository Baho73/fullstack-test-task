# FILE: backend/tests/integration/test_api.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT
#   PURPOSE: Integration tests for FastAPI endpoints via httpx.AsyncClient.
#   SCOPE: Full request/response cycle: routes -> services -> repos -> DB.
#   DEPENDS: M-APP, M-SERVICE-FILES, M-SERVICE-ALERTS, M-DB
#   LINKS: V-M-APP, VF-002, VF-003
# END_MODULE_CONTRACT

import pytest
from httpx import ASGITransport, AsyncClient

from src.app import app
from src.database import get_session
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from src.models import Base


# START_BLOCK_TEST_APP_SETUP
@pytest.fixture(scope="module")
async def test_db_engine():
    """Integration test engine with real schema."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def test_session(test_db_engine):
    session_maker = async_sessionmaker(test_db_engine, expire_on_commit=False)
    async with session_maker() as session:
        yield session


@pytest.fixture
async def client(test_db_engine, monkeypatch):
    """httpx client with overridden DB session and mocked Celery tasks."""
    session_maker = async_sessionmaker(test_db_engine, expire_on_commit=False)

    async def override_get_session():
        async with session_maker() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    # Mock Celery task dispatch — no Redis needed in tests
    monkeypatch.setattr("src.tasks.scan_file_for_threats.delay", lambda file_id: None)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
# END_BLOCK_TEST_APP_SETUP


# START_BLOCK_FILES_ENDPOINT_TESTS
class TestFilesEndpoints:
    """V-M-APP / scenario-1,3,5: File CRUD via HTTP."""

    async def test_list_files_empty(self, client):
        """VF-002: GET /files returns paginated response."""
        resp = await client.get("/files", params={"limit": 10, "offset": 0})
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert data["items"] == []
        assert data["total"] == 0

    async def test_list_files_pagination_params(self, client):
        """Pagination query params are respected."""
        resp = await client.get("/files", params={"limit": 5, "offset": 0})
        assert resp.status_code == 200
        data = resp.json()
        assert data["limit"] == 5
        assert data["offset"] == 0

    async def test_create_file(self, client, tmp_storage, monkeypatch):
        """V-M-APP / scenario-3: POST /files creates file and returns 201."""
        monkeypatch.setattr("src.storage.STORAGE_DIR", tmp_storage)

        resp = await client.post(
            "/files",
            data={"title": "Test Upload"},
            files={"file": ("test.txt", b"Hello World", "text/plain")},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Test Upload"
        assert data["original_name"] == "test.txt"
        assert data["processing_status"] == "uploaded"

    async def test_get_file_not_found(self, client):
        """V-M-APP / scenario-5: GET /files/{unknown} returns 404."""
        resp = await client.get("/files/nonexistent-id")
        assert resp.status_code == 404

    async def test_delete_file(self, client, tmp_storage, monkeypatch):
        """V-M-APP / scenario-4: DELETE /files/{id} returns 204."""
        monkeypatch.setattr("src.storage.STORAGE_DIR", tmp_storage)

        # Create first
        resp = await client.post(
            "/files",
            data={"title": "To Delete"},
            files={"file": ("del.txt", b"content", "text/plain")},
        )
        file_id = resp.json()["id"]

        # Delete
        resp = await client.delete(f"/files/{file_id}")
        assert resp.status_code == 204

        # Verify gone
        resp = await client.get(f"/files/{file_id}")
        assert resp.status_code == 404
# END_BLOCK_FILES_ENDPOINT_TESTS


# START_BLOCK_ALERTS_ENDPOINT_TESTS
class TestAlertsEndpoints:
    """V-M-APP / scenario-2: Alert listing via HTTP."""

    async def test_list_alerts_empty(self, client):
        """VF-002: GET /alerts returns paginated response."""
        resp = await client.get("/alerts", params={"limit": 10, "offset": 0})
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert data["items"] == []
# END_BLOCK_ALERTS_ENDPOINT_TESTS
