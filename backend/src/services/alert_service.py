# FILE: backend/src/services/alert_service.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT
#   PURPOSE: Бизнес-логика алертов: листинг с пагинацией, создание.
#   SCOPE: list_alerts, create_alert
#   DEPENDS: M-REPO-ALERTS, M-SCHEMAS
#   LINKS: M-SERVICE-ALERTS, V-M-SERVICE-ALERTS
# END_MODULE_CONTRACT
#
# START_MODULE_MAP
#   list_alerts - paginated alerts as PaginatedResponse[AlertItem]
#   create_alert - create alert for file, return AlertItem
# END_MODULE_MAP

from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories import alert_repository
from src.schemas import AlertItem, PaginatedResponse


# START_BLOCK_LIST_ALERTS
async def list_alerts(
    session: AsyncSession, *, limit: int = 20, offset: int = 0
) -> PaginatedResponse[AlertItem]:
    alerts, total = await alert_repository.list_alerts(session, limit=limit, offset=offset)
    return PaginatedResponse[AlertItem](
        items=[AlertItem.model_validate(a) for a in alerts],
        total=total,
        limit=limit,
        offset=offset,
    )
# END_BLOCK_LIST_ALERTS


# START_BLOCK_CREATE_ALERT
async def create_alert(
    session: AsyncSession, *, file_id: str, level: str, message: str
) -> AlertItem:
    alert = await alert_repository.create_alert(
        session, file_id=file_id, level=level, message=message
    )
    return AlertItem.model_validate(alert)
# END_BLOCK_CREATE_ALERT

# START_CHANGE_SUMMARY
#   LAST_CHANGE: [v1.0.0 - New module: alert service with pagination, delegates to alert_repository]
# END_CHANGE_SUMMARY
