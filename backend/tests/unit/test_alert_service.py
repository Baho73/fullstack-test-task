from src.services.alert_service import create_alert, list_alerts


class TestListAlerts:
    """V-M-SERVICE-ALERTS / scenario-1: list_alerts returns paginated response."""

    async def test_empty_paginated_response(self, session):
        result = await list_alerts(session, limit=10, offset=0)
        assert hasattr(result, "items")
        assert hasattr(result, "total")
        assert result.total == 0
        assert result.items == []

    async def test_paginated_response_respects_limit(self, session, make_stored_file, make_alert):
        file = make_stored_file(file_id="svc-alert-file")
        session.add(file)
        await session.flush()

        for i in range(5):
            session.add(make_alert(file_id="svc-alert-file", message=f"Alert {i}"))
        await session.flush()

        result = await list_alerts(session, limit=2, offset=0)
        assert len(result.items) == 2
        assert result.total == 5


class TestCreateAlert:
    """V-M-SERVICE-ALERTS / scenario-2: create_alert creates and returns alert."""

    async def test_create_alert(self, session, make_stored_file):
        file = make_stored_file(file_id="svc-create-alert")
        session.add(file)
        await session.flush()

        result = await create_alert(
            session,
            file_id="svc-create-alert",
            level="info",
            message="Test alert",
        )
        assert result.level == "info"
        assert result.file_id == "svc-create-alert"
