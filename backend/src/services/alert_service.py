#

from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories import alert_repository
from src.schemas import AlertItem, PaginatedResponse


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


async def create_alert(
    session: AsyncSession, *, file_id: str, level: str, message: str
) -> AlertItem:
    alert = await alert_repository.create_alert(
        session, file_id=file_id, level=level, message=message
    )
    return AlertItem.model_validate(alert)
