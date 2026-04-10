# FILE: backend/src/repositories/alert_repository.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT
#   PURPOSE: Data access: CRUD для Alert с пагинацией.
#   SCOPE: list_alerts, create_alert, delete_alerts_by_file
#   DEPENDS: M-DB, M-MODELS
#   LINKS: M-REPO-ALERTS, V-M-REPO-ALERTS
# END_MODULE_CONTRACT
#
# START_MODULE_MAP
#   list_alerts - paginated SELECT with total count, ordered by created_at desc
#   create_alert - INSERT and return refreshed
#   delete_alerts_by_file - DELETE WHERE file_id = ?, return count
# END_MODULE_MAP

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Alert


# START_BLOCK_LIST_ALERTS
async def list_alerts(
    session: AsyncSession, *, limit: int = 20, offset: int = 0
) -> tuple[list[Alert], int]:
    total_result = await session.execute(select(func.count(Alert.id)))
    total = total_result.scalar_one()

    result = await session.execute(
        select(Alert)
        .order_by(Alert.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    alerts = list(result.scalars().all())
    return alerts, total
# END_BLOCK_LIST_ALERTS


# START_BLOCK_CREATE_ALERT
async def create_alert(
    session: AsyncSession, *, file_id: str, level: str, message: str
) -> Alert:
    alert = Alert(file_id=file_id, level=level, message=message)
    session.add(alert)
    await session.flush()
    await session.refresh(alert)
    return alert
# END_BLOCK_CREATE_ALERT


# START_BLOCK_DELETE_ALERTS_BY_FILE
async def delete_alerts_by_file(session: AsyncSession, file_id: str) -> int:
    result = await session.execute(
        delete(Alert).where(Alert.file_id == file_id)
    )
    await session.flush()
    return result.rowcount
# END_BLOCK_DELETE_ALERTS_BY_FILE

# START_CHANGE_SUMMARY
#   LAST_CHANGE: [v1.0.0 - New module: extracted data access from service.py with pagination support]
# END_CHANGE_SUMMARY
