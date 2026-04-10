# FILE: backend/src/services/file_service.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT
#   PURPOSE: Бизнес-логика файлов: загрузка (storage + DB), обновление, удаление (cascade), скачивание.
#   SCOPE: list_files, get_file, create_file, update_file, delete_file, get_download_path
#   DEPENDS: M-REPO-FILES, M-REPO-ALERTS, M-STORAGE, M-SCHEMAS
#   LINKS: M-SERVICE-FILES, V-M-SERVICE-FILES
# END_MODULE_CONTRACT
#
# START_MODULE_MAP
#   list_files - paginated files as PaginatedResponse[FileItem]
#   get_file - single file or HTTPException 404
#   create_file - save to storage + DB, return FileItem
#   update_file - update title, return FileItem
#   delete_file - delete from DB + storage + cascade alerts
#   get_download_path - resolve file for FileResponse
# END_MODULE_MAP

import logging
import mimetypes
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import StoredFile
from src.repositories import alert_repository, file_repository
from src.schemas import FileItem, PaginatedResponse
from src.storage import STORAGE_DIR, delete_file as storage_delete, get_path, save_file

logger = logging.getLogger(__name__)


# START_BLOCK_LIST_FILES
async def list_files(
    session: AsyncSession, *, limit: int = 20, offset: int = 0
) -> PaginatedResponse[FileItem]:
    files, total = await file_repository.list_files(session, limit=limit, offset=offset)
    return PaginatedResponse[FileItem](
        items=[FileItem.model_validate(f) for f in files],
        total=total,
        limit=limit,
        offset=offset,
    )
# END_BLOCK_LIST_FILES


# START_BLOCK_GET_FILE
async def get_file(session: AsyncSession, file_id: str) -> StoredFile:
    file = await file_repository.get_file(session, file_id)
    if file is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return file
# END_BLOCK_GET_FILE


# START_BLOCK_CREATE_FILE
async def create_file(
    session: AsyncSession, *, title: str, upload_file: UploadFile
) -> FileItem:
    # START_BLOCK_UPLOAD_FILE
    content_check = await upload_file.read(1)
    if not content_check:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File is empty")
    await upload_file.seek(0)

    file_id = str(uuid4())
    stored_name, size = await save_file(upload_file, file_id)

    file = StoredFile(
        id=file_id,
        title=title,
        original_name=upload_file.filename or stored_name,
        stored_name=stored_name,
        mime_type=upload_file.content_type or mimetypes.guess_type(stored_name)[0] or "application/octet-stream",
        size=size,
        processing_status="uploaded",
    )
    result = await file_repository.create_file(session, file)
    logger.info(
        "[FileService][create_file][BLOCK_UPLOAD_FILE] file uploaded",
        extra={"file_id": file_id, "size": size},
    )
    # END_BLOCK_UPLOAD_FILE
    return FileItem.model_validate(result)
# END_BLOCK_CREATE_FILE


# START_BLOCK_UPDATE_FILE
async def update_file(
    session: AsyncSession, file_id: str, *, title: str
) -> FileItem:
    result = await file_repository.update_file(session, file_id, title=title)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return FileItem.model_validate(result)
# END_BLOCK_UPDATE_FILE


# START_BLOCK_DELETE_FILE
async def delete_file(session: AsyncSession, file_id: str) -> None:
    file = await get_file(session, file_id)

    logger.info(
        "[FileService][delete_file][BLOCK_DELETE_FILE] deleting file",
        extra={"file_id": file_id},
    )

    await alert_repository.delete_alerts_by_file(session, file_id)
    storage_delete(file.stored_name)
    await file_repository.delete_file(session, file_id)
# END_BLOCK_DELETE_FILE


# START_BLOCK_DOWNLOAD_PATH
async def get_download_path(session: AsyncSession, file_id: str) -> tuple[StoredFile, Path]:
    file = await get_file(session, file_id)
    try:
        stored_path = get_path(file.stored_name)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Stored file not found"
        )
    return file, stored_path
# END_BLOCK_DOWNLOAD_PATH

# START_CHANGE_SUMMARY
#   LAST_CHANGE: [v1.0.0 - New module: business logic extracted from old service.py,
#                  delegates to repos/storage, cascade delete, streaming upload, pagination]
# END_CHANGE_SUMMARY
