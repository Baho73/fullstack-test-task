#

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Alert


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


async def create_alert(
    session: AsyncSession, *, file_id: str, level: str, message: str
) -> Alert:
    alert = Alert(file_id=file_id, level=level, message=message)
    session.add(alert)
    await session.flush()
    await session.refresh(alert)
    return alert


async def delete_alerts_by_file(session: AsyncSession, file_id: str) -> int:
    result = await session.execute(
        delete(Alert).where(Alert.file_id == file_id)
    )
    await session.flush()
    return result.rowcount
