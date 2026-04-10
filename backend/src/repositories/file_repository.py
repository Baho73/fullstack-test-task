#

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import StoredFile


async def list_files(
    session: AsyncSession, *, limit: int = 20, offset: int = 0
) -> tuple[list[StoredFile], int]:
    total_result = await session.execute(select(func.count(StoredFile.id)))
    total = total_result.scalar_one()

    result = await session.execute(
        select(StoredFile)
        .order_by(StoredFile.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    files = list(result.scalars().all())
    return files, total


async def get_file(session: AsyncSession, file_id: str) -> StoredFile | None:
    return await session.get(StoredFile, file_id)


async def create_file(session: AsyncSession, file: StoredFile) -> StoredFile:
    session.add(file)
    await session.flush()
    await session.refresh(file)
    return file


async def update_file(
    session: AsyncSession, file_id: str, *, title: str
) -> StoredFile | None:
    file = await session.get(StoredFile, file_id)
    if file is None:
        return None
    file.title = title
    await session.flush()
    await session.refresh(file)
    return file


async def delete_file(session: AsyncSession, file_id: str) -> bool:
    file = await session.get(StoredFile, file_id)
    if file is None:
        return False
    await session.delete(file)
    await session.flush()
    return True
