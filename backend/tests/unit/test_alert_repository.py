import pytest

from src.repositories.alert_repository import (
    create_alert,
    delete_alerts_by_file,
    list_alerts,
)
from src.models import Alert


class TestListAlerts:
    """V-M-REPO-ALERTS / scenario-1: list_alerts returns correct page with total count."""

    async def test_empty_list(self, session):
        alerts, total = await list_alerts(session, limit=10, offset=0)
        assert alerts == []
        assert total == 0

    async def test_pagination(self, session, make_stored_file, make_alert):
        file = make_stored_file(file_id="alert-page-file")
        session.add(file)
        await session.flush()

        for i in range(5):
            session.add(make_alert(file_id="alert-page-file", message=f"Alert {i}"))
        await session.flush()

        alerts, total = await list_alerts(session, limit=2, offset=0)
        assert len(alerts) == 2
        assert total == 5


class TestCreateAlert:
    """V-M-REPO-ALERTS: create_alert inserts and returns."""

    async def test_create_alert(self, session, make_stored_file):
        file = make_stored_file(file_id="alert-create-file")
        session.add(file)
        await session.flush()

        alert = await create_alert(
            session,
            file_id="alert-create-file",
            level="warning",
            message="Test warning",
        )
        assert alert.id is not None
        assert alert.level == "warning"
        assert alert.file_id == "alert-create-file"


class TestDeleteAlertsByFile:
    """V-M-REPO-ALERTS / scenario-2: delete_alerts_by_file removes all alerts for given file_id."""

    async def test_delete_all_alerts_for_file(self, session, make_stored_file, make_alert):
        file = make_stored_file(file_id="alert-del-file")
        session.add(file)
        await session.flush()

        session.add(make_alert(file_id="alert-del-file", message="A1"))
        session.add(make_alert(file_id="alert-del-file", message="A2"))
        await session.flush()

        deleted_count = await delete_alerts_by_file(session, "alert-del-file")
        assert deleted_count == 2

        remaining, total = await list_alerts(session, limit=10, offset=0)
        file_alerts = [a for a in remaining if a.file_id == "alert-del-file"]
        assert len(file_alerts) == 0

    async def test_delete_alerts_for_nonexistent_file(self, session):
        deleted_count = await delete_alerts_by_file(session, "no-such-file")
        assert deleted_count == 0
