# FILE: backend/src/repositories/file_repository.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT
#   PURPOSE: Data access: CRUD для StoredFile с пагинацией.
#   SCOPE: list_files, get_file, create_file, update_file, delete_file
#   DEPENDS: M-DB, M-MODELS
#   LINKS: M-REPO-FILES, V-M-REPO-FILES
# END_MODULE_CONTRACT
#
# START_MODULE_MAP
#   list_files - paginated SELECT with total count, ordered by created_at desc
#   get_file - get by ID or None
#   create_file - INSERT and return refreshed
#   update_file - UPDATE title, return refreshed or None
#   delete_file - DELETE record, return True/False
# END_MODULE_MAP

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import StoredFile


# START_BLOCK_LIST_FILES
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
# END_BLOCK_LIST_FILES


# START_BLOCK_GET_FILE
async def get_file(session: AsyncSession, file_id: str) -> StoredFile | None:
    return await session.get(StoredFile, file_id)
# END_BLOCK_GET_FILE


# START_BLOCK_CREATE_FILE
async def create_file(session: AsyncSession, file: StoredFile) -> StoredFile:
    session.add(file)
    await session.flush()
    await session.refresh(file)
    return file
# END_BLOCK_CREATE_FILE


# START_BLOCK_UPDATE_FILE
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
# END_BLOCK_UPDATE_FILE


# START_BLOCK_DELETE_FILE
async def delete_file(session: AsyncSession, file_id: str) -> bool:
    file = await session.get(StoredFile, file_id)
    if file is None:
        return False
    await session.delete(file)
    await session.flush()
    return True
# END_BLOCK_DELETE_FILE

# START_CHANGE_SUMMARY
#   LAST_CHANGE: [v1.0.0 - New module: extracted data access from service.py with pagination support]
# END_CHANGE_SUMMARY
