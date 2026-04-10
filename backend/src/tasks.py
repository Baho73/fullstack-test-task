# FILE: backend/src/tasks.py
# VERSION: 1.1.0
# START_MODULE_CONTRACT
#   PURPOSE: Celery tasks: scan -> metadata -> alert pipeline. Uses shared DB module.
#   SCOPE: scan_file_for_threats, extract_file_metadata, send_file_alert
#   DEPENDS: M-DB, M-MODELS, M-STORAGE
#   LINKS: M-TASKS, V-M-TASKS
# END_MODULE_CONTRACT
#
# START_MODULE_MAP
#   celery_app - Celery application instance
#   scan_file_for_threats - Celery task: check extension, size, mime mismatch
#   extract_file_metadata - Celery task: extract text/pdf metadata
#   send_file_alert - Celery task: create alert based on results
#   _scan_file_for_threats - async inner: scan logic (testable without Celery)
#   _extract_file_metadata - async inner: metadata logic
#   _send_file_alert - async inner: alert logic
# END_MODULE_MAP

import asyncio
import logging
import os
from pathlib import Path

from celery import Celery
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import async_session_maker
from src.models import Alert, StoredFile
from src.storage import STORAGE_DIR

logger = logging.getLogger(__name__)

REDIS_URL = os.environ.get("REDIS_URL", "redis://backend-redis:6379/0")
celery_app = Celery("file_tasks", broker=REDIS_URL, backend=REDIS_URL)

_worker_loop: asyncio.AbstractEventLoop | None = None


def _run_in_worker_loop(coroutine):
    global _worker_loop
    if _worker_loop is None or _worker_loop.is_closed():
        _worker_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_worker_loop)
    return _worker_loop.run_until_complete(coroutine)


# START_BLOCK_SCAN_FILE
async def _scan_file_for_threats(session: AsyncSession, file_id: str) -> None:
    file_item = await session.get(StoredFile, file_id)
    if not file_item:
        return

    file_item.processing_status = "processing"
    reasons: list[str] = []
    extension = Path(file_item.original_name).suffix.lower()

    if extension in {".exe", ".bat", ".cmd", ".sh", ".js"}:
        reasons.append(f"suspicious extension {extension}")

    if file_item.size > 10 * 1024 * 1024:
        reasons.append("file is larger than 10 MB")

    if extension == ".pdf" and file_item.mime_type not in {"application/pdf", "application/octet-stream"}:
        reasons.append("pdf extension does not match mime type")

    file_item.scan_status = "suspicious" if reasons else "clean"
    file_item.scan_details = ", ".join(reasons) if reasons else "no threats found"
    file_item.requires_attention = bool(reasons)
    await session.commit()

    logger.info(
        "[CeleryTasks][scan_file_for_threats][BLOCK_SCAN_FILE] scan complete",
        extra={"file_id": file_id, "scan_status": file_item.scan_status},
    )
# END_BLOCK_SCAN_FILE


# START_BLOCK_EXTRACT_METADATA
async def _extract_file_metadata(session: AsyncSession, file_id: str) -> None:
    file_item = await session.get(StoredFile, file_id)
    if not file_item:
        return

    stored_path = STORAGE_DIR / file_item.stored_name
    if not stored_path.exists():
        file_item.processing_status = "failed"
        file_item.scan_status = file_item.scan_status or "failed"
        file_item.scan_details = "stored file not found during metadata extraction"
        await session.commit()

        logger.info(
            "[CeleryTasks][extract_file_metadata][BLOCK_EXTRACT_METADATA] file missing",
            extra={"file_id": file_id},
        )
        return

    metadata = {
        "extension": Path(file_item.original_name).suffix.lower(),
        "size_bytes": file_item.size,
        "mime_type": file_item.mime_type,
    }

    if file_item.mime_type.startswith("text/"):
        content = stored_path.read_text(encoding="utf-8", errors="ignore")
        metadata["line_count"] = len(content.splitlines())
        metadata["char_count"] = len(content)
    elif file_item.mime_type == "application/pdf":
        content = stored_path.read_bytes()
        metadata["approx_page_count"] = max(content.count(b"/Type /Page"), 1)

    file_item.metadata_json = metadata
    file_item.processing_status = "processed"
    await session.commit()

    logger.info(
        "[CeleryTasks][extract_file_metadata][BLOCK_EXTRACT_METADATA] metadata extracted",
        extra={"file_id": file_id},
    )
# END_BLOCK_EXTRACT_METADATA


# START_BLOCK_SEND_ALERT
async def _send_file_alert(session: AsyncSession, file_id: str) -> None:
    file_item = await session.get(StoredFile, file_id)
    if not file_item:
        return

    if file_item.processing_status == "failed":
        alert = Alert(file_id=file_id, level="critical", message="File processing failed")
    elif file_item.requires_attention:
        alert = Alert(
            file_id=file_id,
            level="warning",
            message=f"File requires attention: {file_item.scan_details}",
        )
    else:
        alert = Alert(file_id=file_id, level="info", message="File processed successfully")

    session.add(alert)
    await session.commit()

    logger.info(
        "[CeleryTasks][send_file_alert][BLOCK_SEND_ALERT] alert created",
        extra={"file_id": file_id, "level": alert.level},
    )
# END_BLOCK_SEND_ALERT


# START_BLOCK_CELERY_TASKS
@celery_app.task
def scan_file_for_threats(file_id: str) -> None:
    async def _run():
        async with async_session_maker() as session:
            await _scan_file_for_threats(session, file_id)
        async with async_session_maker() as session:
            extract_file_metadata.delay(file_id)

    _run_in_worker_loop(_run())


@celery_app.task
def extract_file_metadata(file_id: str) -> None:
    async def _run():
        async with async_session_maker() as session:
            await _extract_file_metadata(session, file_id)
        send_file_alert.delay(file_id)

    _run_in_worker_loop(_run())


@celery_app.task
def send_file_alert(file_id: str) -> None:
    async def _run():
        async with async_session_maker() as session:
            await _send_file_alert(session, file_id)

    _run_in_worker_loop(_run())
# END_BLOCK_CELERY_TASKS

# START_CHANGE_SUMMARY
#   LAST_CHANGE: [v1.1.0 - Refactored: removed duplicate engine/session_maker,
#                  now uses shared database.async_session_maker. Inner async functions
#                  accept session parameter for testability. Added GRACE markup and logging.]
# END_CHANGE_SUMMARY
